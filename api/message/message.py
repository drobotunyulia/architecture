from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from auth.auth import get_current_user
from chat.chat import chats_db

messages_db = {}

class Message(BaseModel):
    chat_id: int
    sender: str
    text: str
    timestamp: datetime
    message_id: int

class MessageCreate(BaseModel):
    text: str

message_router = APIRouter()

@message_router.post("/chats/{chat_id}/messages/")
def send_message(chat_id: int, message_data: MessageCreate, current_user: Dict = Depends(get_current_user)):
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = chats_db[chat_id]
    if current_user["username"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    # Генерируем уaникальный идентификатор для сообщения
    message_id = len(messages_db.get(chat_id, [])) + 1

    new_message = {
        "message_id": message_id,
        "chat_id": chat_id,
        "sender": current_user["username"],
        "text": message_data.text,
        "timestamp": datetime.utcnow()
    }

    if chat_id not in messages_db:
        messages_db[chat_id] = []
    messages_db[chat_id].append(new_message)

    return {"message": "Message sent successfully", "data": new_message}

# Получение сообщений из чата
@message_router.get("/chats/{chat_id}/messages/")
def get_chat_messages(chat_id: int, current_user: Dict = Depends(get_current_user)):
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = chats_db[chat_id]
    if current_user["username"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    return {"messages": messages_db.get(chat_id, [])}

# Удаление сообщения
@message_router.delete("/chats/{chat_id}/messages/{message_id}/")
def delete_message(chat_id: int, message_id: int, current_user: Dict = Depends(get_current_user)):
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = chats_db[chat_id]
    if current_user["username"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    messages = messages_db.get(chat_id, [])
    message_to_delete = next((message for message in messages if message["message_id"] == message_id), None)

    if not message_to_delete:
        raise HTTPException(status_code=404, detail="Message not found")

    messages_db[chat_id] = [message for message in messages if message["message_id"] != message_id]

    return {"message": f"Message {message_id} deleted successfully"}
