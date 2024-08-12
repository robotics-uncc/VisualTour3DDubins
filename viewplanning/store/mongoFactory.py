from pymongo import MongoClient
import os
from viewplanning.configuration import ConfigurationFactory
from bson.codec_options import CodecOptions
from bson.binary import STANDARD



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
            db = config['db']
            if 'user' in config and 'password' in config:
                MongoFactory._instances[pid] = MongoClient(host=config['host'], port=config['port'], username=config['user'], password=config['password']).get_database(db, codec_options=CodecOptions(uuid_representation=STANDARD))
            else:
                MongoFactory._instances[pid] = MongoClient(host=config['host'], port=config['port']).get_database(db, codec_options=CodecOptions(uuid_representation=STANDARD))
        return MongoFactory._instances[pid]
