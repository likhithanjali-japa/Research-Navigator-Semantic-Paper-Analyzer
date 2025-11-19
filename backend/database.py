from pymongo import MongoClient
import os

# FIXED: Use local MongoDB instead of docker hostname 'mongo'
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("MONGO_DB", "paperiq")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db["users"]
papers = db["papers"]
search_logs = db["search_logs"]
feedbacks = db["feedbacks"]
analytics = db["analytics"]
