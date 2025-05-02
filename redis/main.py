from fastapi import FastAPI
from auth.auth import token_router, user_router
from chat.chat import chat_router
# from message.message import message_router


app = FastAPI(title="Messenger API")

app.include_router(token_router, tags=["Auth"])
app.include_router(user_router, tags=["Users"])
app.include_router(chat_router, tags=["Chats"])
# app.include_router(message_router, tags=["Messages"])

@app.get("/")
def root():
    return {"message": "Welcome to Messenger API"}

# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
