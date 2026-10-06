# 🚢 Release and Packaging Checklist

Anpyra v0.1 is an alpha baseline. The manual TestPyPI/PyPI workflow is prepared; its account configuration and first index upload remain pending. Follow [publishing](publishing.md) for one-time setup, tag/run commands and installation verification. Android release identity and app-store delivery remain separate future work.

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
uv build --no-create-gitignore --out-dir dist/pypi/0.1.0
python scripts/check_release.py --tag v0.1.0 --dist dist/pypi/0.1.0
uvx --from twine twine check --strict dist/pypi/0.1.0/*
```

Use an empty output folder and the actual candidate version. uv builds both wheel and source archive. The pip alternative is:

```powershell
python -m pip install build twine
python -m build --outdir dist/pypi/0.1.0
python -m twine check --strict dist/pypi/0.1.0/*
```

`MANIFEST.in` includes guides, examples, tests, maintenance scripts and repository templates in the source distribution. Wheel contents are the installable packages, metadata/license and typing marker, not the complete repository.

Inspect both archives for absent secrets/generated files. Install the wheel in a fresh environment and from outside the checkout; create/build/verify a new app. Unpack the source archive and confirm its documented tests and docs checks have their required files.

## 🏷️ Publish only with evidence

Record commit, tool versions, test/CI results, APK fingerprints and tested devices. List unresolved compatibility limits. Only mark a roadmap phase complete when its exit criteria are met. Do not add a success badge for a test that has not run.

Tagging, uploading wheels and app-store delivery are explicit distribution actions. The publish workflow is manually dispatched from main with an existing vVERSION tag and a selected index. It reuses tests, checks tag/version, validates archives/README, smoke-tests a wheel, then uploads through a separately configured trusted publisher. A normal push/tag does not upload packages.

## 🔄 Post-release maintenance

Keep fixes small and reproduce failures. Backport compatibility fixes deliberately, retain regression fixtures, and document any accepted-language change. If a release fails on a new device/API, update the known result rather than claiming universal Android support.
