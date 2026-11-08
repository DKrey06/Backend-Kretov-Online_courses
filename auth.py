from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from db.database import get_db_connection

#Настройка хеширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Схема Basic Auth для Swagger и защиты
security = HTTPBasic()

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, hashed_password FROM users WHERE username = %s", (credentials.username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not verify_password(credentials.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"id": user[0], "username": user[1]}