from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Логин пользователя")
    password: str = Field(..., min_length=4, description="Пароль")

class UserResponse(BaseModel):
    id: int
    username: str