"""A: нарушения ловятся на реальном AST временной копии."""

from pathlib import Path

import pytest

from scripts.check_layers import check


@pytest.mark.parametrize(
    "code",
    [
        "import sqlite3 as db",
        "from src.infrastructure.persistence import sqlite_repository",
        "from ...infrastructure import bootstrap",
        "from src import presentation",
        '__import__("sqlite3")',
        "from argparse import ArgumentParser",
    ],
)
def test_domain_violations(tmp_path, code):
    f = tmp_path / "src/domain/entities/bad.py"
    f.parent.mkdir(parents=True)
    f.write_text(code)
    assert check(tmp_path)


def test_application_cannot_import_adapter(tmp_path):
    f = tmp_path / "src/application/bad.py"
    f.parent.mkdir(parents=True)
    f.write_text("from src.infrastructure import bootstrap")
    assert check(tmp_path)


def test_valid_and_flat(tmp_path):
    assert check(tmp_path) == []
    f = tmp_path / "src/application/good.py"
    f.parent.mkdir(parents=True)
    f.write_text("from src.domain.repositories.university_repository import UniversityRepository")
    assert check(tmp_path) == []


def test_current_architecture():
    assert check(Path(__file__).resolve().parents[1]) == []
