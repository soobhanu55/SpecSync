"""Turns a real import graph (from parser.py) into a PlantUML component diagram."""


def to_plantuml(graph: dict) -> str:
    modules = graph["modules"]
    edges = graph["edges"]

    packages: dict[str, list[str]] = {}
    for name, package in modules.items():
        packages.setdefault(package, []).append(name)

    lines = ["@startuml", "skinparam componentStyle rectangle", ""]
    for package in sorted(packages):
        lines.append(f'package "{package}" {{')
        for name in sorted(packages[package]):
            lines.append(f'  [{name}]')
        lines.append("}")
        lines.append("")

    for src, dst in edges:
        lines.append(f'[{src}] --> [{dst}]')

    lines.append("@enduml")
    return "\n".join(lines) + "\n"
