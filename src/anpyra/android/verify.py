# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

import hashlib
import struct
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .manifest_inspect import inspect_manifest
from .signing import (
    APK_SIG_BLOCK_MAGIC,
    APK_SIGNATURE_SCHEME_V2_ID,
    SIG_ALG_RSA_PKCS1_V1_5_WITH_SHA256,
    compute_chunked_content_digest,
    find_eocd,
    patch_eocd_central_directory_offset,
)


class ApkV2VerifyError(ValueError):
    pass


@dataclass(frozen=True)
class ApkReport:
    entries: tuple[str, ...]
    package: str
    activity: str
    label: str
    min_sdk: int
    target_sdk: int
    exported: bool
    dex_magic_ok: bool
    dex_sha1_ok: bool
    dex_checksum_ok: bool
    v2_block_found: bool
    v2_signature_ok: bool
    v2_content_digest_ok: bool
    certificate_subject: str
    signing_block_size: int
    central_directory_offset: int


def _u32(data: bytes, off: int) -> int:
    if off + 4 > len(data):
        raise ApkV2VerifyError("u32 out of bounds")
    return struct.unpack_from("<I", data, off)[0]


def _u64(data: bytes, off: int) -> int:
    if off + 8 > len(data):
        raise ApkV2VerifyError("u64 out of bounds")
    return struct.unpack_from("<Q", data, off)[0]


def _take_lp32(data: bytes, off: int) -> tuple[bytes, int]:
    n = _u32(data, off)
    start = off + 4
    end = start + n
    if end > len(data):
        raise ApkV2VerifyError("length-prefixed field out of bounds")
    return data[start:end], end


def _iter_lp32_sequence(data: bytes):
    p = 0
    while p < len(data):
        item, p = _take_lp32(data, p)
        yield item
    if p != len(data):
        raise ApkV2VerifyError("bad length-prefixed sequence")


def _locate_signing_block(apk: bytes):
    eocd_off = find_eocd(apk)
    eocd = apk[eocd_off:]
    cd_size = _u32(eocd, 12)
    cd_off = _u32(eocd, 16)

    if cd_off + cd_size != eocd_off:
        raise ApkV2VerifyError("Central Directory/EOCD relationship invalid")

    footer_off = cd_off - 24
    if footer_off < 8:
        raise ApkV2VerifyError("APK Signing Block footer not found")

    trailing_size = _u64(apk, footer_off)
    magic = apk[footer_off + 8 : footer_off + 24]
    if magic != APK_SIG_BLOCK_MAGIC:
        raise ApkV2VerifyError("APK Sig Block 42 magic not found")

    block_start = cd_off - (trailing_size + 8)
    if block_start < 0:
        raise ApkV2VerifyError("APK Signing Block start underflow")

    leading_size = _u64(apk, block_start)
    if leading_size != trailing_size:
        raise ApkV2VerifyError("APK Signing Block size fields differ")

    pairs_start = block_start + 8
    pairs_end = footer_off
    p = pairs_start
    v2_value = None

    while p < pairs_end:
        pair_len = _u64(apk, p)
        pair_start = p + 8
        pair_end = pair_start + pair_len
        if pair_end > pairs_end or pair_len < 4:
            raise ApkV2VerifyError("invalid signing-block pair")
        pair_id = _u32(apk, pair_start)
        value = apk[pair_start + 4 : pair_end]
        if pair_id == APK_SIGNATURE_SCHEME_V2_ID:
            v2_value = value
        p = pair_end

    if p != pairs_end:
        raise ApkV2VerifyError("signing-block pairs do not end at footer")
    if v2_value is None:
        raise ApkV2VerifyError("v2 ID-value pair missing")

    return {
        "eocd_off": eocd_off,
        "eocd": eocd,
        "cd_off": cd_off,
        "cd_size": cd_size,
        "block_start": block_start,
        "block_size": cd_off - block_start,
        "v2_value": v2_value,
    }


