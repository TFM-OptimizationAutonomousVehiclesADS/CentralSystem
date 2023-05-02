from queries.client import db
import pymongo
import datetime
import os
import json

collection = db.AlertsMessages

def addAlertMessage(message, typeMessage, typeAlert, digitalModel=None, evaluation_dict=None):
    timestamp = datetime.datetime.now()
    alert = {
        "typeAlert": message,
        "digitalModel": digitalModel,
        "evaluation_dict": evaluation_dict,
        "message": message,
        "typeMessage": typeMessage, # alert, success, error
        "timestamp": timestamp,
        "delivered": False
    }
    collection.insert_one(alert)

def deliveredAlertMessage(messageId):
    collection.update_one({"_id": messageId}, {"$set": {"delivered": True}})
    return True

def deliveredAllAlertsMessages():
    collection.update_many({}, {"$set": {"delivered": True}})
    return True

def findAllAlertsMessages():
    result = []
    result = list(collection.find({}, {'_id': False}).sort("timestamp", pymongo.DESCENDING))
    return result

def findAllAlertsMessagesFederative():
    result = []
    result = list(collection.find({"typeAlert": "FEDERATIVE"}, {'_id': False}).sort("timestamp", pymongo.DESCENDING))
    return result

def findAllAlertsMessagesNoDelivered():
    result = []
    result = list(collection.find({"delivered": False}, {'_id': False}).sort("timestamp", pymongo.DESCENDING))
    return result