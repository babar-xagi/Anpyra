# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

APK_SIG_BLOCK_MAGIC = b"APK Sig Block 42"
APK_SIGNATURE_SCHEME_V2_ID = 0x7109871A
SIG_ALG_RSA_PKCS1_V1_5_WITH_SHA256 = 0x0103
EOCD_SIGNATURE = b"PK\x05\x06"
MAX_CHUNK_SIZE = 1024 * 1024


class V2SigningError(ValueError):
    pass


@dataclass(frozen=True)
class ZipSections:
    before_central_directory: bytes
    central_directory: bytes
    eocd: bytes
    central_directory_offset: int
    central_directory_size: int
    eocd_offset: int


@dataclass(frozen=True)
class V2SignerMaterial:
    private_key: rsa.RSAPrivateKey
    certificate_der: bytes
    public_key_der: bytes


@dataclass(frozen=True)
class V2SignResult:
    apk: bytes
    certificate_der: bytes
    content_digest: bytes
    signing_block_size: int
    original_central_directory_offset: int
    final_central_directory_offset: int


def _u32(value: int) -> bytes:
    return struct.pack("<I", value)


def _u64(value: int) -> bytes:
    return struct.pack("<Q", value)


def lp32(payload: bytes) -> bytes:
    return _u32(len(payload)) + payload


def seq32(elements: list[bytes] | tuple[bytes, ...]) -> bytes:
    return b"".join(lp32(x) for x in elements)


def find_eocd(apk: bytes) -> int:
    # EOCD is at least 22 bytes and may have a ZIP comment up to 65535 bytes.
    start = max(0, len(apk) - (22 + 0xFFFF))
    pos = apk.rfind(EOCD_SIGNATURE, start)
    if pos < 0:
        raise V2SigningError("ZIP End of Central Directory not found")

    if pos + 22 > len(apk):
        raise V2SigningError("truncated EOCD")

    comment_len = struct.unpack_from("<H", apk, pos + 20)[0]
    if pos + 22 + comment_len != len(apk):
        raise V2SigningError(
            "EOCD is not the final ZIP structure or comment length is inconsistent"
        )
    return pos


def split_zip_sections(apk: bytes) -> ZipSections:
    eocd_off = find_eocd(apk)
    eocd = apk[eocd_off:]

    disk_no, cd_disk, disk_entries, total_entries, cd_size, cd_off = struct.unpack_from(
        "<HHHHII", eocd, 4
    )

    if disk_no != 0 or cd_disk != 0:
        raise V2SigningError("multi-disk ZIP/APK is not supported")
    if disk_entries != total_entries:
        raise V2SigningError("multi-disk entry count mismatch")
    if cd_off + cd_size != eocd_off:
        raise V2SigningError("Central Directory must immediately precede EOCD")

    return ZipSections(
        before_central_directory=apk[:cd_off],
        central_directory=apk[cd_off:eocd_off],
        eocd=eocd,
        central_directory_offset=cd_off,
        central_directory_size=cd_size,
        eocd_offset=eocd_off,
    )


def patch_eocd_central_directory_offset(eocd: bytes, new_offset: int) -> bytes:
    if eocd[:4] != EOCD_SIGNATURE:
        raise V2SigningError("not an EOCD record")
    if not 0 <= new_offset <= 0xFFFFFFFF:
        raise V2SigningError("ZIP64 not implemented in Anpyra")
    out = bytearray(eocd)
    struct.pack_into("<I", out, 16, new_offset)
    return bytes(out)


def compute_chunked_content_digest(sections: tuple[bytes, ...]) -> bytes:
    chunk_digests: list[bytes] = []

    for section in sections:
        pos = 0
        while pos < len(section):
            chunk = section[pos : pos + MAX_CHUNK_SIZE]
            prefix = b"\xa5" + _u32(len(chunk))
            chunk_digests.append(hashlib.sha256(prefix + chunk).digest())
            pos += len(chunk)

    if not chunk_digests:
        raise V2SigningError("APK digest cannot have zero chunks")

    top = b"\x5a" + _u32(len(chunk_digests)) + b"".join(chunk_digests)
    return hashlib.sha256(top).digest()


def generate_signer_material() -> V2SignerMaterial:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Anpyra Debug"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local Development"),
        ]
    )

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    cert_der = cert.public_bytes(serialization.Encoding.DER)
    public_key_der = key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return V2SignerMaterial(key, cert_der, public_key_der)