def _parse_v2_signer(v2_value: bytes):
    # Outer: LP(sequence of LP signer blocks)
    signer_sequence, end = _take_lp32(v2_value, 0)
    if end != len(v2_value):
        raise ApkV2VerifyError("trailing bytes in v2 value")

    signers = list(_iter_lp32_sequence(signer_sequence))
    if len(signers) != 1:
        raise ApkV2VerifyError("Anpyra expects exactly one signer")
    signer = signers[0]

    signed_data, p = _take_lp32(signer, 0)
    signatures_sequence, p = _take_lp32(signer, p)
    public_key_der, p = _take_lp32(signer, p)
    if p != len(signer):
        raise ApkV2VerifyError("trailing bytes in signer block")

    # signed_data = LP(digests_seq), LP(certs_seq), LP(attrs_seq)
    digests_seq, q = _take_lp32(signed_data, 0)
    certs_seq, q = _take_lp32(signed_data, q)
    attrs_seq, q = _take_lp32(signed_data, q)
    if q != len(signed_data):
        raise ApkV2VerifyError("trailing bytes in signed data")
    if attrs_seq:
        raise ApkV2VerifyError("unexpected additional attributes")

    digest_items = list(_iter_lp32_sequence(digests_seq))
    if len(digest_items) != 1:
        raise ApkV2VerifyError("expected one digest record")
    digest_record = digest_items[0]
    if len(digest_record) < 8:
        raise ApkV2VerifyError("truncated digest record")
    digest_alg = _u32(digest_record, 0)
    digest_bytes, r = _take_lp32(digest_record, 4)
    if r != len(digest_record):
        raise ApkV2VerifyError("trailing bytes in digest record")

    cert_items = list(_iter_lp32_sequence(certs_seq))
    if len(cert_items) != 1:
        raise ApkV2VerifyError("expected one signer certificate")
    cert_der = cert_items[0]

    signature_items = list(_iter_lp32_sequence(signatures_sequence))
    if len(signature_items) != 1:
        raise ApkV2VerifyError("expected one signature record")
    sig_record = signature_items[0]
    sig_alg = _u32(sig_record, 0)
    signature, r = _take_lp32(sig_record, 4)
    if r != len(sig_record):
        raise ApkV2VerifyError("trailing bytes in signature record")

    if digest_alg != sig_alg:
        raise ApkV2VerifyError("digest/signature algorithm IDs differ")
    if sig_alg != SIG_ALG_RSA_PKCS1_V1_5_WITH_SHA256:
        raise ApkV2VerifyError(f"unexpected signature algorithm 0x{sig_alg:04x}")

    cert = x509.load_der_x509_certificate(cert_der)
    cert_public = cert.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    if cert_public != public_key_der:
        raise ApkV2VerifyError("certificate public key != signer public key")

    cert.public_key().verify(
        signature,
        signed_data,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    return signed_data, digest_bytes, cert


def inspect_apk(path: Path) -> ApkReport:
    apk = path.read_bytes()
    loc = _locate_signing_block(apk)
    signed_data, declared_digest, cert = _parse_v2_signer(loc["v2_value"])

    # For v2 content digest:
    # section 1 = bytes before APK Signing Block
    # section 3 = Central Directory
    # section 4 = EOCD, but CD offset field treated as block start.
    before = apk[: loc["block_start"]]
    central = apk[loc["cd_off"] : loc["eocd_off"]]
    digest_eocd = patch_eocd_central_directory_offset(
        loc["eocd"],
        loc["block_start"],
    )
    actual_digest = compute_chunked_content_digest((before, central, digest_eocd))

    content_digest_ok = actual_digest == declared_digest
    if not content_digest_ok:
        raise ApkV2VerifyError(
            f"content digest mismatch: {actual_digest.hex()} != {declared_digest.hex()}"
        )

    # Standard ZIP readers use the final patched CD offset.
    with zipfile.ZipFile(path, "r") as zf:
        names = tuple(zf.namelist())
        if len(names) != 2 or set(names) != {"AndroidManifest.xml", "classes.dex"}:
            raise ApkV2VerifyError(f"unexpected APK entries: {names}")
        manifest = zf.read("AndroidManifest.xml")
        dex = zf.read("classes.dex")

    info = inspect_manifest(manifest)

    dex_magic_ok = dex[:8] == b"dex\n035\x00"
    dex_sha1_ok = dex[12:32] == hashlib.sha1(dex[32:]).digest()
    dex_checksum_ok = len(dex) >= 112 and _u32(dex, 8) == zlib.adler32(dex[12:]) & 0xFFFFFFFF
    if not dex_magic_ok or not dex_sha1_ok or not dex_checksum_ok:
        raise ApkV2VerifyError("DEX integrity check failed")

    return ApkReport(
        entries=names,
        package=info["package"],
        activity=info["activity"],
        label=info["label"],
        min_sdk=info["minSdkVersion"],
        target_sdk=info["targetSdkVersion"],
        exported=info["exported"],
        dex_magic_ok=dex_magic_ok,
        dex_sha1_ok=dex_sha1_ok,
        dex_checksum_ok=dex_checksum_ok,
        v2_block_found=True,
        v2_signature_ok=True,
        v2_content_digest_ok=True,
        certificate_subject=cert.subject.rfc4514_string(),
        signing_block_size=loc["block_size"],
        central_directory_offset=loc["cd_off"],
    )
