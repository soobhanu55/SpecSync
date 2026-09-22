import os
import tempfile

from specsync.parser import build_import_graph
from specsync.diagram import to_plantuml


def _write(root, rel_path, content):
    path = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_detects_real_import_edge():
    with tempfile.TemporaryDirectory() as root:
        _write(root, "pkg/a.py", "from pkg import b\n")
        _write(root, "pkg/b.py", "x = 1\n")
        graph = build_import_graph(root)
        assert ("pkg.a", "pkg.b") in graph["edges"]


def test_ignores_external_imports():
    with tempfile.TemporaryDirectory() as root:
        _write(root, "pkg/a.py", "import os\nimport requests\n")
        graph = build_import_graph(root)
        assert graph["edges"] == []


def test_from_package_import_submodule_resolves_correctly():
    # regression test: "from pkg import sub" imports pkg.sub, not a name
    # defined in pkg/__init__.py, this used to be silently missed
    with tempfile.TemporaryDirectory() as root:
        _write(root, "mlops/__init__.py", "")
        _write(root, "mlops/metrics.py", "x = 1\n")
        _write(root, "vision/detector.py", "from mlops import metrics\n")
        graph = build_import_graph(root)
        assert ("vision.detector", "mlops.metrics") in graph["edges"]


def test_diagram_output_is_deterministic():
    with tempfile.TemporaryDirectory() as root:
        _write(root, "pkg/a.py", "from pkg import b\n")
        _write(root, "pkg/b.py", "x = 1\n")
        graph = build_import_graph(root)
        first = to_plantuml(graph)
        second = to_plantuml(build_import_graph(root))
        assert first == second