def load_or_create_signer_material(state_dir: Path) -> V2SignerMaterial:
    """Keep one local debug signer so rebuilt APKs can update the same package."""
    state_dir.mkdir(parents=True, exist_ok=True)
    key_path = state_dir / "debug-key.pem"
    cert_path = state_dir / "debug-cert.der"

    if key_path.exists() != cert_path.exists():
        raise V2SigningError(
            "incomplete debug signing identity: restore both debug-key.pem and debug-cert.der"
        )

    if key_path.exists() and cert_path.exists():
        key = serialization.load_pem_private_key(
            key_path.read_bytes(),
            password=None,
        )
        if not isinstance(key, rsa.RSAPrivateKey):
            raise V2SigningError("debug key is not an RSA private key")
        cert_der = cert_path.read_bytes()
        cert = x509.load_der_x509_certificate(cert_der)
        cert_public = cert.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_public = key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if cert_public != key_public:
            raise V2SigningError("stored debug certificate does not match debug key")
        return V2SignerMaterial(key, cert_der, key_public)

    material = generate_signer_material()
    key_path.write_bytes(
        material.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(material.certificate_der)
    return material


def build_v2_value(
    *,
    content_digest: bytes,
    material: V2SignerMaterial,
) -> bytes:
    # signedData.digests:
    # sequence< LP( uint32 algorithm_id + LP(digest) ) >
    digest_record = _u32(SIG_ALG_RSA_PKCS1_V1_5_WITH_SHA256) + lp32(content_digest)
    digests_sequence = seq32([digest_record])

    # signedData.certificates:
    # sequence< LP(certificate DER) >
    certificates_sequence = seq32([material.certificate_der])

    # signedData.additionalAttributes = empty sequence
    attributes_sequence = b""

    # signer.signedData is itself three length-prefixed fields.
    signed_data = seq32(
        [
            digests_sequence,
            certificates_sequence,
            attributes_sequence,
        ]
    )

    signature = material.private_key.sign(
        signed_data,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    signature_record = _u32(SIG_ALG_RSA_PKCS1_V1_5_WITH_SHA256) + lp32(signature)
    signatures_sequence = seq32([signature_record])

    # signer = LP(signed_data) + LP(signatures_sequence) + LP(public_key)
    signer = seq32(
        [
            signed_data,
            signatures_sequence,
            material.public_key_der,
        ]
    )

    # V2 block = LP(sequence-of-LP-signers). With one signer:
    # [ total-signers-length ][ signer-length ][ signer bytes ]
    signer_sequence = seq32([signer])
    return lp32(signer_sequence)


def build_apk_signing_block(v2_value: bytes) -> bytes:
    pair_payload = _u32(APK_SIGNATURE_SCHEME_V2_ID) + v2_value
    pair = _u64(len(pair_payload)) + pair_payload

    # First size excludes its own uint64 but includes:
    # pair(s) + trailing size + 16-byte magic.
    size_field = len(pair) + 8 + len(APK_SIG_BLOCK_MAGIC)

    block = _u64(size_field) + pair + _u64(size_field) + APK_SIG_BLOCK_MAGIC

    if len(block) != size_field + 8:
        raise AssertionError("APK Signing Block size calculation failed")
    return block


def sign_apk_v2(unsigned_apk: bytes, material: V2SignerMaterial | None = None) -> V2SignResult:
    sections = split_zip_sections(unsigned_apk)
    if material is None:
        material = generate_signer_material()

    # When digesting EOCD, AOSP requires the Central Directory offset field
    # to contain the APK Signing Block's start offset. We insert the block at
    # the original Central Directory offset, so this is the original cd offset.
    digest_eocd = patch_eocd_central_directory_offset(
        sections.eocd,
        sections.central_directory_offset,
    )

    content_digest = compute_chunked_content_digest(
        (
            sections.before_central_directory,
            sections.central_directory,
            digest_eocd,
        )
    )

    v2_value = build_v2_value(
        content_digest=content_digest,
        material=material,
    )
    signing_block = build_apk_signing_block(v2_value)

    final_cd_offset = sections.central_directory_offset + len(signing_block)
    final_eocd = patch_eocd_central_directory_offset(
        sections.eocd,
        final_cd_offset,
    )

    final_apk = (
        sections.before_central_directory + signing_block + sections.central_directory + final_eocd
    )

    return V2SignResult(
        apk=final_apk,
        certificate_der=material.certificate_der,
        content_digest=content_digest,
        signing_block_size=len(signing_block),
        original_central_directory_offset=sections.central_directory_offset,
        final_central_directory_offset=final_cd_offset,
    )
