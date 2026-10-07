# 🚢 Release and Packaging Checklist

Anpyra **0.1.3** was published to PyPI on October 6, 2026 through [the successful workflow](https://github.com/babar-xagi/Anpyra/actions/runs/37539219407). Public wheel/source hashes match checked CI artifacts. Fresh installation and separate pip/uv upgrades from 0.1.2 built/verified starter and Button/state/ripple/icon APKs, retaining existing project configuration, signing identity and starter APK bytes. See [release notes](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.3) and [progress evidence](../progress.md). TestPyPI rehearsal was not run for this release. Android app-store signing/distribution remains a separate future workflow; see [publishing](publishing.md) for setup and commands.

Anpyra **0.1.4** was published on October 6, 2026 through [Trusted Publishing](https://github.com/babar-xagi/Anpyra/actions/runs/37573611590). Public wheel/source hashes match the checked CI files attached to the [GitHub release](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.4). Fresh PyPI installation and separate pip/uv upgrades from 0.1.3 passed, preserving configuration, signing identity and starter APK bytes. Each public-package environment built/verified the new chatbot reproducibly. See [progress](../progress.md) for fingerprints and scope; TestPyPI rehearsal was not run.

The 0.1.5 candidate adds generic callbacks, typed Activity state and explicit saved-instance restore. Publication/index evidence is recorded after upload in [progress](../progress.md).

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
uv build --no-create-gitignore --out-dir dist/pypi/0.1.5
python scripts/check_release.py --tag v0.1.5 --dist dist/pypi/0.1.5
uvx --from twine twine check --strict dist/pypi/0.1.5/*
```

Use an empty output folder and the actual candidate version. uv builds both wheel and source archive. The pip alternative is:

```powershell
python -m pip install build twine
python -m build --outdir dist/pypi/0.1.5
python -m twine check --strict dist/pypi/0.1.5/*
```

`MANIFEST.in` includes guides, examples, tests, maintenance scripts and repository templates in the source distribution. Wheel contents are the installable packages, metadata/license and typing marker, not the complete repository.

Inspect both archives for absent secrets/generated files. Install the wheel in a fresh environment and from outside the checkout; create/build/verify a new app. Unpack the source archive and confirm its documented tests and docs checks have their required files.

## 🏷️ Publish only with evidence

Record commit, tool versions, test/CI results, APK fingerprints and tested devices. List unresolved compatibility limits. Only mark a roadmap phase complete when its exit criteria are met. Do not add a success badge for a test that has not run.

Tagging, uploading wheels and app-store delivery are explicit distribution actions. The publish workflow is manually dispatched from main with an existing vVERSION tag and a selected index. It reuses tests, checks tag/version, validates archives/README, smoke-tests a wheel, then uploads through a separately configured trusted publisher. A normal push/tag does not upload packages.

## 🔄 Post-release maintenance

Keep fixes small and reproduce failures. Backport compatibility fixes deliberately, retain regression fixtures, and document any accepted-language change. If a release fails on a new device/API, update the known result rather than claiming universal Android support.
