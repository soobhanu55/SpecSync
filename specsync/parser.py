"""Extracts a real internal-import graph from a Python codebase via ast.

No hand-maintained diagram, no invented boxes, every edge here is a real
`import` statement found by parsing the actual source files.
"""
import ast
from pathlib import Path


def _module_name(root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(root).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_import(mod_name: str, known_modules: set[str]) -> str | None:
    # Walk up the dotted path until we find a module that actually exists
    # in this codebase, e.g. "vision.detector.helper" -> "vision.detector".
    parts = mod_name.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in known_modules:
            return candidate
        parts = parts[:-1]
    return None


def build_import_graph(root_dir: str) -> dict:
    """Returns {"modules": {name: package}, "edges": [(from, to), ...]}."""
    root = Path(root_dir).resolve()
    py_files = [p for p in root.rglob("*.py") if "__pycache__" not in p.parts and "test" not in p.stem]

    modules: dict[str, str] = {}
    for f in py_files:
        name = _module_name(root, f)
        if not name:
            continue
        package = name.split(".")[0] if "." in name else "(root)"
        modules[name] = package

    known = set(modules.keys())
    edges: set[tuple[str, str]] = set()

    for f in py_files:
        src_name = _module_name(root, f)
        if src_name not in known:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _resolve_import(alias.name, known)
                    if target and target != src_name:
                        edges.add((src_name, target))
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                # "from pkg import submodule" imports a submodule, not a name
                # defined in pkg/__init__.py; check that case before falling
                # back to resolving the bare module path.
                added_submodule = False
                for alias in node.names:
                    submodule_candidate = f"{node.module}.{alias.name}"
                    if submodule_candidate in known and submodule_candidate != src_name:
                        edges.add((src_name, submodule_candidate))
                        added_submodule = True
                if not added_submodule:
                    target = _resolve_import(node.module, known)
                    if target and target != src_name:
                        edges.add((src_name, target))

    return {"modules": modules, "edges": sorted(edges)}
