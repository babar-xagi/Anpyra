# 🗂️ Repository Structure

The current source tree focuses on Android and uses direct component ownership. Version 0.1.1 includes this layout; immutable 0.1.0 retains its original internal layout.

## 🌳 Maintained tree

```text
Anpyra/
├── README.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE
├── pyproject.toml, MANIFEST.in, .gitignore
├── .github/
│   ├── workflows/tests.yml       # Windows/Linux checks; reusable by release
│   ├── workflows/publish.yml     # Manual tagged TestPyPI/PyPI upload
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── src/
│   ├── README.md
│   ├── anpyra/
│   │   ├── __init__.py, __main__.py, py.typed
│   │   ├── api.py                # Public Android authoring types
│   │   ├── config.py             # Metadata, project and TOML validation
│   │   ├── scaffold.py           # New project source/config/ignore files
│   │   ├── cli.py                # Commands and optional adb dispatch
│   │   ├── build.py              # Compile/package/sign/verify/report pipeline
│   │   ├── compiler/
│   │   │   ├── frontend.py       # Static Python AST → typed IR
│   │   │   └── ir.py             # Application/function/operation records
│   │   └── android/
│   │       ├── README.md, __init__.py
│   │       ├── screen.py         # Native screen/lifecycle method bindings
│   │       ├── codegen.py        # IR → method code, registers and branches
│   │       ├── dalvik.py         # Instruction encoding and assembler
│   │       ├── dex_types.py      # Signature and result/listing records
│   │       ├── encoding.py       # DEX binary/string helpers
│   │       ├── dex.py            # DEX pools, sections and checksums
│   │       ├── manifest.py       # Binary manifest writing
│   │       ├── manifest_inspect.py # Manifest reading
│   │       ├── packaging.py      # Deterministic unsigned APK ZIP
│   │       ├── signing.py        # Debug identity and APK v2 signing
│   │       └── verify.py         # APK/content/DEX integrity inspection
│   └── pyandroid/__init__.py     # Experiment authoring imports
├── examples/hello/, score/       # Complete Android source/config projects
├── tests/
│   ├── unit/                    # Compiler/config/DEX/components/release guards
│   ├── integration/             # CLI/build/identity workflows
│   ├── regression/              # Functions and exact historical DEX output
│   └── fixtures/                # Unchanged source inputs 005–008
├── docs/
│   ├── user_guide/
│   ├── developer_guide/
│   ├── pypi_readme.md
│   ├── progress.md              # Implemented work and success evidence
│   └── roadmap.md               # Android completion phases
└── scripts/check_docs.py, check_release.py
```

## 🧭 Where changes belong

Source syntax/types belong in frontend.py; operation records belong in ir.py. Activity/construction calls belong in screen.py; typography emission belongs in android/textview.py and font validation in android/fonts.py; register/control-flow rules in codegen.py; binary instructions in dalvik.py; container layout in dex.py; ZIP entries in packaging.py. Keep API stubs, source checks, IR and emitters in agreement.

There are no common/platforms/desktop/iOS placeholder packages. Root config owns the current Android project settings. Root build orchestrates actual components; android/dex.py is the only DEX writer.

## 🧹 Local artifacts

| Directory | Meaning | Git policy |
| --- | --- | --- |
| .venv/, build/, dist/ | Python environment, package/temporary outputs | Ignored |
| .cache/, .ruff_cache/ | Tool data and local validation baselines | Ignored |
| .anpyra/, .pyandroid/ | Retained private signing identities | Ignored; preserve for updates |
| .reference/ | Optional historical audit input | Ignored; not required by tests/builds |
| __pycache__/, *.egg-info/ | Python-generated caches/metadata | Ignored |

Do not remove a signing identity as routine cleanup. Build distributions from clean source or a fresh source archive to prevent stale build/lib packages being carried over. Check the wheel inventory after deleting package directories.

Use [source reference](source_reference.md) for functions, [components](android_components.md) for boundaries and [progress](../progress.md) for what is actually complete.
