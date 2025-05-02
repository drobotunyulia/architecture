from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)

db = client["messenger_db"]
chat_collection = db["chats"]

# Индексы (поиск по имени и создателю)
chat_collection.create_index("name")
chat_collection.create_index("creator_id")
