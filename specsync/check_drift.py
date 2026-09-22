"""Regenerates the architecture diagram from the current code and compares
it against the committed architecture.puml. Exit code 1 means the diagram
is stale, drift.py doesn't guess at intent, only detects a real mismatch.
"""
import argparse
import difflib
import sys
from pathlib import Path

from specsync.parser import build_import_graph
from specsync.diagram import to_plantuml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target_dir", help="root of the Python codebase to scan")
    ap.add_argument("--spec", default="architecture.puml", help="committed diagram to check against")
    ap.add_argument("--write", action="store_true", help="write the regenerated diagram instead of checking")
    args = ap.parse_args()

    graph = build_import_graph(args.target_dir)
    fresh = to_plantuml(graph)
    spec_path = Path(args.spec)

    if args.write:
        spec_path.write_text(fresh, encoding="utf-8")
        print(f"Wrote {spec_path} ({len(graph['edges'])} edges, {len(graph['modules'])} modules)")
        return 0

    if not spec_path.exists():
        print(f"No committed spec at {spec_path}. Run with --write first.")
        return 1

    committed = spec_path.read_text(encoding="utf-8")
    if committed == fresh:
        print("Architecture diagram matches the code. No drift.")
        return 0

    print("DRIFT DETECTED: architecture.puml no longer matches the code.\n")
    diff = difflib.unified_diff(
        committed.splitlines(keepends=True),
        fresh.splitlines(keepends=True),
        fromfile="committed architecture.puml",
        tofile="regenerated from code",
    )
    sys.stdout.writelines(diff)
    return 1


if __name__ == "__main__":
    sys.exit(main())
