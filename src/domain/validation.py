"""Общие проверки входных значений."""

from src.domain.entities.university import ValidationError


def text(value: str, label: str) -> str:
    value = value.strip()
    if not 1 <= len(value) <= 100:
        raise ValidationError(f"{label}: требуется 1–100 символов")
    return value


def integer(value: int, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValidationError(f"{label}: целое число {low}–{high}")
    return value
