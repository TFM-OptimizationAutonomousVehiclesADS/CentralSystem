from queries.client import db
import pymongo
import datetime
import os

collection = db.DigitalModels

def addOrUpdateDigitalModel(digitalModelId, digitalModelJson):
    digitalModelJson["digitalModelId"] = digitalModelId
    digitalModelJson["updatedAt"] = datetime.datetime.now()

    result = collection.find_one({"digitalModelId": digitalModelId})
    if not result:
        digitalModelJson["createdAt"] = datetime.datetime.now()
        result = collection.insert_one(digitalModelJson)
    else:
        newValues = {"$set": digitalModelJson}
        result = collection.update_one({"digitalModelId": digitalModelId}, newValues)
    return result

def findAllDigitalModels():
    result = list(collection.find().sort("createdAt", pymongo.DESCENDING))
    return result

def findDigitalModelById(digitalModelId):
    result = collection.find_one({"digitalModelId": digitalModelId}, sort=[("createdAt", pymongo.DESCENDING)])
    return result

def findQueryDigitalModelById(digitalModelId, query):
    result = collection.find_one({"digitalModelId": digitalModelId}, sort=[("createdAt", pymongo.DESCENDING)])
    result = result.get("query").get(query)
    return result