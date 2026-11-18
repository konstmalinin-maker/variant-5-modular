"""Flat: бизнес-операции непосредственно зависят от database.SQLiteRepository."""

from dataclasses import replace
from uuid import uuid4

from src.domain.entities.university import Course, Grade, NotFoundError, Student, ValidationError
from src.domain.repositories.university_repository import UniversityRepository
from src.domain.validation import integer, text


class UniversityService:
    def __init__(self, repo: UniversityRepository):
        self.repo = repo

    def add_student(self, name: str) -> Student:
        student = Student(str(uuid4()), text(name, "Имя"))
        state = self.repo.load()
        self.repo.save(replace(state, students=(*state.students, student)))
        return student

    def add_course(self, title: str, credits: int) -> Course:
        course = Course(str(uuid4()), text(title, "Курс"), integer(credits, 1, 60, "Кредиты"))
        state = self.repo.load()
        self.repo.save(replace(state, courses=(*state.courses, course)))
        return course

    @staticmethod
    def student(state, student_id):
        for student in state.students:
            if student.id == student_id:
                return student
        raise NotFoundError("Студент не найден")

    @staticmethod
    def course(state, course_id):
        for course in state.courses:
            if course.id == course_id:
                return course
        raise NotFoundError("Курс не найден")

    def enroll(self, student_id: str, course_id: str) -> Grade:
        state = self.repo.load()
        self.student(state, student_id)
        self.course(state, course_id)
        if any(g.student_id == student_id and g.course_id == course_id for g in state.grades):
            raise ValidationError("Студент уже записан на курс")
        entry = Grade(student_id, course_id)
        self.repo.save(replace(state, grades=(*state.grades, entry)))
        return entry

    def list(self, student_id: str) -> list[tuple[Course, int | None]]:
        state = self.repo.load()
        self.student(state, student_id)
        courses = {c.id: c for c in state.courses}
        return sorted(
            [(courses[g.course_id], g.value) for g in state.grades if g.student_id == student_id],
            key=lambda item: item[0].title.casefold(),
        )

    def grade(self, student_id: str, course_id: str, value: int) -> Grade:
        integer(value, 2, 5, "Оценка")
        state = self.repo.load()
        self.student(state, student_id)
        self.course(state, course_id)
        for index, old in enumerate(state.grades):
            if old.student_id == student_id and old.course_id == course_id:
                updated = replace(old, value=value)
                rows = list(state.grades)
                rows[index] = updated
                self.repo.save(replace(state, grades=tuple(rows)))
                return updated
        raise NotFoundError("Студент не записан на курс")

    def gpa(self, student_id: str) -> float:
        graded = [(course, value) for course, value in self.list(student_id) if value is not None]
        if not graded:
            raise ValidationError("Нет выставленных оценок для GPA")
        return sum(c.credits * value for c, value in graded) / sum(c.credits for c, _ in graded)

    def drop(self, student_id: str, course_id: str) -> None:
        state = self.repo.load()
        self.student(state, student_id)
        self.course(state, course_id)
        rows = tuple(g for g in state.grades if (g.student_id, g.course_id) != (student_id, course_id))
        if len(rows) == len(state.grades):
            raise NotFoundError("Студент не записан на курс")
        self.repo.save(replace(state, grades=rows))
