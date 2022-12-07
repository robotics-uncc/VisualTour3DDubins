from pymongo import MongoClient
import os
from viewplanning.configuration import ConfigurationFactory

class MongoFactory:
    _instances = {}
    @staticmethod
    def getMongoClient():
        pid = os.getpid()
        if pid not in MongoFactory._instances:
            config = ConfigurationFactory.getInstance()['database']['mongo']
            MongoFactory._instances[pid] = MongoClient(host=config['host'], port=config['port'])
        return MongoFactory._instances[pid]
