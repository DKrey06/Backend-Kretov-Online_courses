#Основной файлик с апи 
from fastapi import FastAPI, HTTPException, status
from typing import List

from models import CourseCreate, CourseUpdate, CourseResponse

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="API Онлайн-курсов")

courses_db = []
current_id = 1

@app.get("/health")
def health_check():
	return{"status": "ok"}

@app.post("/api/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate):
	global current_id
	new_course = {"id": current_id, **course.model_dump()} #Pydantic сделает словарем
	courses_db.append(new_course)
	current_id+=1
	return new_course

@app.get("/api/courses", response_model=List[CourseResponse])
def get_courses():
	return courses_db

@app.get("/api/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int):
	for course in courses_db:
		if course["id"] == course_id:
			return course
	raise HTTPException(status_code=404, detail="Курс не найден :(")

@app.put("/api/courses/{course_id}", response_model=CourseResponse)
def update_course_put(course_id: int, course_data: CourseCreate):
    for index, course in enumerate(courses_db):
        if course["id"] == course_id:
            updated_course = {
                "id": course_id,
                **course_data.model_dump()
            }
            courses_db[index] = updated_course
            return updated_course
    raise HTTPException(status_code=404, detail="Курс не найден")

@app.patch("/api/courses/{course_id}", response_model=CourseResponse)
def update_course_patch(course_id: int, course_update: CourseUpdate):
    for index, course in enumerate(courses_db):
        if course["id"] == course_id:
            update_data = course_update.model_dump(exclude_unset=True)
            courses_db[index].update(update_data)
            return courses_db[index]
    raise HTTPException(status_code=404, detail="Курс не найден")

@app.delete("/api/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int):
    for index, course in enumerate(courses_db):
        if course["id"] == course_id:
            courses_db.pop(index)
            return
    raise HTTPException(status_code=404, detail="Курс не найден")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Ошибка валидации данных"}
    )