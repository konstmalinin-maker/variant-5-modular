"""Один контракт для Flat, шагов рефакторинга и Modular."""

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from main import main
from src.domain.entities.university import Course, Grade, NotFoundError, State, StorageError, ValidationError
from src.infrastructure.bootstrap import build_service
from src.infrastructure.persistence.sqlite_repository import SQLiteRepository


@pytest.fixture
def service(tmp_path):
    return build_service(tmp_path / "university.sqlite3")


@pytest.fixture
def enrolled(service):
    student = service.add_student(" Константин ")
    course = service.add_course("Архитектура", 3)
    service.enroll(student.id, course.id)
    return service, student, course


def test_entities_and_roundtrip(enrolled):
    svc, student, course = enrolled
    assert student.name == "Константин"
    assert State.from_dict(svc.repo.load().to_dict()) == svc.repo.load()
    assert svc.list(student.id) == [(course, None)]


def test_bad_schema():
    with pytest.raises(ValueError):
        State.from_dict({})


@pytest.mark.parametrize("name", ["", " ", "a" * 101])
def test_invalid_student(service, name):
    with pytest.raises(ValidationError):
        service.add_student(name)
    assert service.repo.load() == State()


@pytest.mark.parametrize("name", ["a", "a" * 100, " Студент "])
def test_name_boundaries(service, name):
    assert service.add_student(name).name == name.strip()


@pytest.mark.parametrize("credits", [0, 61, True, 2.5])
def test_invalid_credits(service, credits):
    with pytest.raises(ValidationError):
        service.add_course("Курс", credits)


@pytest.mark.parametrize("credits", [1, 60])
def test_credit_boundaries(service, credits):
    assert service.add_course(" Курс ", credits).credits == credits


def test_invalid_course(service):
    with pytest.raises(ValidationError):
        service.add_course("", 1)


def test_duplicate_enrollment(enrolled):
    svc, s, c = enrolled
    before = svc.repo.load()
    with pytest.raises(ValidationError, match="уже"):
        svc.enroll(s.id, c.id)
    assert svc.repo.load() == before


@pytest.mark.parametrize("value", [2, 3, 4, 5])
def test_grade_and_update(enrolled, value):
    svc, s, c = enrolled
    assert svc.grade(s.id, c.id, value) == Grade(s.id, c.id, value)
    assert svc.list(s.id) == [(c, value)]
    assert svc.gpa(s.id) == value


@pytest.mark.parametrize("value", [1, 6, 0, True, 3.5])
def test_invalid_grade_preserves_state(enrolled, value):
    svc, s, c = enrolled
    before = svc.repo.load()
    with pytest.raises(ValidationError):
        svc.grade(s.id, c.id, value)
    assert svc.repo.load() == before


def test_weighted_gpa_and_ungraded_ignored(enrolled):
    svc, s, a = enrolled
    b = svc.add_course("Базы данных", 1)
    ungraded = svc.add_course("Без оценки", 60)
    svc.enroll(s.id, b.id)
    svc.enroll(s.id, ungraded.id)
    svc.grade(s.id, a.id, 5)
    svc.grade(s.id, b.id, 3)
    assert svc.gpa(s.id) == 4.5


def test_no_grades(enrolled):
    svc, s, _ = enrolled
    with pytest.raises(ValidationError, match="Нет"):
        svc.gpa(s.id)


def test_empty_list(service):
    s = service.add_student("А")
    assert service.list(s.id) == []
    with pytest.raises(ValidationError):
        service.gpa(s.id)


def test_list_sorted_and_isolated(enrolled):
    svc, s, _ = enrolled
    b = svc.add_course("Базы", 1)
    svc.enroll(s.id, b.id)
    other = svc.add_student("Другой")
    assert [c.title for c, _ in svc.list(s.id)] == ["Архитектура", "Базы"]
    assert svc.list(other.id) == []


def test_drop_keeps_other_students(enrolled):
    svc, s, c = enrolled
    other = svc.add_student("Другой")
    svc.enroll(other.id, c.id)
    svc.drop(s.id, c.id)
    assert svc.list(s.id) == [] and svc.list(other.id) == [(c, None)]
    with pytest.raises(NotFoundError):
        svc.drop(s.id, c.id)


