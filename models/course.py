from pydantic import BaseModel, Field
from typing import Optional

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Название курса")
    teacher: str = Field(..., min_length=1, description="Преподаватель")
    seats: int = Field(..., ge=0, description="Количество мест")

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    teacher: Optional[str] = Field(None, min_length=1)
    seats: Optional[int] = Field(None, ge=0)

class CourseResponse(CourseCreate):
    id: int