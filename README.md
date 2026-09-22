# SpecSync — architecture-as-code, kept honest by construction

A diagram of a codebase's structure goes stale the moment someone adds a
new import and forgets to update it. SpecSync doesn't ask anyone to keep it
updated, it regenerates the diagram from the actual code and fails CI if
the committed one no longer matches.

## How it works

```
Python source (ast) → real import graph → PlantUML diagram → SVG
                                    ↓
                    committed architecture.puml
                                    ↓
                  CI regenerates and diffs on every push
```

1. **`specsync/parser.py`** walks a codebase and extracts a real internal
   import graph with Python's `ast` module, every edge is a genuine
   `import` statement found in the source, nothing hand-drawn or guessed.
2. **`specsync/diagram.py`** turns that graph into a PlantUML component
   diagram, grouped by top-level package.
3. **`specsync/render.py`** renders it to SVG via the public PlantUML
   server, free, no account. For private/proprietary code, point it at a
   local PlantUML instance instead (see Limitations).
4. **`specsync/check_drift.py`** regenerates the diagram and diffs it
   against the committed `architecture.puml`. Exit code 1 on mismatch.
5. **`.github/workflows/drift-check.yml`** runs step 4 on every push,
   free GitHub Actions minutes on a public repo.
6. **`specsync/changelog.py`** (optional) sends the diff to Groq's free
   tier and appends a 2-3 sentence plain-English summary to
   `CHANGELOG.md` when drift is found.

## Worked example, run against a real codebase

`examples/inspectai_backend` is a snapshot of
[InspectAI](https://github.com/soobhanu55/InspectAI)'s backend. Running
SpecSync against it produces
[`examples/inspectai_backend_architecture.puml`](examples/inspectai_backend_architecture.puml)
and its rendered
[`examples/inspectai_backend_architecture.svg`](examples/inspectai_backend_architecture.svg):
**33 real import edges across 22 modules**, extracted directly from the
code, not written by hand.

### Proof the drift check actually catches something

Tested by adding a real new import (`from mlops import metrics`) to
`vision/detector.py` and rerunning the check:

```
DRIFT DETECTED: architecture.puml no longer matches the code.

--- committed architecture.puml
+++ regenerated from code
@@ -77,4 +77,5 @@
 [vision.detector] --> [config]
+[vision.detector] --> [mlops.metrics]
 @enduml
```

This test also caught a real bug in the first version of the parser:
`from package import submodule` was being resolved against the bare
package name instead of the submodule, so this exact kind of import was
silently missed. Fixed in `parser.py` and covered by a regression test in
`tests/test_parser.py::test_from_package_import_submodule_resolves_correctly`,
not just fixed and forgotten.

## Run it

```bash
pip install -e .
python -m specsync.check_drift path/to/your/codebase --write   # generate architecture.puml
python -m specsync.check_drift path/to/your/codebase            # check for drift, exit 1 if stale
```

## Limitations, stated honestly

- **Python only**, via `ast`. No Java, TypeScript, or C++ support yet, the
  approach generalizes (parse imports/includes, diff against a spec) but
  the parser itself is Python-specific.
- **Import-level granularity only.** This shows which modules depend on
  which, not sequence flows, data models, or requirements traceability, a
  real subset of "everything as code," not the whole thing.
- **Public PlantUML server by default.** Fine for public repos like this
  one's own example. For proprietary code, run a local PlantUML server
  (`docker run -d -p 8080:8080 plantuml/plantuml-server`) and pass its URL
  to `render_svg(text, server=...)` instead, don't send private code
  structure to a third-party server.
- **Dynamic imports aren't caught.** `importlib.import_module(name)` with
  a runtime-computed `name` is invisible to static `ast` analysis, same
  limitation any static tool has.

## Cost: €0.00

Local `ast` parsing, public PlantUML server, GitHub Actions free minutes
on a public repo, Groq's free tier for the optional changelog step.
