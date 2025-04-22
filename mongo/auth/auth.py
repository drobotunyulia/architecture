from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from data import db as database
from data import models

# Настройки JWT
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Безопасность
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Создание роутеров
token_router = APIRouter()
user_router = APIRouter()


# ===========================
# Pydantic-модели
# ===========================
class UserCreate(BaseModel):
    username: str
    password: str
    age: Optional[int] = None


class UserRead(BaseModel):
    id: int
    username: str
    age: Optional[int]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: str


# ===========================
# Работа с БД
# ===========================
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===========================
# Утилиты
# ===========================
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ===========================
# CRUD-функции
# ===========================
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, id: int):
    return db.query(models.User).filter(models.User.id == id).first()


def create_user_in_db(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pw, age=user.age)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user_by_id(db: Session, id: int):
    user = get_user_by_id(db, id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def update_user_username(db: Session, id: int, username: str):
    user = get_user_by_id(db, id)
    if user:
        user.username = username
        db.commit()
        db.refresh(user)
        return user
    return None


# ===========================
# Авторизация
# ===========================
@token_router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user


# ===========================
# Роуты пользователей
# ===========================
@user_router.post("/users/", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    return create_user_in_db(db, user)

@user_router.get("/users/{id}", response_model=UserRead)
def get_user_info_by_id(id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@user_router.delete("/users/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account."
        )

    deleted = delete_user_by_id(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return {"detail": f"User with id {id} has been deleted."}


@user_router.put("/users/{id}/username", response_model=UserRead)
def update_user_username_by_id(id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    updated_user = update_user_username(db, id, user_update.username)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user
