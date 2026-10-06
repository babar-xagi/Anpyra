"""Validate project images and package deterministic, oriented static PNG assets."""

from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image as PillowImage
from PIL import ImageCms, ImageOps, UnidentifiedImageError

from ..compiler.ir import AppIR, ApplyScreenBackground, IfBool, IfCompare


class AssetError(ValueError):
    pass


@dataclass(frozen=True)
class PreparedAssets:
    ir: AppIR
    entries: dict[str, bytes]
    report: tuple[dict, ...]


def validate_png(payload: bytes) -> None:
    """Check the packaged raster profile, including PNG checksums and dimensions."""
    try:
        with PillowImage.open(io.BytesIO(payload)) as image:
            if (
                image.format != "PNG"
                or max(image.size) > 4096
                or image.width * image.height > 16_000_000
            ):
                raise AssetError("invalid packaged image format/dimensions")
            image.verify()
    except (OSError, ValueError, SyntaxError) as exc:
        raise AssetError(f"invalid packaged PNG: {exc}") from exc


def prepare_assets(app: AppIR, root: Path) -> PreparedAssets:
    root = root.resolve()
    entries = {}
    report = {}

    def prepare(op):
        if isinstance(op, (IfBool, IfCompare)):
            return replace(
                op,
                then_ops=tuple(prepare(item) for item in op.then_ops),
                else_ops=tuple(prepare(item) for item in op.else_ops),
            )
        if not isinstance(op, ApplyScreenBackground) or op.background.image is None:
            return op
        spec = op.background.image
        path = (root / spec.path).resolve()
        if not path.is_relative_to(root):
            raise AssetError(f"image path escapes project: {spec.path}")
        if not path.is_file():
            raise AssetError(f"image does not exist: {spec.path}")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", PillowImage.DecompressionBombWarning)
                with PillowImage.open(path) as source:
                    if source.format in {"EPS", "PDF", "WMF"}:
                        raise AssetError(
                            "screen images must be raster images; convert vector/document files to PNG"
                        )
                    if source.width * source.height > 16_000_000 or max(source.size) > 4096:
                        raise AssetError(
                            "image exceeds 4096 pixels per side or 16 million pixels; resize it first"
                        )
                    if spec.frame >= getattr(source, "n_frames", 1):
                        raise AssetError(f"image frame {spec.frame} does not exist: {spec.path}")
                    source.seek(spec.frame)
                    oriented = ImageOps.exif_transpose(source)
                    profile = source.info.get("icc_profile")
                    if profile:
                        if oriented.mode == "P":
                            oriented = oriented.convert("RGBA")
                        oriented = ImageCms.profileToProfile(
                            oriented,
                            ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                            ImageCms.createProfile("sRGB"),
                            outputMode="RGBA",
                        )
                    normalized = oriented.convert("RGBA")
                    normalized.info.clear()
                    buffer = io.BytesIO()
                    normalized.save(buffer, format="PNG", optimize=False)
                    payload = buffer.getvalue()
                    width, height = normalized.size
        except (
            OSError,
            ValueError,
            UnidentifiedImageError,
            ImageCms.PyCMSError,
            PillowImage.DecompressionBombError,
            PillowImage.DecompressionBombWarning,
        ) as exc:
            raise AssetError(f"cannot decode image {spec.path}: {exc}") from exc
        digest = hashlib.sha256(payload).hexdigest()
        asset = f"anpyra/{digest}.png"
        entry = "assets/" + asset
        entries[entry] = payload
        report[(spec.path, spec.frame)] = {
            "source": spec.path,
            "frame": spec.frame,
            "entry": entry,
            "sha256": digest,
            "width": width,
            "height": height,
        }
        return replace(op, image_asset=asset)

    prepared = replace(app, operations=tuple(prepare(op) for op in app.operations))
    return PreparedAssets(prepared, entries, tuple(report.values()))
