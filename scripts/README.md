# 🧰 Repository Maintenance Scripts

## 📚 check_docs.py

Run from any directory using the script's path:

```powershell
python scripts/check_docs.py
```

The script discovers repository-owned Markdown, checks relative file links and emoji title conventions, parses Python snippets, and compiles supported documented Activity examples in memory. It reports failures with file/line information and returns a nonzero status.

It excludes local environments/caches/build outputs/reference inputs. It does not fetch external URLs, validate heading anchors, execute host snippets, install packages, or run device commands. Blocks marked `python unsupported` are syntax-checked but intentionally not compiled as apps.

Activate/install Anpyra before running it. Compiler availability is checked so supported examples cannot silently skip compilation. CI runs it alongside lint and tests. See the [testing guide](../docs/developer_guide/testing.md).

## 📦 check_release.py

```powershell
python scripts/check_release.py --tag v0.1.0
python scripts/check_release.py --tag v0.1.0 --dist dist/pypi/0.1.0
```

`check_version` reads pyproject.toml and parses the package __version__ assignment without importing framework code. The optional tag must equal vVERSION. `check_distributions` requires one wheel and one source archive, checks name/version metadata and required package/release files, and rejects duplicate/unsafe paths, tar links, common key/signing state and generated artifacts.

This read-only guard does not build, extract, upload, change versions or access credentials. `main` returns 1 with a diagnostic on failure. See [publishing](../docs/developer_guide/publishing.md) for build/upload commands and account configuration.
