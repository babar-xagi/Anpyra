"""Reusable build orchestration. Application source is parsed, never executed."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .android.dex import DexBuild, build_dex
from .android.manifest import build_manifest
from .android.packaging import build_unsigned_apk as _zip_payload
from .android.signing import load_or_create_signer_material, sign_apk_v2
from .android.verify import ApkReport, inspect_apk
from .compiler.frontend import CompileResult, compile_file
from .config import AppConfig, Project, load_project


@dataclass(frozen=True)
class BuildResult:
    apk_path: Path
    unsigned_apk_path: Path
    manifest_path: Path
    dex_path: Path
    report_path: Path
    compile_result: CompileResult
    dex_build: DexBuild
    verification: ApkReport
    apk_size: int


def build_apk(
    source_path: str | Path,
    out_dir: str | Path,
    *,
    package: str = "dev.anpyra.app",
    label: str = "Anpyra",
    version_code: int = 1,
    version_name: str = "0.1.0",
    min_sdk: int = 24,
    target_sdk: int = 36,
    state_dir: str | Path | None = None,
) -> BuildResult:
    config = AppConfig(package, label, version_code, version_name, min_sdk, target_sdk)
    source_path, out_dir = Path(source_path).resolve(), Path(out_dir).resolve()
    if source_path.is_relative_to(out_dir):
        raise ValueError("output directory cannot contain the source file")
    compiled = compile_file(source_path, package=config.package, label=config.label)
    app = compiled.ir
    manifest = build_manifest(
        app.package,
        app.qualified_activity,
        app.label,
        version_code=config.version_code,
        version_name=config.version_name,
        min_sdk=config.min_sdk,
        target_sdk=config.target_sdk,
    )
    dex_build = build_dex(app)
    unsigned = _zip_payload(manifest, dex_build.data)
    state = Path(state_dir).resolve() if state_dir is not None else source_path.parent / ".anpyra"
    if state == out_dir or state.is_relative_to(out_dir) or out_dir.is_relative_to(state):
        raise ValueError("signing state and output directory must be separate")
    signer = load_or_create_signer_material(state)
    signed = sign_apk_v2(unsigned, material=signer)

    # Verify a staged build before replacing any previous artifacts.
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".anpyra-build-", dir=out_dir.parent) as temporary:
        staging = Path(temporary)
        apk_name = app.package + ".apk"
        staged_apk = staging / apk_name
        staged_apk.write_bytes(signed.apk)
        verification = inspect_apk(staged_apk)
        report = {
            "schema_version": 1,
            "source": str(source_path),
            "output_dir": str(out_dir),
            "config": {
                key: value
                for key, value in asdict(config).items()
                if key not in {"entry", "output_dir"}
            },
            "apk_sha256": hashlib.sha256(signed.apk).hexdigest(),
            "apk_size": len(signed.apk),
            "certificate_sha256": hashlib.sha256(signer.certificate_der).hexdigest(),
            "verification": asdict(verification),
            "methods": [asdict(method) for method in dex_build.methods],
        }
        payloads = {
            "AndroidManifest.xml": manifest,
            "classes.dex": dex_build.data,
            "unsigned.apk": unsigned,
            "build-report.json": (json.dumps(report, indent=2) + "\n").encode("utf-8"),
        }
        for name, data in payloads.items():
            (staging / name).write_bytes(data)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in (*payloads, apk_name):
            (staging / name).replace(out_dir / name)

    return BuildResult(
        out_dir / apk_name,
        out_dir / "unsigned.apk",
        out_dir / "AndroidManifest.xml",
        out_dir / "classes.dex",
        out_dir / "build-report.json",
        compiled,
        dex_build,
        verification,
        len(signed.apk),
    )


def build_project(project: str | Path | Project = ".", *, target: str = "android") -> BuildResult:
    if target != "android":
        raise ValueError("Anpyra supports Android only")
    project = project if isinstance(project, Project) else load_project(project)
    c = project.config
    return build_apk(
        project.source_path,
        project.output_path,
        package=c.package,
        label=c.label,
        version_code=c.version_code,
        version_name=c.version_name,
        min_sdk=c.min_sdk,
        target_sdk=c.target_sdk,
        state_dir=project.state_path,
    )
