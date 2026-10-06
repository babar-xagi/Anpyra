"""Opt-in Android screen rendering checks using real app pixels on a selected device.

Builds/installs a named test package, leaves it installed, and saves screenshots
and results under a dedicated work directory. No SDK compiler is required.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image as PILImage

from anpyra import AppConfig, build_project, load_project
from anpyra.scaffold import init_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="authorized adb device serial")
    parser.add_argument("--adb", default="adb", help="adb executable name/path")
    parser.add_argument("--package", default="dev.anpyra.screenmatrix")
    parser.add_argument("--work-dir", type=Path, default=Path("build/screen-device-checks"))
    args = parser.parse_args()
    AppConfig(package=args.package)
    ROOT = args.work_dir.resolve()
    if ROOT.exists():
        if load_project(ROOT).config.package != args.package:
            raise ValueError("work directory belongs to another package")
    else:
        init_project(ROOT, package=args.package, label="Screen checks")
    ROOT.joinpath("assets").mkdir(exist_ok=True)
    adb = shutil.which(args.adb)
    if adb is None:
        raise ValueError("adb was not found; use --adb PATH or add platform-tools to PATH")
    ADB = [adb, "-s", args.serial]
    PACKAGE = args.package
    pattern = PILImage.new("RGBA", (1024, 512))
    for x in range(1024):
        color = (255, 0, 0, 255) if x < 341 else (0, 255, 0, 255) if x < 683 else (0, 0, 255, 255)
        pattern.paste(color, (x, 0, x + 1, 512))
    pattern.save(ROOT / "assets/test.png")

    def command(*args):
        return subprocess.check_output(ADB + list(args), text=True, errors="replace")

    def run(name, style):
        ROOT.joinpath("app.py").write_text(
            """from anpyra import Activity
    from anpyra.components import Screen, Image, Gradient, Background
    class MainActivity(Activity):
        def on_create(self, state):
            screen = Screen(self)
    """
            + "".join("        " + line + "\n" for line in style)
            + """        self.set_content_view(screen)
    """,
            encoding="utf-8",
        )
        apk = build_project(ROOT).apk_path
        command("install", "-r", str(apk))
        command("shell", "am", "force-stop", PACKAGE)
        output = command(
            "shell", "am", "start", "-W", "-n", PACKAGE + "/" + PACKAGE + ".MainActivity"
        )
        if "Status: ok" not in output:
            raise RuntimeError(output)
        time.sleep(0.6)
        pid = command("shell", "pidof", PACKAGE).strip()
        if not pid:
            raise RuntimeError(name + ": app did not remain alive")
        png = subprocess.check_output(ADB + ["exec-out", "screencap", "-p"])
        ROOT.joinpath(name + ".png").write_bytes(png)
        return PILImage.open(io.BytesIO(png)).convert("RGB")

    metadata = {
        "api": command("shell", "getprop", "ro.build.version.sdk").strip(),
        "model": command("shell", "getprop", "ro.product.model").strip(),
        "package": PACKAGE,
    }
    base = run("base", [])
    command("shell", "uiautomator", "dump", "/data/local/tmp/anpyra-screen.xml")
    xml = command("shell", "cat", "/data/local/tmp/anpyra-screen.xml")
    tree = ElementTree.fromstring(xml[xml.index("<?xml") :])
    node = next(
        node
        for node in tree.iter("node")
        if node.attrib.get("resource-id") == "android:id/content"
        and node.attrib.get("package") == PACKAGE
    )
    x0, y0, x1, y1 = map(int, re.findall(r"\d+", node.attrib["bounds"]))
    if y1 - y0 <= x1 - x0:
        raise ValueError(
            "native pixel matrix expects portrait content; rotate the phone to portrait"
        )

    def pixel(image, x, y):
        return image.getpixel((round(x0 + (x1 - x0 - 1) * x), round(y0 + (y1 - y0 - 1) * y)))

    results = {}
    results["base"] = {"bounds": [x0, y0, x1, y1], "center": pixel(base, 0.5, 0.5)}
    print("Native content bounds:", results["base"], flush=True)
    solid = run("solid", ['screen.bg.color = "#d21b73"'])
    assert max(abs(a - b) for a, b in zip(pixel(solid, 0.5, 0.5), (210, 27, 115))) <= 2, pixel(
        solid, 0.5, 0.5
    )
    results["solid"] = {"center": pixel(solid, 0.5, 0.5)}
    print("PASS arbitrary solid RGB", flush=True)
    half = run("alpha", ['screen.bg.color = "#d21b73"', "screen.bg.opacity = 0.5"])
    expected = tuple(round((a + b) / 2) for a, b in zip(pixel(base, 0.5, 0.5), (210, 27, 115)))
    assert max(abs(a - b) for a, b in zip(pixel(half, 0.5, 0.5), expected)) <= 3, (
        pixel(half, 0.5, 0.5),
        expected,
    )
    results["alpha"] = {"center": pixel(half, 0.5, 0.5), "expected": expected}
    print("PASS background group opacity", flush=True)
    transparent = run("transparent", ['screen.bg.color = "red"', "screen.bg.transparent = True"])
    assert pixel(transparent, 0.5, 0.5) == pixel(base, 0.5, 0.5)
    results["transparent"] = {"center": pixel(transparent, 0.5, 0.5)}
    print("PASS transparent background", flush=True)
    for direction in (
        "top_bottom",
        "bottom_top",
        "left_right",
        "right_left",
        "tl_br",
        "tr_bl",
        "bl_tr",
        "br_tl",
    ):
        image = run(
            "linear_" + direction,
            [f'screen.bg.gradient = Gradient(["red", "blue"], direction="{direction}")'],
        )
        points = {
            "top_bottom": ((0.5, 0.1), (0.5, 0.9)),
            "bottom_top": ((0.5, 0.9), (0.5, 0.1)),
            "left_right": ((0.1, 0.5), (0.9, 0.5)),
            "right_left": ((0.9, 0.5), (0.1, 0.5)),
            "tl_br": ((0.1, 0.1), (0.9, 0.9)),
            "tr_bl": ((0.9, 0.1), (0.1, 0.9)),
            "bl_tr": ((0.1, 0.9), (0.9, 0.1)),
            "br_tl": ((0.9, 0.9), (0.1, 0.1)),
        }[direction]
        start, end = (pixel(image, *point) for point in points)
        assert start[0] > start[2] and end[2] > end[0], (direction, start, end)
        results["linear_" + direction] = {"start": start, "end": end}
        print("PASS linear " + direction, flush=True)
    radial = run(
        "radial", ['screen.bg.gradient = Gradient(["red", "blue"], kind="radial", radius=220)']
    )
    center, edge = pixel(radial, 0.5, 0.5), pixel(radial, 0.5, 0.05)
    assert center[0] > center[2] and edge[2] > edge[0], (center, edge)
    results["radial"] = {"center": center, "edge": edge}
    print("PASS radial gradient", flush=True)
    sweep = run("sweep", ['screen.bg.gradient = Gradient(["red", "blue"], kind="sweep")'])
    samples = [pixel(sweep, *point) for point in ((0.9, 0.5), (0.5, 0.9), (0.1, 0.5), (0.5, 0.1))]
    assert len(set(samples)) >= 3, samples
    results["sweep"] = {"quadrants": samples}
    print("PASS sweep gradient", flush=True)
    for mode in ("cover", "contain", "fill", "center", "inside", "fit_start", "fit_end"):
        image = run(
            "fit_" + mode,
            [
                'screen.bg.color = "#101010"',
                f'screen.bg.image = Image("assets/test.png", fit="{mode}")',
            ],
        )
        center = pixel(image, 0.5, 0.5)
        top, bottom = pixel(image, 0.5, 0.05), pixel(image, 0.5, 0.95)
        if mode == "cover":
            assert center[1] > 240 and top[1] > 240 and bottom[1] > 240, (mode, center, top, bottom)
        elif mode == "fill":
            assert pixel(image, 0.1, 0.5)[0] > 240 and pixel(image, 0.9, 0.5)[2] > 240
        elif mode == "fit_start":
            assert top[1] > 240 and bottom == (16, 16, 16), (mode, top, bottom)
        elif mode == "fit_end":
            assert bottom[1] > 240 and top == (16, 16, 16), (mode, top, bottom)
        else:
            assert center[1] > 240 and top == (16, 16, 16) and bottom == (16, 16, 16), (
                mode,
                center,
                top,
                bottom,
            )
        results["fit_" + mode] = {"center": center, "top": top, "bottom": bottom}
        print("PASS image fit " + mode, flush=True)
    imagealpha = run(
        "image_alpha",
        [
            'screen.bg.color = "#000000"',
            'screen.bg.image = Image("assets/test.png", fit="fill", opacity=0.5)',
        ],
    )
    assert abs(pixel(imagealpha, 0.5, 0.5)[1] - 128) <= 2, pixel(imagealpha, 0.5, 0.5)
    results["image_alpha"] = {"center": pixel(imagealpha, 0.5, 0.5)}
    print("PASS image opacity", flush=True)
    layered = run(
        "layered_group_alpha",
        [
            'screen.bg.color = "red"',
            'screen.bg.gradient = Gradient(["blue", "blue"])',
            "screen.bg.opacity = 0.5",
        ],
    )
    expected = tuple(round((a + b) / 2) for a, b in zip(pixel(base, 0.5, 0.5), (0, 0, 255)))
    actual = pixel(layered, 0.5, 0.5)
    assert max(abs(a - b) for a, b in zip(actual, expected)) <= 3, (actual, expected)
    results["layered_group_alpha"] = {"center": actual, "expected": expected}
    argb = run("argb_alpha", ['screen.bg.color = "#804080c0"'])
    expected = tuple(
        round(a * (127 / 255) + b * (128 / 255))
        for a, b in zip(pixel(base, 0.5, 0.5), (64, 128, 192))
    )
    actual = pixel(argb, 0.5, 0.5)
    assert max(abs(a - b) for a, b in zip(actual, expected)) <= 3, (actual, expected)
    results["argb_alpha"] = {"center": actual, "expected": expected}
    PILImage.new("RGBA", (256, 128), (20, 220, 40, 128)).save(ROOT / "assets/intrinsic.png")
    intrinsic = run(
        "intrinsic_alpha",
        [
            'screen.bg.color = "#000000"',
            'screen.bg.image = Image("assets/intrinsic.png",fit="fill")',
        ],
    )
    actual = pixel(intrinsic, 0.5, 0.5)
    assert max(abs(a - b) for a, b in zip(actual, (10, 110, 20))) <= 2, actual
    results["intrinsic_alpha"] = {"center": actual, "expected": (10, 110, 20)}
    print("PASS layered opacity, ARGB and intrinsic image alpha", flush=True)
    ROOT.joinpath("device-results.json").write_text(
        json.dumps({"device": metadata, "cases": results}, indent=2), encoding="utf-8"
    )
    print("ALL NATIVE PIXEL CASES PASSED:", len(results), flush=True)


if __name__ == "__main__":
    main()
