# 🧩 Common Framework Code

Reusable source and project rules live here. Dependencies flow from platform backends toward common code.

| File | Responsibility |
| --- | --- |
| `config.py` | Application ID, label and version validation; shared `ConfigError` |
| `project.py` | Project settings protocol and source/output/state path validation |
| `compiler/frontend.py` | Static Python AST validation, types and lowering |
| `compiler/ir.py` | Immutable operation, function and application records |
| Package `__init__.py` files | Package markers; no target registration |

Common code must not import platform implementations or public Android facades. SDK values, DEX, binary XML, APK packaging and signing belong to Android's backend.

The current front end and IR still describe Activity/TextView apps and carry Android lifecycle/descriptor/register assumptions. Future native backends require deliberate generalization; these folders do not imply cross-platform source compatibility today.

Read the [native architecture guide](../../../docs/developer_guide/native_platforms.md) and [source reference](../../../docs/developer_guide/source_reference.md).
