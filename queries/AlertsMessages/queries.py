from queries.client import db
import pymongo
import datetime
import os
import json

collection = db.AlertsMessages

def addAlertMessage(message, typeMessage):
    timestamp = datetime.datetime.now()
    alert = {
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
    result = list(collection.find().sort("timestamp", pymongo.DESCENDING))
    return result

def findAllAlertsMessagesNoDelivered():
    result = []
    result = list(collection.find({"delivered": False}).sort("timestamp", pymongo.DESCENDING))
    return result