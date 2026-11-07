from db.database import get_db_connection

def seed():
    conn = get_db_connection()
    cur = conn.cursor()
    
    #Очищаем таблицы
    cur.execute("TRUNCATE enrollments, courses RESTART IDENTITY CASCADE;")
    
    courses = [
        ("Python для начинающих", "Иванов", 20),
        ("Backend на FastAPI", "Петров", 15),
        ("Базы данных", "Месенев", 30)
    ]
    for title, teacher, seats in courses:
        cur.execute(
            "INSERT INTO courses (title, teacher, seats) VALUES (%s, %s, %s)",
            (title, teacher, seats)
        )
        
    enrollments = [
        ("Студент 1", "s1@mail.ru", "2026-10-01", 1),
        ("Студент 2", "s2@mail.ru", "2026-10-02", 1),
        ("Студент 3", "s3@mail.ru", "2026-10-03", 2),
    ]
    for student, email, date, course_id in enrollments:
        cur.execute(
            "INSERT INTO enrollments (student, email, enrolled_at, course_id) VALUES (%s, %s, %s, %s)",
            (student, email, date, course_id)
        )
        
    conn.commit()
    cur.close()
    conn.close()
    print("БД успешно заполнена тестовыми данными!")

if __name__ == "__main__":
    seed()