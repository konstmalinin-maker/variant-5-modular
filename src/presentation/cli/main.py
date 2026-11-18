"""CLI: вариант 5 — университет."""

import argparse
import os
import sys

from src.domain.entities.university import DomainError
from src.infrastructure.bootstrap import build_service


def main(argv=None):
    parser = argparse.ArgumentParser(description="Университет: GPA по кредитам, шкала 2–5")
    commands = parser.add_subparsers(dest="command", required=True)
    student = commands.add_parser("add-student")
    student.add_argument("name")
    course = commands.add_parser("add-course")
    course.add_argument("title")
    course.add_argument("credits", type=int)
    for name in ("enroll", "list", "grade", "gpa", "drop"):
        sub = commands.add_parser(name)
        sub.add_argument("student_id")
        if name in ("enroll", "grade", "drop"):
            sub.add_argument("course_id")
        if name == "grade":
            sub.add_argument("value", type=int)
    args = parser.parse_args(argv)
    try:
        service = build_service(os.environ.get("DATA_PATH", "university.sqlite3"))
        if args.command == "add-student":
            print(service.add_student(args.name).id)
        elif args.command == "add-course":
            print(service.add_course(args.title, args.credits).id)
        elif args.command == "list":
            rows = service.list(args.student_id)
            print(
                "\n".join(
                    f"{c.id} | {c.title} | {c.credits} | {v if v is not None else 'нет оценки'}"
                    for c, v in rows
                )
                or "Записей пока нет"
            )
        elif args.command == "gpa":
            print(f"GPA (2–5): {service.gpa(args.student_id):.2f}")
        else:
            params = [args.student_id, args.course_id]
            if args.command == "grade":
                params.append(args.value)
            getattr(service, args.command)(*params)
            print("Выполнено")
        return 0
    except DomainError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
