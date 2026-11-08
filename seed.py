from db.database import get_db_connection
from auth import get_password_hash

def seed():
    conn = get_db_connection()
    cur = conn.cursor()
    
    #Очищаем таблицы
    cur.execute("TRUNCATE enrollments, courses RESTART IDENTITY CASCADE;")
    
    #Создаем тестового пользователя для привязки курсов
    hashed_pw = get_password_hash("secret123")
    cur.execute(
        "INSERT INTO users (username, hashed_password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING RETURNING id",
        ("testuser", hashed_pw)
    )
    row = cur.fetchone()
    if row:
        owner_id = row[0]
    else:
        #Если пользователь уже существовал, достаем его ID
        cur.execute("SELECT id FROM users WHERE username = %s", ("testuser",))
        owner_id = cur.fetchone()[0]
    
    courses = [
        ("Python для начинающих", "Иванов", 20),
        ("Backend на FastAPI", "Петров", 15),
        ("Базы данных", "Месенев", 30)
    ]
    for title, teacher, seats in courses:
        cur.execute(
            "INSERT INTO courses (title, teacher, seats, owner_id) VALUES (%s, %s, %s, %s)",
            (title, teacher, seats, owner_id)
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