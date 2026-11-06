<!--
  Это шаблон README проекта. После создания своего репозитория:
  1. Переименовать репозиторий в backend-<фамилия>-<тема>, например backend-ivanova-library.
  2. Заполнить разделы ниже под свою тему и удалить этот комментарий.
  Задания лаб лежат в папке docs/, начинать с docs/README.md.
-->

# Backend: Онлайн-курсы

Тема №12: **Онлайн-курсы**. Сервис для управления каталогом образовательных курсов, позволяющий добавлять, просматривать и редактировать информацию о занятиях. Предназначен для студентов и преподавателей.

|                          |                                       |
| ------------------------ | ------------------------------------- |
| Главная сущность         | Курс (Course)                         |
| Связанная сущность (1:N) | Запись (Enrollment)                   |
| Фишка                    | ...                                   |
| Стек                     | Python, FastAPI, Pydantic, PostgreSQL |

## Как запустить

```bash
# 1. Клонировать репозиторий
git clone https://github.com/DKrey06/Backend-Kretov-Online_courses.git
cd Backend-Kretov-Online_courses

# 2. Создать и активировать виртуальное окружение
python -m venv venv
.\venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Применить миграции базы данных
alembic upgrade head

# 5. Запустить сервер
uvicorn main:app --reload

# 6. Заполнить БД тестовыми данными (опционально)
python seed.py
```

Сервис работает на `http://localhost:8000`. Запросы для демонстрации лежат в `requests.http`.

## Эндпоинты

| Метод  | Путь                            | Что делает               | Ответ                               |
| ------ | ------------------------------- | ------------------------ | ----------------------------------- |
| GET    | `/health`                       | Проверка, что сервис жив | 200 `{"status":"ok"}`               |
| POST   | `/api/courses`                  | Создать курс             | 201 и объект с `id`; 400 при ошибке |
| GET    | `/api/courses`                  | Список курсов            | 200                                 |
| GET    | `/api/courses/{id}`             | Получить один курс       | 200; 404                            |
| PATCH  | `/api/courses/{id}`             | Частично изменить        | 200; 400; 404                       |
| PUT    | `/api/courses/{id}`             | Полностью заменить       | 200; 400; 404                       |
| DELETE | `/api/courses/{id}`             | Удалить                  | 204; 404                            |
| POST   | `/api/courses/{id}/enrollments` | Создать запись на курс   | 201 и объект записи; 400/404        |
| GET    | `/api/courses/{id}/enrollments` | Список записей курса     | 200                                 |

## ER-диаграмма

<!-- С лабы 2. Блок mermaid GitHub рисует сам. -->

```mermaid
erDiagram
    courses ||--o{ enrollments : "имеет"
    courses {
        int id PK
        varchar title
        varchar teacher
        int seats
    }
    enrollments {
        int id PK
        varchar student
        varchar email
        date enrolled_at
        int course_id FK
    }
```

## Индекс и EXPLAIN

Для ускорения поиска по названию курса создан индекс `ix_courses_title` на колонку `title` (создан через Alembic-миграцию).

Пример запроса и его план выполнения:

```sql
EXPLAIN ANALYZE SELECT * FROM courses WHERE title = 'Backend на FastAPI';
```

Вывод:

```
 Index Scan using ix_courses_title on courses  (cost=0.15..8.17 rows=1 width=32) (actual time=0.023..0.024 rows=0.00 loops=1)
   Index Cond: ((title)::text = 'Backend на FastAPI'::text)
   Index Searches: 1
   Buffers: shared hit=1
 Planning:
   Buffers: shared hit=35
 Planning Time: 2.580 ms
 Execution Time: 0.043 ms
(8 строк)
```

## Интерфейс

<!-- С лабы 4: скриншот, например ![Интерфейс](docs/screenshot.png) -->
