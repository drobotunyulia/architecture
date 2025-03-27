from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from auth.auth import get_current_user

# Временное хранилище чатов
chats_db = {}

class Chat(BaseModel):
    id: int
    name: str
    members: List[str]

class ChatCreate(BaseModel):
    name: str

class AddUserToChat(BaseModel):
    username: str

chat_router = APIRouter()

# Создать новый чат
@chat_router.post("/chats/")
def create_chat(chat: ChatCreate, current_user: Dict = Depends(get_current_user)):
    chat_id = len(chats_db) + 1
    new_chat = {
        "id": chat_id,
        "name": chat.name,
        "members": [current_user["username"]],  # Создатель автоматически добавляется в чат
    }
    chats_db[chat_id] = new_chat
    return {"message": "Chat created successfully", "chat": new_chat}

# Добавить пользователя в чат
@chat_router.post("/chats/{chat_id}/add_user/")
def add_user_to_chat(chat_id: int, user_data: AddUserToChat, current_user: Dict = Depends(get_current_user)):
    chat = chats_db.get(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user["username"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    if user_data.username in chat["members"]:
        raise HTTPException(status_code=400, detail="User already in chat")

    chat["members"].append(user_data.username)
    return {"message": f"User {user_data.username} added to chat {chat_id}"}

# Получить список чатов пользователя
@chat_router.get("/chats/")
def get_user_chats(current_user: Dict = Depends(get_current_user)):
    user_chats = [chat for chat in chats_db.values() if current_user["username"] in chat["members"]]
    return {"chats": user_chats}

# Получить информацию о конкретном чате
@chat_router.get("/chats/{chat_id}")
def get_chat(chat_id: int, current_user: Dict = Depends(get_current_user)):
    chat = chats_db.get(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user["username"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    return chat
