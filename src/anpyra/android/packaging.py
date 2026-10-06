"""Deterministic unsigned APK ZIP packaging."""

import hashlib
import io
import re
import zipfile

from .assets import validate_png

ASSET_ENTRY = re.compile(r"assets/anpyra/[0-9a-f]{64}\.png\Z")


def valid_asset_entry(name: str) -> bool:
    return ASSET_ENTRY.fullmatch(name) is not None


def build_unsigned_apk(
    manifest: bytes, dex: bytes, assets: dict[str, bytes] | None = None
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", allowZip64=False) as archive:
        entries = [("AndroidManifest.xml", manifest), ("classes.dex", dex)]
        for name, payload in sorted((assets or {}).items()):
            if not valid_asset_entry(name):
                raise ValueError(f"invalid screen asset entry: {name}")
            if hashlib.sha256(payload).hexdigest() != name.rsplit("/", 1)[1][:-4]:
                raise ValueError("screen asset name must match its PNG digest")
            validate_png(payload)
            entries.append((name, payload))
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()
