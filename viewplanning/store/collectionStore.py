from viewplanning.store.mongoFactory import MongoFactory
from viewplanning.configuration import ConfigurationFactory
from dataclasses import asdict
import json
from typing import TypeVar, Generic, Iterable, Callable
from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient
import numpy as np
import uuid
from functools import cmp_to_key
import logging


T = TypeVar('T')


class CollectionStore(Generic[T]):
    '''
    abstract type to store data
    '''
    def __init__(self, name, factory: Callable[[dict], T]):
        '''
        Parameters
        ----------
        name: str
            name of the store
        factory: (dict) -> T
            deserilize the data stored as a dictionary
        '''
        self.name = name
        self.factory = factory

    def getItems(self) -> 'list[T]':
        '''
        get a list of items
        
        Returns
        -------
            list[T]
        '''
        raise NotImplementedError()

    def insertItem(self, item):
        '''
        insert an item into the store

        Parameters
        ----------
        item: T
            the item to insert
        '''
        raise NotImplementedError()

    def close(self):
        '''
        close the store
        '''
        raise NotImplementedError()

    def find(self, search):
        '''
        find items in the store the search is a dict with key being parameters to look up and the values being matches
        {'_id': 1} for any item that has an _id of 1
        Parameters
        ----------
        search: dict
            search term
        
        Returns
        -------
            T
        '''
        raise NotImplementedError()

    def getItemsIterator(self, sort: dict = {}) -> 'Iterable[T]':
        '''
        get an interator of items sorted by a dict with keys being fields to sort by and the value {-1, 1} being the direction of sorting

        Parameters
        ----------
        sort: dict

        Returns
        -------
        Iterable[T]
        '''
        raise NotImplementedError()

    def getItemById(self, id):
        '''
        get an item by the _id

        Parameters
        ----------
        id: Any
            the Id to look up
        
            
        Returns
        -------
            T | None
        '''
        raise NotImplementedError()

    def hasId(self, id):
        '''
        the collection has an item with the _id

        Parameters
        ----------
        id: Any
            the id to check
        
        Returns
        -------
        bool
            true if the item exists
        '''
        raise NotImplementedError()

    def updateItem(self, item):
        '''
        update an item in the store

        Parameters
        ----------
        item: T
            the item to update
        '''
        raise NotImplementedError()

    def removeItem(self, id):
        '''
        remove an item with the _id

        Parameters
        ----------
        id: Any
            the id of the item to delete
        
        Returns
        -------
        T
            the deleted item
        '''
        raise NotImplementedError()


class MongoCollectionStore(CollectionStore[T]):
    def __init__(self, name, factory: Callable[[dict], T]):
        super().__init__(name, factory)
        self.client: MongoClient = MongoFactory.getDatabase()
        self.collection: Collection = self.client.get_collection(name)

    def getItems(self) -> 'list[T]':
        items = self.collection.find()
        return [self.factory(item) for item in items]

    def find(self, search):
        '''
        search mongodb

        Parameters
        ----------
        search: dict
            mongodb search dictionary
        '''
        items = self.collection.find(search)
        return [self.factory(item) for item in items]

    def getItemsIterator(self, sort: dict = None, search: dict = None) -> 'Iterable[T]':
        '''
        iterate all items in the store

        Parameters
        ----------
        sort: dict
            optional sort for mongodb

        Returns
        -------
        Iterable[T]
            iterable of items
        '''
        if search is None:
            iterator = self.collection.find()
        else:
            iterator = self.collection.find(search)
        if sort is not None:
            iterator = iterator.sort(sort)
        for item in iterator:
            yield self.factory(item)

    def getItemById(self, id) -> 'T':
        '''
        search mongodb for a specific item

        Parameters
        ----------
        id: UUID
            id of the object to get

        Returns
        -------
        T | None
            None if the item doesn't exist
        '''
        items = self.collection.find({'_id': id}).limit(1)
        lst = [self.factory(item) for item in items]
        if len(lst) > 0:
            return lst[0]
        return None

    def hasId(self, id):
        '''
        does the database contain an id

        Parameters
        ----------
        id: UUID
            id to check

        Returns
        -------
        bool
            True if the id exists, False if the id doesn't exist
        '''
        items = self.collection.find({'_id': id})
        if next(items, None) is None:
            return False
        return True

    def insertItem(self, item):
        self.collection.insert_one(asdict(item, dict_factory=dict_factory_mongo))

    def updateItem(self, item):
        self.collection.replace_one({'_id': item._id}, asdict(item))

    def removeItem(self, id):
        return self.collection.delete_one({'_id': id})

    def close(self):
        pass


