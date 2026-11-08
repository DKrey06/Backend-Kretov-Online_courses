#Основной файлик с апи 
from fastapi import FastAPI, HTTPException, status, Request, Depends
from typing import List, Optional

from models import CourseCreate, CourseUpdate, CourseResponse, EnrollmentCreate, EnrollmentResponse
from models import UserCreate, UserResponse
from auth import get_password_hash, get_current_user

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import time

from db.database import get_db_connection, init_db

app = FastAPI(title="API Онлайн-курсов")

#Инициализация БД
@app.on_event("startup")
def on_startup():
    init_db()

#Для логов
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
     start_time = time.time()
     response = await call_next(request)
     process_time = (time.time() - start_time) *1000
     print(f"{request.method} {request.url.path} {response.status_code} {process_time:.1f}ms")
     return response

@app.get("/health")
def health_check():
	return{"status": "ok"}

#Авторизация
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    
    #Проверка, нет ли такого пользователя
    cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
        
    hashed = get_password_hash(user.password)
    cur.execute(
        "INSERT INTO users (username, hashed_password) VALUES (%s, %s) RETURNING id",
        (user.username, hashed)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "username": user.username}

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

#Курсы
@app.post("/api/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO courses (title, teacher, seats, owner_id) VALUES (%s, %s, %s, %s) RETURNING id",
        (course.title, course.teacher, course.seats, current_user["id"])
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "owner_id": current_user["id"], **course.model_dump()} 

@app.get("/api/courses", response_model=List[CourseResponse])
def get_courses(limit: int = 10, offset: int = 0, q: Optional[str] = None, title: Optional[str] = None,
teacher: Optional[str] = None):
    conn = get_db_connection()
    cur = conn.cursor()

    query = "SELECT id, title, teacher, seats, owner_id FROM courses WHERE 1=1"
    params = []

    if q: 
        query += " AND title ILIKE %s"
        params.append(f"%{q}%")
    
    if title:
        query += " AND title ILIKE %s"
        params.append(f"%{title}%")
    if teacher:
        query += " AND teacher ILIKE %s"
        params.append(f"%{teacher}%")
        
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{"id": r[0], "title": r[1], "teacher": r[2], "seats": r[3], "owner_id": r[4]} for r in rows]

@app.get("/api/courses/stats")
def get_course_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    #Агрегатный запрос. Считаем количество записей на каждый курс
    cur.execute("""
        SELECT c.id, c.title, c.seats, COUNT(e.id) as enrolled
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id, c.title, c.seats
        ORDER BY c.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    stats = []
    for r in rows:
        course_id, title, seats, enrolled = r
        percent = round((enrolled / seats * 100), 1) if seats > 0 else 0.0
        stats.append({
            "course_id": course_id,
            "title": title,
            "seats": seats,
            "enrolled": enrolled,
            "fill_percent": percent
        })
        
    return stats

@app.get("/api/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, teacher, seats, owner_id FROM courses WHERE id = %s", (course_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Курс не найден :(")
        
    return {"id": row[0], "title": row[1], "teacher": row[2], "seats": row[3], "owner_id": row[4]}

@app.put("/api/courses/{course_id}", response_model=CourseResponse)
def update_course_put(course_id: int, course_data: CourseCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    #Проверка владельца
    cur.execute("SELECT owner_id FROM courses WHERE id = %s", (course_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Курс не найден")
    if row[0] != current_user["id"]:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Нельзя изменять чужую запись")

    cur.execute(
        "UPDATE courses SET title = %s, teacher = %s, seats = %s WHERE id = %s RETURNING id",
        (course_data.title, course_data.teacher, course_data.seats, course_id)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated:
        raise HTTPException(status_code=404, detail="Курс не найден")
        
    return {"id": course_id, "owner_id": current_user["id"], **course_data.model_dump()}

@app.patch("/api/courses/{course_id}", response_model=CourseResponse)
def update_course_patch(course_id: int, course_update: CourseUpdate, current_user: dict = Depends(get_current_user)):
    update_data = course_update.model_dump(exclude_unset=True)

    if not update_data:
        return get_course(course_id)
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT owner_id FROM courses WHERE id = %s", (course_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Курс не найден")
    if row[0] != current_user["id"]:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Нельзя изменять чужую запись")

    set_clauses = [f"{key} = %s" for key in update_data.keys()]
    values = list(update_data.values())
    values.append(course_id)
    
    query = f"UPDATE courses SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, title, teacher, seats"
    
    cur.execute(query, tuple(values))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated:
        raise HTTPException(status_code=404, detail="Курс не найден")
        
    return {"id": updated[0], "title": updated[1], "teacher": updated[2], "seats": updated[3], "owner_id": current_user["id"]}

@app.delete("/api/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT owner_id FROM courses WHERE id = %s", (course_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Курс не найден")
    if row[0] != current_user["id"]:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Нельзя изменять чужую запись")

    cur.execute("DELETE FROM courses WHERE id = %s RETURNING id", (course_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return


@app.post("/api/courses/{course_id}/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(course_id: int, enrollment: EnrollmentCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        #Блок строки курса, чтобы никто не изменил seats во время проверки
        cur.execute("SELECT seats FROM courses WHERE id = %s FOR UPDATE", (course_id,))
        course = cur.fetchone()
        
        if not course:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        seats_total = course[0]
        
        cur.execute("SELECT COUNT(*) FROM enrollments WHERE course_id = %s", (course_id,))
        enrolled_count = cur.fetchone()[0]
        
        if enrolled_count >= seats_total:
            raise HTTPException(
                status_code=409, 
                detail="На курс больше нет свободных мест"
            )
        
        cur.execute(
            "INSERT INTO enrollments (student, email, enrolled_at, course_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (enrollment.student, enrollment.email, enrollment.enrolled_at, course_id)
        )
        new_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {"id": new_id, "course_id": course_id, **enrollment.model_dump()}
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {e}")
    finally:
        cur.close()
        conn.close()

@app.get("/api/courses/{course_id}/enrollments", response_model=List[EnrollmentResponse])
def get_enrollments(course_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT id, student, email, enrolled_at, course_id FROM enrollments WHERE course_id = %s ORDER BY id",
        (course_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{
        "id": r[0], 
        "student": r[1], 
        "email": r[2], 
        "enrolled_at": str(r[3]),
        "course_id": r[4]
    } for r in rows]


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error = exc.errors()[0]
    field_name = str(error["loc"][-1])
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": error["msg"], "field": field_name}
    )