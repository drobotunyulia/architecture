from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from mongo_data import mongo
from fastapi import Depends
from auth.auth import get_current_user
from auth.auth import UserRead

chat_router = APIRouter()

class ChatCreate(BaseModel):
    name: str
    participant_ids: List[int]

class ChatRead(ChatCreate):
    creator_id: int
    id: str

@chat_router.post("/chats/", response_model=ChatRead)
def create_chat(chat: ChatCreate, current_user: UserRead = Depends(get_current_user)):
    chat_dict = chat.dict()
    chat_dict["creator_id"] = current_user.id
    result = mongo.chat_collection.insert_one(chat_dict)
    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Chat creation failed")
    chat_dict["creator_id"] = current_user.id
    chat_dict["id"] = str(result.inserted_id)
    return chat_dict

@chat_router.get("/chats/{chat_id}", response_model=ChatRead)
def get_chat(chat_id: str):
    chat = mongo.chat_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat["id"] = str(chat["_id"])
    return chat

@chat_router.get("/chats/", response_model=List[ChatRead])
def list_chats(current_user: UserRead = Depends(get_current_user)):
    chats = []
    for chat in mongo.chat_collection.find({"creator_id": current_user.id}):
        chat["id"] = str(chat["_id"])
        chats.append(chat)
    return chats

@chat_router.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, current_user: UserRead = Depends(get_current_user)):
    chat = mongo.chat_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat["creator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the creator of this chat")
    result = mongo.chat_collection.delete_one({"_id": ObjectId(chat_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete chat")
    return {"detail": "Chat deleted"}


@chat_router.put("/chats/{chat_id}", response_model=ChatRead)
def update_chat(chat_id: str, chat: ChatCreate):
    result = mongo.chat_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": chat.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    updated = mongo.chat_collection.find_one({"_id": ObjectId(chat_id)})
    updated["id"] = str(updated["_id"])
    return updated

@chat_router.post("/chats/{chat_id}/add_participant")
def add_participant_to_chat(chat_id: str, participant_id: int, current_user: UserRead = Depends(get_current_user)):
    chat = mongo.chat_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat["creator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the creator of this chat")
    if participant_id in chat["participant_ids"]:
        raise HTTPException(status_code=400, detail="Participant already in the chat")
    result = mongo.chat_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {"participant_ids": participant_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to add participant")
    return {"detail": f"Participant {participant_id} added to chat"}
