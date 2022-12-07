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
    def __init__(self, name):
        self.name = name

    def getItems(self):
        pass

    def insertItem(self, experiment):
        pass

    def close(self):
        pass


class MongoCollectionStore(CollectionStore[T]):
    def __init__(self, name, factory: Callable[[dict], T]):
        super().__init__(name)
        self.client: MongoClient = MongoFactory.getMongoClient()
        self.collection: Collection = self.client.get_database('view_planning', codec_options=CodecOptions(uuid_representation=STANDARD)).get_collection(name)
        self.factory = factory

    def getItems(self) -> 'list[T]':
        items = self.collection.find()
        return [self.factory(item) for item in items]

    def find(self, search):
        items = self.collection.find(search)
        return [self.factory(item) for item in items]

    def getItemsIterator(self, sort: dict = {}) -> 'Iterable[T]':
        for item in self.collection.find().sort(sort):
            yield self.factory(item)

    def getItemById(self, id) -> 'T':
        items = self.collection.find({'_id': id}).limit(1)
        lst = [self.factory(item) for item in items]
        if len(lst) > 0:
            return lst[0]
        return None

    def hasId(self, id):
        items = self.collection.find({'_id': id})
        if next(items, None) is None:
            return False
        return True

    def insertItem(self, item):
        self.collection.insert_one(asdict(item))

    def updateItem(self, item):
        self.collection.replace_one({'_id': item['_id']}, asdict(item))


class FileCollectionStore(CollectionStore[T]):
    def __init__(self, name, factory: Callable[[dict], T]):
        self.name = name
        self.factory = factory
        try:
            with open(self.name) as f:
                self.items = list(map(self.factory, json.load(f)))
        except FileNotFoundError:
            self.items = []

    def __del__(self):
        self.close()

    def close(self):
        with open(self.name) as f:
            json.dump([asdict(item) for item in self.items], f)
        self.items = None

    def getItems(self):
        return self.items

    def getItemById(self, id):
        for item in self.items:
            if item._id == id:
                return item
        return None

    def insertItem(self, item):
        self.items.append(item)

    def updateItem(self, item):
        for i in range(len(self.items)):
            if item._id == self.items[i]._id:
                self.items[i] = item

    def hasId(self, id):
        return self.getItemById(id) is not None

    def getItemsIterator(self, **kwargs) -> 'Iterable[T]':
        return self.getItems()
