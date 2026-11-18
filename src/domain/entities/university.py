"""Вариант 5: неизменяемые сущности и снимок университета."""

from dataclasses import asdict, dataclass


class DomainError(Exception):
    """Ожидаемая ошибка приложения."""


class ValidationError(DomainError):
    """Нарушение правила предметной области."""


class NotFoundError(DomainError):
    """Неизвестный студент, курс или запись."""


class StorageError(DomainError):
    """Ошибка чтения/атомарного сохранения."""


@dataclass(frozen=True)
class Student:
    id: str
    name: str


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    credits: int


@dataclass(frozen=True)
class Grade:
    student_id: str
    course_id: str
    value: int | None = None


@dataclass(frozen=True)
class State:
    students: tuple[Student, ...] = ()
    courses: tuple[Course, ...] = ()
    grades: tuple[Grade, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "State":
        if set(data) != {"students", "courses", "grades"}:
            raise ValueError("Неверная схема снимка")
        return cls(
            tuple(Student(**s) for s in data["students"]),
            tuple(Course(**c) for c in data["courses"]),
            tuple(Grade(**g) for g in data["grades"]),
        )
