from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    id: int
    username: str
    hashed_password: str
    age: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    password: str
    age: Optional[int] = None


# Временное хранилище пользователей
users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "hashed_password": pwd_context.hash("secret"),
        "age": 30
    }
}

client_db = {
    "admin": pwd_context.hash("secret")
}


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(username: str):
    hashed_password = client_db.get(username)
    if hashed_password:
        return {"username": username, "hashed_password": hashed_password}
    return None


token_router = APIRouter()

user_router = APIRouter()


@token_router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except jwt.PyJWTError:
        raise credentials_exception


@user_router.post("/users/")
def create_user(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = len(users_db) + 1
    new_user = {
        "id": user_id,
        "username": user.username,
        "hashed_password": hash_password(user.password),
        "age": user.age
    }
    users_db[user.username] = new_user
    return {"message": "User created successfully", "user": new_user}


@user_router.get("/users/{username}")
def get_user(username: str, current_user: dict = Depends(get_current_user)):
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
