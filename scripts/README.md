# 🧰 Repository Maintenance Scripts

## 📚 check_docs.py

Run from any directory using the script's path:

```powershell
python scripts/check_docs.py
```

The script discovers repository-owned Markdown, checks relative file links and emoji title conventions, parses Python snippets, and compiles supported documented Activity examples in memory. It reports failures with file/line information and returns a nonzero status.

It excludes local environments/caches/build outputs/reference inputs. It does not fetch external URLs, validate heading anchors, execute host snippets, install packages, or run device commands. Blocks marked `python unsupported` are syntax-checked but intentionally not compiled as apps.

Activate/install Anpyra before running it. Compiler availability is checked so supported examples cannot silently skip compilation. CI runs it alongside lint and tests. See the [testing guide](../docs/developer_guide/testing.md).
