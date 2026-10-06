"""Fit normalized raster icons to the declared drawable aspect ratio."""

import math

from PIL import Image, ImageOps


def fit_icon(image, specification):
    width, height = specification.size
    ratio = width / height
    longest = min(4096, max(image.size))
    if ratio >= 1:
        target = (longest, max(1, round(longest / ratio)))
    else:
        target = (max(1, round(longest * ratio)), longest)
    if target[0] * target[1] > 16_000_000:
        scale = math.sqrt(16_000_000 / (target[0] * target[1]))
        target = (max(1, int(target[0] * scale)), max(1, int(target[1] * scale)))
    if specification.fit == "cover":
        return ImageOps.fit(image, target, method=Image.Resampling.LANCZOS)
    if specification.fit == "fill":
        return image.resize(target, Image.Resampling.LANCZOS)
    fitted = ImageOps.contain(image, target, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", target, (0, 0, 0, 0))
    canvas.paste(fitted, ((target[0] - fitted.width) // 2, (target[1] - fitted.height) // 2))
    return canvas
