# 🗂️ Repository Structure

The repository separates the installable framework, user examples, automated checks, documentation and local generated files.

## 🌳 Maintained tree

```text
Anpyra/
├── README.md                  # Project landing page and quick start
├── CONTRIBUTING.md            # Contribution process
├── CHANGELOG.md               # Baseline and unreleased changes
├── LICENSE                    # Existing Apache-2.0 license
├── MANIFEST.in                # Include guides/examples/tests in source distributions
├── pyproject.toml             # Package, dependency, CLI and Ruff configuration
├── .gitignore                 # Generated files and private local identities
├── .github/
│   ├── workflows/tests.yml    # CI matrix and package checks
│   ├── ISSUE_TEMPLATE/        # Bug and feature report templates
│   └── pull_request_template.md
├── src/
│   ├── README.md              # Source navigation
│   ├── anpyra/
│   │   ├── __init__.py        # Public exports and package version
│   │   ├── __main__.py        # python -m anpyra entry
│   │   ├── api.py             # Activity/TextView authoring types
│   │   ├── config.py          # App metadata and project paths
│   │   ├── scaffold.py        # New app source/configuration
│   │   ├── cli.py             # CLI parser and command behavior
│   │   ├── build.py           # Build orchestration and outputs
│   │   ├── py.typed           # Typing-package marker
│   │   ├── compiler/
│   │   │   ├── __init__.py
│   │   │   ├── frontend.py    # Python AST → checked IR
│   │   │   ├── ir.py          # Immutable operation/application records
│   │   │   └── dex.py         # Assembly and DEX writer
│   │   └── android/
│   │       ├── __init__.py
│   │       ├── manifest.py    # Binary XML writer
│   │       ├── manifest_inspect.py
│   │       ├── signing.py     # Debug identity and v2 APK signing
│   │       └── verify.py      # APK/DEX integrity verification
│   └── pyandroid/__init__.py  # Legacy authoring type exports
├── examples/
│   ├── README.md
│   ├── hello/                 # app.py, anpyra.toml, README.md
│   └── score/                 # app.py, anpyra.toml, README.md
├── tests/
│   ├── README.md
│   ├── __init__.py
│   ├── unit/                  # Compiler/config/DEX behavior
│   ├── integration/           # CLI/build/signing workflows
│   ├── regression/            # Experiment 008 contract
│   └── fixtures/              # Original experiment 005–008 source
├── docs/
│   ├── README.md
│   ├── architecture.md        # Compatibility pointer to developer architecture
│   ├── roadmap.md
│   ├── user_guide/            # End-user tasks and concepts
│   └── developer_guide/       # Maintenance and internals
└── scripts/
    ├── README.md
    └── check_docs.py          # Local docs links, emoji headings and Python snippets
```

## 📦 What belongs where?

| Work | Location |
| --- | --- |
| New source language rule | `src/anpyra/compiler/frontend.py`, IR/backend if needed |
| Dalvik opcode or DEX fix | `src/anpyra/compiler/dex.py` |
| Android XML/package/signature change | `src/anpyra/android/` and build orchestration |
| Public API/CLI/config change | Relevant top-level `src/anpyra/` file |
| Small isolated contract test | `tests/unit/` |
| Cross-module output/workflow test | `tests/integration/` |
| Historical compatibility contract | `tests/regression/` and immutable fixtures |
| Runnable application | Separate folder under `examples/` |
| User task/concept | `docs/user_guide/` |
| Maintenance explanation/file map | `docs/developer_guide/` |
| Future feature proposal | `docs/roadmap.md` and issue discussion |

Keep generated app state out of `src/`. Keep host scripts separate from the restricted app source. Avoid large file moves solely to change appearance; module boundaries should follow actual responsibilities.

## 🧹 Generated and private local directories

| Directory | Meaning | Git policy |
| --- | --- | --- |
| `.venv/` | Local Python environment | Ignored |
| `.cache/`, `.ruff_cache/` | Tool caches | Ignored |
| `build/`, nested app `build/` | Package/generated APK artifacts | Ignored |
| `dist/` | Wheels/source distributions | Ignored |
| `*.egg-info/`, `__pycache__/` | Python metadata/cache | Ignored |
| `.anpyra/`, `.pyandroid/` | Local signing material | Ignored |
| `.reference/` | Optional local experiment-source audit inputs | Ignored; not required by builds/tests |

These directories may exist on a maintainer's machine and do not appear in a clean checkout. Do not delete retained signing identities as part of routine cleanup. The wheel ships framework code and license; the source distribution also carries project guides, examples and tests through `MANIFEST.in`.

The [source reference](source_reference.md) explains every framework file in more detail.
