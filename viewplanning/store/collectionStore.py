from viewplanning.store.mongoFactory import MongoFactory
from bson.codec_options import CodecOptions
from bson.binary import UuidRepresentation, STANDARD
from dataclasses import asdict
import json
from typing import TypeVar, Generic, Iterable, Callable
from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient
from viewplanning.configuration import ConfigurationFactory


T = TypeVar('T')


class CollectionStore(Generic[T]):
    '''
    Base class for a database like object
    '''

    def __init__(self, name):
        '''
        Parameters
        ----------
        name: str
            name of the store
        '''
        self.name = name

    def getItems(self):
        '''
        get all items from the store

        Returns
        -------
        list
            a list of all items in the store
        '''
        pass

    def insertItem(self, item):
        '''
        inserts and item into the store

        Parameters
        ----------
        item: Any
            Item to insert into the store
        '''
        pass

    def close(self):
        '''
        discards any resources related to the store
        '''
        pass


class MongoCollectionStore(CollectionStore[T]):
    def __init__(self, name, factory: Callable[[dict], T]):
        '''
        Parameters
        ----------
        name: str
            mongodb collection name
        factory: Callable[[dict], T]
            factory method for creating objects from mongodb json
        '''
        super().__init__(name)
        self.client: MongoClient = MongoFactory.getMongoClient()
        self.collection: Collection = self.client.get_database('view_planning', codec_options=CodecOptions(uuid_representation=STANDARD)).get_collection(name)
        self.factory = factory

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

    def getItemsIterator(self, sort: dict = {}) -> 'Iterable[T]':
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
        for item in self.collection.find().sort(sort):
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
        self.collection.insert_one(asdict(item))

    def updateItem(self, item):
        '''
        Update item in store

        Parameters
        ----------
        item: T
            item to update
        '''
        self.collection.replace_one({'_id': item['_id']}, asdict(item))
