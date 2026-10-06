"""Opt-in typography pixel/geometry checks on one connected Android test device."""

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
from PIL import ImageChops

from anpyra import AppConfig, build_project, load_project
from anpyra.scaffold import init_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--package", default="dev.anpyra.textmatrix")
    parser.add_argument("--work-dir", type=Path, default=Path("build/text-device-checks"))
    parser.add_argument(
        "--resume-from",
        help="reuse earlier screenshots and start fresh device captures at this case; use only for an unchanged test candidate",
    )
    args = parser.parse_args()
    AppConfig(package=args.package)
    root = args.work_dir.resolve()
    if root.exists():
        if load_project(root).config.package != args.package:
            raise ValueError("work directory belongs to another package")
    else:
        init_project(root, package=args.package, label="Text checks")
    adb = shutil.which(args.adb)
    if adb is None:
        raise ValueError("adb was not found")
    command_base = [adb, "-s", args.serial]
    assets = Path(__file__).resolve().parents[1] / "examples/text_style/assets"
    (root / "assets").mkdir(exist_ok=True)
    for extension in ("ttf", "otf"):
        shutil.copyfile(
            assets / ("AnpyraDemo." + extension), root / "assets" / ("demo." + extension)
        )

    def command(*parts):
        return subprocess.check_output(command_base + list(parts), text=True, errors="replace")

    metadata = {
        "model": command("shell", "getprop", "ro.product.model").strip(),
        "api": command("shell", "getprop", "ro.build.version.sdk").strip(),
        "package": args.package,
    }
    results = {}
    bounds = None
    replaying = args.resume_from is not None
    metadata["reused_screenshots"] = []

    def run(name, style=(), text="ABC", *, system_font=False):
        nonlocal replaying
        if replaying and name != args.resume_from:
            cached = root / (name + ".png")
            if not cached.is_file():
                raise ValueError("missing earlier screenshot for resume: " + name)
            metadata["reused_screenshots"].append(name)
            image = PILImage.open(cached).convert("RGB")
            return image if bounds is None else image.crop(bounds)
        replaying = False
        command("shell", "input", "keyevent", "224")
        lines = [
            "screen = Screen(self)",
            'screen.bg.color = "#001020"',
            f"title = TextView(self, text={text!r})",
            'title.style.color = "#ff0000"',
            "title.style.keep_screen_on = True",
            "title.style.size = 24",
            "title.style.include_font_padding = False",
            'title.style.width = "match_parent"',
            'title.style.height = "match_parent"',
            'title.style.content_description = "Typography test"',
        ]
        lines += (
            ['title.style.font = Font(family="monospace")']
            if system_font
            else ['title.style.font = Font(path="assets/demo.ttf")']
        )
        lines.extend(style)
        lines.extend(["screen.set_content(title)", "self.set_content_view(screen)"])
        (root / "app.py").write_text(
            "from anpyra import Activity\nfrom anpyra.components import TextView, Screen, Font, Shadow, TextStyle\nclass MainActivity(Activity):\n    def on_create(self,state):\n"
            + "".join("        " + line + "\n" for line in lines),
            encoding="utf-8",
        )
        apk = build_project(root).apk_path
        command("install", "-r", str(apk))
        command("shell", "am", "force-stop", args.package)
        output = command("shell", "am", "start", "-W", "-n", args.package + "/.MainActivity")
        if "Status: ok" not in output:
            raise RuntimeError(output)
        time.sleep(0.6)
        if not command("shell", "pidof", args.package).strip():
            raise RuntimeError(name + ": app did not remain alive")
        png = subprocess.check_output(command_base + ["exec-out", "screencap", "-p"])
        (root / (name + ".png")).write_bytes(png)
        image = PILImage.open(io.BytesIO(png)).convert("RGB")
        return image if bounds is None else image.crop(bounds)

    def hierarchy():
        command("shell", "uiautomator", "dump", "/data/local/tmp/anpyra-text.xml")
        xml = command("shell", "cat", "/data/local/tmp/anpyra-text.xml")
        return ElementTree.fromstring(xml[xml.index("<?xml") :])

    def ink(image, channel=0):
        mask = image.getchannel(channel).point(lambda value: 255 if value > 180 else 0).convert("1")
        for other in range(3):
            if other != channel:
                test = (
                    image.getchannel(other)
                    .point(lambda value: 255 if value < 60 else 0)
                    .convert("1")
                )
                mask = ImageChops.logical_and(mask, test)
        box = mask.getbbox()
        if box is None:
            raise AssertionError(
                "no expected text pixels; keep the phone unlocked and the test app visible"
            )
        return box, mask.convert("L").histogram()[255]

    def record(name, detail):
        results[name] = detail
        (root / "device-results.json").write_text(
            json.dumps({**metadata, "checks": results}, indent=2), encoding="utf-8"
        )
        print("PASS", name, detail, flush=True)

    image = run("baseline")
    cached_result = (
        json.loads((root / "device-results.json").read_text(encoding="utf-8"))
        if args.resume_from
        else None
    )
    if cached_result:
        if any(cached_result[key] != metadata[key] for key in ("model", "api", "package")):
            raise ValueError("resume metadata belongs to another device or package")
        accessibility_bounds = tuple(
            cached_result["checks"]["baseline_ttf"]["accessibility_bounds"]
        )
    else:
        node = next(
            (
                node
                for node in hierarchy().iter("node")
                if node.attrib.get("resource-id") == "android:id/content"
                and node.attrib.get("package") == args.package
            ),
            None,
        )
        if node is None:
            raise RuntimeError(
                "test app content is not visible; unlock the phone and keep this app open"
            )
        accessibility_bounds = tuple(map(int, re.findall(r"\d+", node.attrib["bounds"])))
    # Some OEM accessibility windows clip the reported bottom by a system inset.
    # Derive visible app content from the exact background of our test fixture.
    background = PILImage.new("1", image.size, 1)
    for channel, expected in enumerate((0, 16, 32)):
        test = (
            image.getchannel(channel)
            .point(lambda value, wanted=expected: 255 if value == wanted else 0)
            .convert("1")
        )
        background = ImageChops.logical_and(background, test)
    bounds = background.getbbox()
    if bounds is None:
        raise RuntimeError("test background is not visible; keep the phone unlocked")
    image = image.crop(bounds)
    base_box, base_count = ink(image)
    width, height = image.size
    record(
        "baseline_ttf",
        {
            "bounds": bounds,
            "accessibility_bounds": accessibility_bounds,
            "ink": base_box,
            "pixels": base_count,
        },
    )
    larger = ink(run("larger", ["title.style.size = 36"]))[0]
    assert larger[2] - larger[0] > (base_box[2] - base_box[0]) * 1.4
    record("size_sp", {"ink": larger})
    letter = ink(run("letter_spacing", ["title.style.letter_spacing = .3"]))[0]
    assert letter[2] - letter[0] > base_box[2] - base_box[0] + 15
    record("letter_spacing", {"ink": letter})
    for horizontal in ("left", "center", "right", "start", "end"):
        for vertical in ("top", "center", "bottom"):
            name = "alignment_" + horizontal + "_" + vertical
            box, count = ink(
                run(
                    name,
                    [
                        f'title.style.alignment = "{horizontal}"',
                        f'title.style.vertical_alignment = "{vertical}"',
                    ],
                )
            )
            center_x, center_y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            if horizontal in {"left", "start"}:
                assert center_x < width * 0.25
            elif horizontal in {"right", "end"}:
                assert center_x > width * 0.75
            else:
                assert abs(center_x - width / 2) < width * 0.05
            if vertical == "top":
                assert center_y < height * 0.15
            elif vertical == "bottom":
                assert center_y > height * 0.85
            else:
                assert abs(center_y - height / 2) < height * 0.05
            record(name, {"ink": box, "pixels": count})
    padded = ink(run("padding", ["title.style.padding = (20, 0, 0, 40)"]))[0]
    dx, dy = padded[0] - base_box[0], padded[1] - base_box[1]
    assert dx > 35 and abs(dx - 2 * dy) <= 3, (dx, dy)
    density = dx / 40
    record("padding_dp", {"ink": padded, "observed_density": density})
    for property in ("underline", "strikethrough"):
        box, count = ink(run(property, [f"title.style.{property} = True"]))
        assert count > base_count
        restored = ink(
            run(
                property + "_off",
                [f"title.style.{property} = True", f"title.style.{property} = False"],
            )
        )
        assert restored == (base_box, base_count)
        record(property, {"ink": box, "pixels": count, "restored_pixels": restored[1]})
    otf = ink(run("otf", ['title.style.font = Font(path="assets/demo.otf")']))
    assert otf[0][2] - otf[0][0] == base_box[2] - base_box[0]
    record("otf", {"ink": otf[0], "pixels": otf[1]})
    normal = ink(run("normal_font"))[1]
    bold = ink(run("bold", ["title.style.font.bold = True"]))[1]
    assert bold > normal
    italic = ink(run("italic", ["title.style.font.italic = True"]))[0]
    assert italic != base_box
    record("font_bold_italic", {"normal_pixels": normal, "bold_pixels": bold, "italic_ink": italic})
    caps = run("all_caps", ["title.style.all_caps = True"], "aA", system_font=True)
    expected_caps = run("all_caps_reference", text="AA", system_font=True)
    assert caps.tobytes() == expected_caps.tobytes()
    record("all_caps", {"matches_explicit_uppercase": True})
    opacity = run("opacity", ["title.style.opacity = .5"])
    sample = image.getpixel((base_box[0] + 1, base_box[1] + 1))
    # Locate a fully covered glyph pixel from the baseline rather than assuming its shape.
    point = next(
        (x, y) for y in range(height) for x in range(width) if image.getpixel((x, y)) == (255, 0, 0)
    )
    actual = opacity.getpixel(point)
    assert max(abs(a - b) for a, b in zip(actual, (128, 8, 16))) <= 3, actual
    record("opacity", {"pixel": actual, "baseline_sample": sample})
    dimensions = run(
        "dimensions",
        [
            "title.style.width = 200",
            "title.style.height = 100",
            'title.style.background_color = "#113355"',
        ],
    )
    assert dimensions.getpixel((round(100 * density), round(80 * density))) == (17, 51, 85)
    assert dimensions.getpixel((round(210 * density), round(80 * density))) == (0, 16, 32)
    record("dimensions_background", {"density": density})
    two_lines = ink(run("two_lines", text="ABC\nDEF"))[0]
    spaced = ink(run("line_spacing", ["title.style.line_spacing = (20,1)"], text="ABC\nDEF"))[0]
    assert abs((spaced[3] - two_lines[3]) - 20 * density) <= 3
    record("line_spacing", {"baseline": two_lines, "spaced": spaced})
    rtl = ink(
        run("rtl", ['title.style.text_direction = "rtl"', 'title.style.alignment = "start"'])
    )[0]
    # Text direction does not change the view's LTR layout direction on this fixture.
    assert rtl[0] < width * 0.3
    record("rtl_start", {"ink": rtl, "layout_direction_unchanged": True})
    run("selectable", ["title.style.selectable = True"])
    view = next(
        node
        for node in hierarchy().iter("node")
        if node.attrib.get("content-desc") == "Typography test"
    )
    # Android hides click/long-click accessibility actions for selectable text.
    # Exercise the actual long-press gesture rather than asserting hidden flags.
    assert view.attrib["focusable"] == "true"
    x = round((base_box[0] + base_box[2]) / 2 + bounds[0])
    y = round((base_box[1] + base_box[3]) / 2 + bounds[1])
    command("shell", "input", "swipe", str(x), str(y), str(x), str(y), "1200")
    own = [node for node in hierarchy().iter("node") if node.attrib.get("package") == args.package]
    focused = next(node for node in own if node.attrib.get("content-desc") == "Typography test")
    assert focused.attrib["focused"] == "true"
    png = subprocess.check_output(command_base + ["exec-out", "screencap", "-p"])
    (root / "selection_long_press.png").write_bytes(png)
    record(
        "selection_accessibility",
        {
            "text": view.attrib["text"],
            "bounds": view.attrib["bounds"],
            "focused_after_long_press": True,
            "toolbar_labels": [
                node.attrib["text"]
                for node in own
                if node.attrib.get("text") and node.attrib["text"] not in {"ABC", "Text checks"}
            ],
        },
    )
    # Exercise remaining native calls together; this records liveness, not pixel proof for each option.
    run(
        "native_options",
        [
            "title.style.min_lines = 1",
            "title.style.max_lines = 2",
            "title.style.single_line = True",
            'title.style.ellipsize = "end"',
            "title.style.font_features = \"'kern' 0\"",
            'title.style.shadow = Shadow("#00ff00",radius=1,dx=10,dy=3)',
        ],
        text="A long native title that must ellipsize inside the view",
    )
    record("remaining_native_calls", {"launch_ok": True})
    print(f"Typography device checks passed: {len(results)} recorded cases; {root}", flush=True)


if __name__ == "__main__":
    main()
