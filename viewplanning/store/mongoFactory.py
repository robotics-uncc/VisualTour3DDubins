from pymongo import MongoClient
import os
from viewplanning.configuration import ConfigurationFactory


class MongoFactory:
    '''
    Singleton mehtod for creating connections to the mongodb database
    '''
    _instances = {}

    @staticmethod
    def getMongoClient():
        '''
        get a mongodb client
        '''
        pid = os.getpid()
        if pid not in MongoFactory._instances:
            config = ConfigurationFactory.getInstance()['database']['mongo']
            MongoFactory._instances[pid] = MongoClient(host=config['host'], port=config['port'])
        return MongoFactory._instances[pid]
