"""Атомарный JSON-адаптер снимка университета."""

import json
import os
import tempfile
from pathlib import Path

from src.domain.entities.university import State, StorageError
from src.domain.repositories.university_repository import UniversityRepository


class JSONRepository(UniversityRepository):
    def __init__(self, path):
        self.path = Path(path)

    def load(self) -> State:
        try:
            if not self.path.exists():
                return State()
            return State.from_dict(json.loads(self.path.read_text(encoding="utf8")))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise StorageError(f"Ошибка чтения JSON: {exc}") from exc

    def save(self, state: State) -> None:
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf8") as stream:
                json.dump(state.to_dict(), stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except (OSError, ValueError, TypeError) as exc:
            raise StorageError(f"Ошибка записи JSON: {exc}") from exc
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
