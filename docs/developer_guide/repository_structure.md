# 🗂️ Repository Structure

The repository separates the installable framework, user examples, automated checks, documentation and local generated files.

## 🌳 Maintained tree

```text
Anpyra/
├── README.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE
├── pyproject.toml, MANIFEST.in, .gitignore
├── .github/                   # Tests/publish workflows, issue and PR templates
├── src/
│   ├── README.md
│   ├── anpyra/
│   │   ├── __init__.py, __main__.py, py.typed
│   │   ├── api.py, config.py   # Public Android-compatible imports
│   │   ├── cli.py, scaffold.py
│   │   ├── build.py           # Public build API and target dispatch
│   │   ├── common/
│   │   │   ├── config.py      # Shared identity/version validation
│   │   │   ├── project.py     # Shared project path rules
│   │   │   └── compiler/
│   │   │       ├── frontend.py  # Python AST analysis/lowering
│   │   │       └── ir.py        # Operation/function/app records
│   │   ├── platforms/
│   │   │   ├── registry.py    # Available/planned native targets
│   │   │   ├── mobile/
│   │   │   │   ├── android/   # Working backend
│   │   │   │   │   ├── api.py, config.py, backend.py
│   │   │   │   │   ├── build.py, dex.py
│   │   │   │   │   ├── manifest.py, manifest_inspect.py
│   │   │   │   │   └── signing.py, verify.py
│   │   │   │   └── ios/       # Future backend; not implemented
│   │   │   └── desktop/
│   │   │       ├── windows/   # Future backend; not implemented
│   │   │       ├── macos/     # Future backend; not implemented
│   │   │       └── linux/     # Future backend; not implemented
│   │   ├── compiler/         # Historical import forwarding only
│   │   └── android/          # Historical import forwarding only
│   └── pyandroid/__init__.py  # Legacy authoring imports
├── examples/                 # Complete hello and score projects
├── tests/
│   ├── unit/                 # Source/config/DEX/native-boundary checks
│   ├── integration/          # CLI/build/signing workflows
│   ├── regression/           # Experiment 008 contract
│   └── fixtures/             # Historical source inputs
├── docs/
│   ├── user_guide/
│   ├── developer_guide/
│   └── roadmap.md
└── scripts/                  # check_docs.py and read-only check_release.py
```

## 📦 What belongs where?

| Work | Location |
| --- | --- |
| New source language rule | `src/anpyra/common/compiler/frontend.py`, IR/backend if needed |
| Dalvik opcode or DEX fix | `src/anpyra/platforms/mobile/android/dex.py` |
| Android XML/package/signature change | `src/anpyra/platforms/mobile/android/` |
| Shared project paths/metadata | `src/anpyra/common/project.py`, `common/config.py` |
| Native target selection | `src/anpyra/platforms/registry.py` |
| Future iOS/desktop implementation | Respective target directory under `platforms/` |
| Public API/CLI/config change | Relevant top-level `src/anpyra/` file |
| Small isolated contract test | `tests/unit/` |
| Cross-module output/workflow test | `tests/integration/` |
| Historical compatibility contract | `tests/regression/` and immutable fixtures |
| Runnable application | Separate folder under `examples/` |
| User task/concept | `docs/user_guide/` |
| Maintenance explanation/file map | `docs/developer_guide/` |
| Future feature proposal | `docs/roadmap.md` and issue discussion |

Android is the only implemented target. Planned packages contain a marker and README, not a compiler. Web is outside target scope. Package markers and target ownership READMEs supplement the tree above. Read [native platform architecture](native_platforms.md) before adding a backend.

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
