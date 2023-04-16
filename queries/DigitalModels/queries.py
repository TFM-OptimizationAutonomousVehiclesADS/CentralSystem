from queries.client import db
import pymongo
import datetime
import os
import json

collection = db.DigitalModels
# USE DISK LOCAL TO SAVE JSON OF DIGITAL MODELS
root_dir = "/opt/CentralSystem/queries/DigitalModels/jsonData/"

if not os.path.isdir(root_dir):
    os.makedirs(root_dir)

def addOrUpdateDigitalModel(digitalModelId, digitalModelJson):
    fullpath = root_dir + digitalModelId + ".json"

    digitalModelJson["digitalModelId"] = digitalModelId
    digitalModelJson["updatedAt"] = datetime.datetime.now()

    if not os.path.exists(fullpath):
        digitalModelJson["createdAt"] = datetime.datetime.now()
        with open(fullpath, 'w') as outfile:
            json.dump(digitalModelJson, outfile)
    else:
        with open(fullpath, 'r') as outfile:
            actualDataJson = json.load(outfile)
        actualDataJson.update(digitalModelJson)
        with open(fullpath, 'w') as outfile:
            json.dump(actualDataJson, outfile)

    # result = collection.find_one({"digitalModelId": digitalModelId})
    # if not result:
    #     digitalModelJson["createdAt"] = datetime.datetime.now()
    #     result = collection.insert_one(digitalModelJson)
    # else:
    #     newValues = {"$set": digitalModelJson}
    #     result = collection.update_one({"digitalModelId": digitalModelId}, newValues)
    # return result

def addOrUpdateDigitalModelMongo(digitalModelId, digitalModelJson):
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
    result = []
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            fullpath = os.path.join(root_dir, filename)
            with open(fullpath, 'r') as outfile:
                dataJson = json.load(outfile)
            result.append(dataJson)
    # result = list(collection.find().sort("createdAt", pymongo.DESCENDING))
    return result

def findDigitalModelById(digitalModelId):
    fullpath = root_dir + digitalModelId + ".json"
    with open(fullpath, 'r') as outfile:
        result = json.load(outfile)
    # result = collection.find_one({"digitalModelId": digitalModelId}, sort=[("createdAt", pymongo.DESCENDING)])
    return result

def findDigitalModelByIdMongo(digitalModelId):
    result = collection.find_one({"digitalModelId": digitalModelId}, sort=[("createdAt", pymongo.DESCENDING)])
    return result

def findQueryDigitalModelById(digitalModelId, query):
    fullpath = root_dir + digitalModelId + ".json"
    with open(fullpath, 'r') as outfile:
        result = json.load(outfile)
    # result = collection.find_one({"digitalModelId": digitalModelId}, sort=[("createdAt", pymongo.DESCENDING)])
    result = result.get("query").get(query)
    return result