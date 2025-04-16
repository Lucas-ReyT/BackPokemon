import pymongo
from pymongo import MongoClient


client = MongoClient('mongodb+srv://MP-Death30:1234@cluster0.dtgdmge.mongodb.net/myDatabase?retryWrites=true&w=majority')
db = client['Pokemon']
collection = db['Pokemon_collection']
collection_users = db["users"]
type_collection = db['Pokemon_Type']
