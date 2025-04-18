from pymongo import MongoClient, ASCENDING
from db import collection, collection_users

collection.create_index([('Name', ASCENDING)])
collection.create_index([('Type', ASCENDING)])
collection_users.create_index([('username', ASCENDING)], unique=True)
