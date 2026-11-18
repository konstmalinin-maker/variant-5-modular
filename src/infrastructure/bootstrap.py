"""Точка сборки зависимостей вне бизнес-слоя."""

from src.application.services.university_service import UniversityService
from src.infrastructure.persistence.sqlite_repository import SQLiteRepository


def build_service(path):
    return UniversityService(SQLiteRepository(path))
