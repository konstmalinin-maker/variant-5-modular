"""A: AST-проверка прямых, относительных и динамических импортов слоёв."""

import argparse
import ast
from pathlib import Path

LOW_LEVEL = {
    "sqlite3",
    "sqlalchemy",
    "psycopg",
    "argparse",
    "click",
    "tkinter",
    "os",
    "sys",
    "database",
    "handlers",
    "main",
    "json_repository",
}


def check(root: Path) -> list[str]:
    problems = []
    source = root / "src"
    if not source.exists():
        # Flat не имеет слоёв; не выдаём отсутствие проверки за доказательство DIP.
        return []
    for path in source.rglob("*.py"):
        relative = path.relative_to(root)
        parts = relative.parts
        if len(parts) < 3 or parts[1] not in {"domain", "application"}:
            continue
        layer = parts[1]
        tree = ast.parse(path.read_text(encoding="utf8"))
        for node in ast.walk(tree):
            imports = []
            if isinstance(node, ast.Import):
                imports = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    prefix = list(parts[:-1])
                    for _ in range(node.level - 1):
                        prefix.pop()
                    module = ".".join([*prefix, module]).strip(".")
                imports = [module]
                if module in {"src", "src.infrastructure", "src.presentation"}:
                    imports += [f"{module}.{a.name}" for a in node.names]
            for name in imports:
                target = name.split(".")
                bad = target[0] in LOW_LEVEL
                if len(target) > 1 and target[0] == "src":
                    allowed = {"domain"} if layer == "domain" else {"domain", "application"}
                    bad = bad or target[1] not in allowed
                if bad:
                    problems.append(f"{relative}:{node.lineno}: {layer} -> {name} запрещено")
            if isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name)
                and node.func.id in {"__import__", "eval", "exec"}
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            ):
                problems.append(
                    f"{relative}:{node.lineno}: динамический импорт/исполнение запрещено в {layer}"
                )
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root
    errors = check(root)
    print(
        "\n".join(errors)
        if errors
        else (
            "OK: domain/application соблюдают границы"
            if (root / "src").exists()
            else "OK: Flat; границы слоёв отсутствуют, DIP не заявляется"
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
