"""Точка сборки зависимостей вне бизнес-слоя."""

import os

from src.application.services.university_service import UniversityService
from src.domain.entities.university import ValidationError
from src.infrastructure.persistence.json_repository import JSONRepository
from src.infrastructure.persistence.sqlite_repository import SQLiteRepository


def build_service(path):
    backend = os.environ.get("STORAGE", "sqlite")
    if backend not in {"sqlite", "json"}:
        raise ValidationError("STORAGE должен быть sqlite или json")
    return UniversityService((SQLiteRepository if backend == "sqlite" else JSONRepository)(path))
