# 🚢 Release and Packaging Checklist

Anpyra v0.1 is an alpha baseline. A local wheel is available; PyPI publication, signed release workflows and store publishing are separate future work.

## 📋 Prepare a candidate

- [ ] Choose a version deliberately; update `pyproject.toml` and `src/anpyra/__init__.py` together.
- [ ] Update changelog with user-visible behavior and limitations.
- [ ] Update commands/examples/reference tables when behavior changed.
- [ ] Review license and packaged file lists.
- [ ] Keep debug identities, caches and generated APKs out of source changes.
- [ ] Check actual CI matrix results and unresolved bugs.

## 🧪 Validate the checkout

```powershell
python -m unittest discover -s tests -v
ruff check src tests examples scripts
ruff format --check src tests examples scripts
python scripts/check_docs.py
anpyra build examples/hello
anpyra build examples/score
anpyra verify examples/score/build/dev.anpyra.score.apk
```

Complete the [manual device checklist](testing.md) before claiming device acceptance for that candidate. Host verification and original experiment results do not substitute for this refactored build's runtime result.

## 📦 Build distributions

```powershell
python -m pip wheel --no-deps . --wheel-dir dist
```

For a source archive, use the configured setuptools backend through a standard build frontend when available:

```powershell
python -m pip install build
python -m build --sdist
```

`MANIFEST.in` includes guides, examples, tests, maintenance scripts and repository templates in the source distribution. Wheel contents are the installable packages, metadata/license and typing marker, not the complete repository.

Inspect both archives for absent secrets/generated files. Install the wheel in a fresh environment and from outside the checkout; create/build/verify a new app. Unpack the source archive and confirm its documented tests and docs checks have their required files.

## 🏷️ Publish only with evidence

Record commit, tool versions, test/CI results, APK fingerprints and tested devices. List unresolved compatibility limits. Only mark a roadmap phase complete when its exit criteria are met. Do not add a success badge for a test that has not run.

Tagging, uploading wheels, publishing to PyPI, and app-store delivery are explicit distribution actions, not side effects of this local checklist. Plan those workflows in the release/distribution roadmap phase.

## 🔄 Post-release maintenance

Keep fixes small and reproduce failures. Backport compatibility fixes deliberately, retain regression fixtures, and document any accepted-language change. If a release fails on a new device/API, update the known result rather than claiming universal Android support.
