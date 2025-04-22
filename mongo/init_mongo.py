from mongo_data import mongo

def init_chats():
    if mongo.chat_collection.count_documents({}) == 0:
        mongo.chat_collection.insert_many([
            {
                "name": "Python Lovers",
                "creator_id": 1,
                "participant_ids": [1]
            },
            {
                "name": "FastAPI Fans",
                "creator_id": 1,
                "participant_ids": [1]
            }
        ])
    else:
        print("Чаты уже существуют.")

if __name__ == "__main__":
    init_chats()