"""Узкий порт снимков, независимый от SQL/файлов (DIP/ISP)."""

from abc import ABC, abstractmethod

from src.domain.entities.university import State


class UniversityRepository(ABC):
    @abstractmethod
    def load(self) -> State: ...

    @abstractmethod
    def save(self, state: State) -> None: ...
