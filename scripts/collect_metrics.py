import ast
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from radon.complexity import cc_visit

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
output = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "metrics.json"
files = [p for p in root.rglob("*.py") if not any(x in p.parts for x in ("__pycache__", ".venv", ".git"))]
prod = [
    p for p in files if "tests" not in p.parts and not p.name.startswith("test_") and "scripts" not in p.parts
]
mods = {str(p.relative_to(root).with_suffix("")).replace("/", ".") for p in prod}
blocks = []
edges = []
for p in prod:
    code = p.read_text()
    blocks += cc_visit(code)
    source = str(p.relative_to(root).with_suffix("")).replace("/", ".")
    for node in ast.walk(ast.parse(code)):
        refs = (
            [node.module]
            if isinstance(node, ast.ImportFrom)
            else [a.name for a in node.names]
            if isinstance(node, ast.Import)
            else []
        )
        for ref in refs:
            if ref in mods:
                edges.append((source, ref))
cov = json.loads((root / "coverage.json").read_text())
cases = ET.parse(root / "junit.xml").findall(".//testcase")
suites = ET.parse(root / "junit.xml").findall(".//testsuite")
data = {
    "py_files": len(files),
    "production_py": len(prod),
    "application_folders": len({str(p.parent.relative_to(root)) for p in prod if p.parent != root}),
    "loc_all": sum(len(p.read_text().splitlines()) for p in files),
    "loc_production": sum(len(p.read_text().splitlines()) for p in prod),
    "max_file_loc": max(len(p.read_text().splitlines()) for p in files),
    "internal_imports": len(edges),
    "cc_average": round(sum(b.complexity for b in blocks) / len(blocks), 3),
    "cc_blocks": len(blocks),
    "coverage": cov["totals"]["percent_covered"],
    "tests": len(cases),
    "test_seconds": sum(float(s.get("time", "0")) for s in suites),
    "edges": edges,
}
output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in data.items() if k != "edges"}, ensure_ascii=False))
