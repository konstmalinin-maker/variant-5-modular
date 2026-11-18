"""Composition root; выбор адаптера не затрагивает application/domain."""

import os

from src.application.services.university_service import UniversityService
from src.domain.entities.university import ValidationError
from src.domain.repositories.university_repository import UniversityRepository
from src.infrastructure.di.container import Container
from src.infrastructure.persistence.json_repository import JSONRepository
from src.infrastructure.persistence.sqlite_repository import SQLiteRepository


def build_container(path) -> Container:
    backend = os.environ.get("STORAGE", "sqlite")
    if backend not in {"sqlite", "json"}:
        raise ValidationError("STORAGE должен быть sqlite или json")
    container = Container()
    cls = SQLiteRepository if backend == "sqlite" else JSONRepository
    container.register(UniversityRepository, lambda c: cls(path))
    container.register(UniversityService, lambda c: UniversityService(c.resolve(UniversityRepository)))
    return container


def build_service(path) -> UniversityService:
    return build_container(path).resolve(UniversityService)
