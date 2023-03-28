from queries.client import db
import pymongo
import datetime
import os

collection = db.Users

def addNewUser(userJson):
    result = collection.insert_one(userJson)
    return result

def getUserByUsername(username):
    result = collection.find_one({"username": username})
    return result