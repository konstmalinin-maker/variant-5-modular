"""Экспорт — отдельный сценарий; CSV не меняет правила GPA."""

import csv

from src.application.services.university_service import UniversityService


def export_to_csv(service: UniversityService, student_id: str, path) -> int:
    with open(path, "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["course_id", "title", "credits", "grade"])
        rows = service.list(student_id)
        writer.writerows((c.id, c.title, c.credits, "" if value is None else value) for c, value in rows)
    return len(rows)
