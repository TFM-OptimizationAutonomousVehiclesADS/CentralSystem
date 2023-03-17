from pymongo import MongoClient
from queries.config import SERVER_URL, DATABASE

client = MongoClient(SERVER_URL)
db = client[DATABASE]
