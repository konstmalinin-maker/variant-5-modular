"""SQLite с внешними ключами и транзакционной заменой снимка."""

import sqlite3
from contextlib import closing

from src.domain.entities.university import Course, Grade, State, StorageError, Student
from src.domain.repositories.university_repository import UniversityRepository

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS students (id TEXT PRIMARY KEY, name TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS courses (id TEXT PRIMARY KEY, title TEXT NOT NULL, credits INTEGER NOT NULL CHECK(credits BETWEEN 1 AND 60))",
    "CREATE TABLE IF NOT EXISTS grades (student_id TEXT REFERENCES students(id), course_id TEXT REFERENCES courses(id), value INTEGER CHECK(value BETWEEN 2 AND 5), PRIMARY KEY(student_id,course_id))",
)


class SQLiteRepository(UniversityRepository):
    def __init__(self, path):
        self.path = str(path)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @staticmethod
    def schema(db):
        for statement in SCHEMA:
            db.execute(statement)

    def load(self) -> State:
        try:
            with closing(self.connect()) as db, db:
                self.schema(db)
                return State(
                    tuple(Student(*r) for r in db.execute("SELECT * FROM students ORDER BY rowid")),
                    tuple(Course(*r) for r in db.execute("SELECT * FROM courses ORDER BY rowid")),
                    tuple(Grade(*r) for r in db.execute("SELECT * FROM grades ORDER BY rowid")),
                )
        except sqlite3.Error as exc:
            raise StorageError(f"Ошибка чтения SQLite: {exc}") from exc

    def save(self, state: State) -> None:
        try:
            with closing(self.connect()) as db, db:
                self.schema(db)
                for table in ("grades", "students", "courses"):
                    db.execute(f"DELETE FROM {table}")
                db.executemany("INSERT INTO students VALUES (?,?)", [(s.id, s.name) for s in state.students])
                db.executemany(
                    "INSERT INTO courses VALUES (?,?,?)", [(c.id, c.title, c.credits) for c in state.courses]
                )
                db.executemany(
                    "INSERT INTO grades VALUES (?,?,?)",
                    [(g.student_id, g.course_id, g.value) for g in state.grades],
                )
        except sqlite3.Error as exc:
            raise StorageError(f"Ошибка записи SQLite: {exc}") from exc
