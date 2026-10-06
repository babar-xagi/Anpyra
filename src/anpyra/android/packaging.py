"""Deterministic unsigned APK ZIP packaging."""

import io
import zipfile


def build_unsigned_apk(manifest: bytes, dex: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", allowZip64=False) as archive:
        for name, data in (("AndroidManifest.xml", manifest), ("classes.dex", dex)):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()