def test_grade_not_enrolled(service):
    s = service.add_student("А")
    c = service.add_course("Б", 1)
    with pytest.raises(NotFoundError, match="не записан"):
        service.grade(s.id, c.id, 5)


@pytest.mark.parametrize("operation", ["enroll", "grade", "drop", "list", "gpa"])
def test_unknown_student(service, operation):
    args = ["missing"]
    if operation in {"enroll", "grade", "drop"}:
        args.append("unknown")
    if operation == "grade":
        args.append(5)
    with pytest.raises(NotFoundError, match="Студент"):
        getattr(service, operation)(*args)


@pytest.mark.parametrize("operation", ["enroll", "grade", "drop"])
def test_unknown_course(service, operation):
    s = service.add_student("А")
    args = [s.id, "unknown"]
    if operation == "grade":
        args.append(5)
    with pytest.raises(NotFoundError, match="Курс"):
        getattr(service, operation)(*args)


def test_io_failure_atomic(enrolled):
    svc, s, c = enrolled
    before = svc.repo.load()
    with patch.object(svc.repo, "save", side_effect=StorageError("disk")):
        with pytest.raises(StorageError):
            svc.grade(s.id, c.id, 5)
    assert svc.repo.load() == before


def test_real_sqlite_rollback(tmp_path):
    repo = SQLiteRepository(tmp_path / "n.db")
    good = State(courses=(Course("1", "Курс", 1),))
    repo.save(good)
    with pytest.raises(StorageError):
        repo.save(replace(good, courses=good.courses * 2))
    assert repo.load() == good


def test_sqlite_foreign_key(tmp_path):
    repo = SQLiteRepository(tmp_path / "n.db")
    repo.save(State())
    with pytest.raises(StorageError):
        repo.save(State(grades=(Grade("missing", "missing", 5),)))
    assert repo.load() == State()


def test_broken_database(tmp_path):
    path = tmp_path / "n.db"
    path.write_bytes(b"not SQLite")
    repo = SQLiteRepository(path)
    with pytest.raises(StorageError):
        repo.load()
    with pytest.raises(StorageError):
        repo.save(State())


def test_cli_full_flow(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATA_PATH", str(tmp_path / "n.db"))
    assert main(["add-student", "Иван"]) == 0
    s = capsys.readouterr().out.strip()
    assert main(["add-course", "Математика", "3"]) == 0
    c = capsys.readouterr().out.strip()
    assert main(["list", s]) == 0 and "Записей пока нет" in capsys.readouterr().out
    assert main(["enroll", s, c]) == 0
    capsys.readouterr()
    assert main(["list", s]) == 0 and "нет оценки" in capsys.readouterr().out
    assert main(["grade", s, c, "5"]) == 0
    capsys.readouterr()
    assert main(["list", s]) == 0 and "5" in capsys.readouterr().out
    assert main(["gpa", s]) == 0 and "5.00" in capsys.readouterr().out
    assert main(["drop", s, c]) == 0
    capsys.readouterr()
    assert main(["gpa", s]) == 2 and "Ошибка" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(["grade", "a", "b", "oops"])


def test_cli_subprocess(tmp_path):
    result = subprocess.run(
        [sys.executable, "main.py", "add-student", "Иван"],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "DATA_PATH": str(tmp_path / "n.db")},
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0 and len(result.stdout.strip()) == 36


def test_csv_export(enrolled, tmp_path):
    import csv

    from src.application.use_cases.export_csv import export_to_csv

    svc, s, c = enrolled
    path = tmp_path / "plan.csv"
    assert export_to_csv(svc, s.id, path) == 1
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ["course_id", "title", "credits", "grade"]
    assert rows[1] == [c.id, c.title, str(c.credits), ""]


def test_cli_export(enrolled, tmp_path, monkeypatch, capsys):
    _, s, _ = enrolled
    monkeypatch.setenv("DATA_PATH", str(tmp_path / "university.sqlite3"))
    path = tmp_path / "out.csv"
    assert main(["export", s.id, str(path)]) == 0
    assert "Экспортировано: 1" in capsys.readouterr().out
