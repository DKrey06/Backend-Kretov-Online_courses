from pydantic import BaseModel, Field, EmailStr

class EnrollmentCreate(BaseModel):
    student: str = Field(..., min_length=1, description="Имя слушателя")
    email: EmailStr = Field(..., description="Email слушателя")
    enrolled_at: str = Field(..., description="Дата записи (YYYY-MM-DD)")

class EnrollmentResponse(EnrollmentCreate):
    id: int
    course_id: int