def dict_factory_mongo(items):
    for i in range(len(items)):
        key = items[i][0]
        value = items[i][1]
        if isinstance(value, set):
            items[i] = (key, list(value))
        elif isinstance(value, np.ndarray):
            items[i] = (key, value.tolist())
    return dict(items)


def dict_factory_json(items):
    for i in range(len(items)):
        key = items[i][0]
        value = items[i][1]
        if isinstance(value, set):
            items[i] = (key, list(value))
        elif isinstance(value, np.ndarray):
            items[i] = (key, value.tolist())
        elif isinstance(value, uuid.UUID):
            items[i] = (key, str(value))
    return dict(items)


class FileCollectionStore(CollectionStore[T]):
    def __init__(self, name, factory):
        super().__init__(name, factory)
        try:
            with open(self.name) as f:
                self.items = json.load(f)
        except FileNotFoundError as e:
            logging.warn(f'file {self.name} not found creating')
            with open(self.name, 'w') as f:
                json.dump([], f)
            self.items = []

    def __del__(self):
        if self.items is not None:
            logging.error('store not closed updates to store are not saved!')

    def close(self):
        with open(self.name, 'w') as f:
            json.dump(self.items, f)
        self.items = None

    def getItems(self):
        return [self.factory(item) for item in self.items]

    def getItemsIterator(self, sort: list = [], search: dict = None) -> Iterable[T]:

        def compare(a, b):
            for keys, value in sort:
                ap = a
                bp = b
                for key in keys.split('.'):
                    ap = ap[key]
                    bp = bp[key]
                if ap != bp and value > 0:
                    return value * (1 if ap < bp else -1)
            return 0

        return map(self.factory, sorted(self.items, key=cmp_to_key(compare)))

    def getItemById(self, id):
        item = [self.factory(item) for item in self.items if item.get('_id') == str(id)]
        if len(item) > 0:
            return item[0]
        return None

    def insertItem(self, item):
        self.items.append(asdict(item, dict_factory=dict_factory_json))

    def updateItem(self, item):
        for i in range(len(self.items)):
            if item._id == self.items[i]['_id']:
                self.items[i].update(asdict(item, dict_factory=dict_factory_json))

    def hasId(self, id):
        for item in self.items:
            if item['_id'] == id:
                return True
        return False

    def removeItem(self, id):
        for i, item in enumerate(self.items):
            if item['_id'] == str(id):
                self.items.pop(i)
                break


class CollectionStoreFactory:
    '''
    get a store with a name
    '''
    def __init__(self):
        '''store parameters are set in the configuration file'''
        config = ConfigurationFactory.getInstance()
        config['database'] = config.get('database', {})
        config['database']['experiments'] = config['database'].get('experiments', {})
        config['database']['regions'] = config['database'].get('regions', {})
        config['database']['results'] = config['database'].get('results', {})
        config['database']['experiments']['type'] = config['database']['experiments'].get('type', 'mongo')
        config['database']['experiments']['location'] = config['database']['experiments'].get('location', 'experiments')
        config['database']['regions']['type'] = config['database']['regions'].get('type', 'mongo')
        config['database']['regions']['location'] = config['database']['regions'].get('location', 'regions')
        config['database']['results']['type'] = config['database']['results'].get('type', 'mongo')
        config['database']['results']['location'] = config['database']['results'].get('location', 'results')
        self.config: dict = config['database']

    def getStore(self, name: str, factory: Callable[[dict], T]) -> CollectionStore[T]:
        '''
        get a store with a name and a deserilization method

        Parameters
        ----------
        name: str
            name of the store
        factory: (dict) -> T
            deserilization method
        T:
            type of object returned
        
        Returns
        -------
        CollectionStore[T]
        '''
        if name not in self.config.keys():
            raise ValueError(f'no store for {name} stores {list(self.config.keys())}')

        store = self.config[name]
        if store['type'] == 'mongo':
            return MongoCollectionStore[T](store['location'], factory)
        elif store['type'] == 'json':
            return FileCollectionStore[T](store['location'], factory)
        else:
            raise ValueError(f'store type {store["type"]} not implemented')
