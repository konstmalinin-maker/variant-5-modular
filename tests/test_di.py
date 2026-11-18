"""C: подмена через контейнер, без файлов и SQL."""

from unittest.mock import create_autospec

import pytest

from src.application.services.university_service import UniversityService
from src.domain.entities.university import State, ValidationError
from src.domain.repositories.university_repository import UniversityRepository
from src.infrastructure.bootstrap import build_container
from src.infrastructure.di.container import Container


def test_repository_override(tmp_path):
    container = build_container(tmp_path / "n.db")
    original = container.resolve(UniversityRepository)
    mock = create_autospec(UniversityRepository, instance=True)
    mock.load.return_value = State()
    with container.override(UniversityRepository, lambda c: mock):
        service = container.resolve(UniversityService)
        student = service.add_student("А")
        mock.save.assert_called_once_with(State(students=(student,)))
    assert type(container.resolve(UniversityRepository)) is type(original)
    assert not list(tmp_path.iterdir())


def test_invalid_before_io(tmp_path):
    c = build_container(tmp_path / "n.db")
    mock = create_autospec(UniversityRepository, instance=True)
    with c.override(UniversityRepository, lambda c: mock):
        with pytest.raises(ValidationError):
            c.resolve(UniversityService).add_student("")
    mock.load.assert_not_called()


def test_missing_and_cycle():
    c = Container()
    with pytest.raises(LookupError):
        c.resolve("missing")
    c.register("a", lambda c: c.resolve("b"))
    c.register("b", lambda c: c.resolve("a"))
    with pytest.raises(RuntimeError):
        c.resolve("a")
    assert c.resolving == set()


def test_scoped_override_removed_after_error():
    c = Container()
    with pytest.raises(ValueError):
        with c.override("a", lambda c: 1):
            assert c.resolve("a") == 1
            raise ValueError("test")
    with pytest.raises(LookupError):
        c.resolve("a")
