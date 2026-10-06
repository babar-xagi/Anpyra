"""Opt-in native Button pixels, pointer states, icons and geometry on Android."""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageChops

from anpyra import AppConfig, build_project, load_project
from anpyra.scaffold import init_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--package", default="dev.anpyra.buttonmatrix")
    parser.add_argument("--work-dir", type=Path, default=Path("build/button-device-checks"))
    args = parser.parse_args()
    AppConfig(package=args.package)
    root = args.work_dir.resolve()
    if root.exists():
        if load_project(root).config.package != args.package:
            raise ValueError("work directory belongs to another package")
    else:
        init_project(root, package=args.package, label="Button checks")
    (root / "assets").mkdir(exist_ok=True)
    Image.new("RGBA", (80, 40), (0, 255, 0, 255)).save(root / "assets/icon.png")
    executable = shutil.which(args.adb)
    if executable is None:
        raise ValueError("adb not found")
    adb = [executable, "-s", args.serial]
    checks = {}

    def command(*parts):
        return subprocess.check_output(adb + list(parts), text=True, errors="replace")

    metadata = {
        "package": args.package,
        "model": command("shell", "getprop", "ro.product.model").strip(),
        "api": command("shell", "getprop", "ro.build.version.sdk").strip(),
    }

    def capture(name):
        png = subprocess.check_output(adb + ["exec-out", "screencap", "-p"])
        (root / (name + ".png")).write_bytes(png)
        return Image.open(io.BytesIO(png)).convert("RGB")

    def run(name, *style):
        lines = [
            "screen = Screen(self)",
            'screen.bg.color = "#001020"',
            'button = Button(self,text="GO")',
            "button.style.keep_screen_on = True",
            'button.style.color = "white"',
            "button.style.all_caps = False",
            "button.style.width = 200",
            "button.style.height = 80",
            'button.style.placement = "center"',
            'button.style.bg.color = "#2468ac"',
            'button.style.content_description = "Button test"',
            *style,
            "screen.set_content(button)",
            "self.set_content_view(screen)",
        ]
        (root / "app.py").write_text(
            "from anpyra import Activity\nfrom anpyra.components import Button,ButtonStyle,ButtonState,Border,Background,Gradient,Icon,Screen\nclass MainActivity(Activity):\n    def on_create(self,state):\n"
            + "".join("        " + line + "\n" for line in lines),
            encoding="utf-8",
        )
        apk = build_project(root).apk_path
        command("shell", "input", "keyevent", "224")
        command("install", "-r", str(apk))
        command("shell", "am", "force-stop", args.package)
        started = command("shell", "am", "start", "-W", "-n", args.package + "/.MainActivity")
        if "Status: ok" not in started or not command("shell", "pidof", args.package).strip():
            raise RuntimeError("Button app did not launch: " + started)
        # Wait for Activity enter animation/input-window readiness after replacing
        # the test APK; launch completion can precede touch dispatch readiness.
        time.sleep(2)
        return capture(name)

    def color_box(image, color):
        mask = Image.new("1", image.size, 1)
        for band, expected in enumerate(color):
            test = (
                image.getchannel(band)
                .point(lambda value, target=expected: 255 if value == target else 0)
                .convert("1")
            )
            mask = ImageChops.logical_and(mask, test)
        return mask.getbbox()

    def record(name, detail):
        checks[name] = detail
        (root / "device-results.json").write_text(
            json.dumps({**metadata, "checks": checks}, indent=2), encoding="utf-8"
        )
        print("PASS", name, detail, flush=True)

    def expect(actual, expected, tolerance=2):
        assert max(abs(a - b) for a, b in zip(actual, expected)) <= tolerance, (actual, expected)

    normal = run("normal")
    box = color_box(normal, (36, 104, 172))
    if box is None:
        raise RuntimeError("Button fixture is not visible; unlock the phone")
    x0, y0, x1, y1 = box
    density = (x1 - x0) / 200
    assert abs((y1 - y0) - 80 * density) <= 2
    center = (round((x0 + x1) / 2), round((y0 + y1) / 2))
    sample = (round(x0 + (x1 - x0) * 0.15), center[1])
    assert normal.getpixel(sample) == (36, 104, 172)
    record("native_button_dimensions", {"bounds": box, "density": density})

    gesture = None

    def touch(image_name, down=True):
        nonlocal gesture
        if down:
            gesture = subprocess.Popen(
                adb
                + [
                    "shell",
                    "input",
                    "swipe",
                    str(center[0]),
                    str(center[1]),
                    str(center[0]),
                    str(center[1]),
                    "7000",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(1.6)
        elif gesture is not None:
            gesture.communicate(timeout=10)
            gesture = None
            time.sleep(0.15)
        return capture(image_name)

    run(
        "pressed",
        'button.style.pressed.bg.color = "#d02060"',
        'button.style.pressed.color = "#ffff00"',
    )
    try:
        pressed = touch("pressed_down")
        expect(pressed.getpixel(sample), (208, 32, 96))
        yellow = color_box(pressed, (255, 255, 0))
        assert yellow is not None
    finally:
        released = touch("pressed_up", False)
    expect(released.getpixel(sample), (36, 104, 172))
    record(
        "pressed_background_and_text",
        {
            "pressed_pixel": pressed.getpixel(sample),
            "text_bounds": yellow,
            "released_pixel": released.getpixel(sample),
        },
    )

    disabled = run(
        "disabled",
        'button.style.disabled.bg.color = "#555555"',
        'button.style.disabled.color = "#ff00ff"',
        "button.set_enabled(False)",
    )
    expect(disabled.getpixel(sample), (85, 85, 85))
    assert color_box(disabled, (255, 0, 255)) is not None
    try:
        inactive = touch("disabled_down")
        expect(inactive.getpixel(sample), (85, 85, 85))
    finally:
        touch("disabled_up", False)
    record("disabled_state", {"pixel": disabled.getpixel(sample), "press_unchanged": True})

    outlined = run("border", 'button.style.border = Border("#00ffff",width=4)')
    expect(outlined.getpixel((x0 + round(2 * density), center[1])), (0, 255, 255))
    record("border_dp", {"edge": outlined.getpixel((x0 + round(2 * density), center[1]))})
    rounded = run("rounded", "button.style.corner_radius = 24")
    expect(rounded.getpixel((x0 + 1, y0 + 1)), (0, 16, 32))
    expect(rounded.getpixel(sample), (36, 104, 172))
    record("rounded_corners", {"corner": rounded.getpixel((x0 + 1, y0 + 1))})
    asymmetric = run("asymmetric", "button.style.corner_radius = (24,0,12,0)")
    expect(asymmetric.getpixel((x0 + 1, y0 + 1)), (0, 16, 32))
    expect(asymmetric.getpixel((x1 - 2, y0 + 1)), (36, 104, 172))
    record(
        "four_corner_radii",
        {
            "top_left": asymmetric.getpixel((x0 + 1, y0 + 1)),
            "top_right": asymmetric.getpixel((x1 - 2, y0 + 1)),
        },
    )

    for direction in ("left_right", "right_left", "top_bottom", "bottom_top"):
        gradient = run(
            "gradient_" + direction,
            f'button.style.bg.gradient = Gradient(["red","blue"],direction="{direction}")',
        )
        p = gradient.getpixel((round(x0 + (x1 - x0) * 0.1), round(y0 + (y1 - y0) * 0.1)))
        q = gradient.getpixel((round(x0 + (x1 - x0) * 0.9), round(y0 + (y1 - y0) * 0.9)))
        forward = direction in {"left_right", "top_bottom"}
        assert (p[0] > p[2] and q[2] > q[0]) if forward else (p[2] > p[0] and q[0] > q[2]), (
            direction,
            p,
            q,
        )
        record("gradient_" + direction, {"start": p, "end": q})

    for position in ("start", "end", "top", "bottom"):
        icon_image = run(
            "icon_" + position,
            f'button.style.icon = Icon("assets/icon.png",size=24,position="{position}",fit="fill")',
            "button.style.icon_gap = 8",
        )
        icon = color_box(icon_image, (0, 255, 0))
        if icon is None:
            raise AssertionError("no icon pixels")
        assert (
            abs((icon[2] - icon[0]) - 24 * density) <= 2
            and abs((icon[3] - icon[1]) - 24 * density) <= 2
        )
        if position == "start":
            assert icon[0] < center[0]
        elif position == "end":
            assert icon[2] > center[0]
        elif position == "top":
            assert icon[1] < center[1]
        else:
            assert icon[3] > center[1]
        record("icon_" + position, {"bounds": icon})
    tinted = run(
        "icon_tint", 'button.style.icon = Icon("assets/icon.png",size=24,tint="#00ffff",fit="fill")'
    )
    assert color_box(tinted, (0, 255, 255)) is not None
    record("icon_tint", {"cyan_bounds": color_box(tinted, (0, 255, 255))})

    margin = run(
        "margin", 'button.style.placement = "top_start"', "button.style.margin = (20,0,0,30)"
    )
    margin_box = color_box(margin, (36, 104, 172))
    assert abs(margin_box[0] - 30 * density) <= 2
    assert margin_box[1] < y0
    record("placement_and_margins", {"bounds": margin_box})
    left = run("text_alignment", 'button.style.alignment = "left"', "button.style.padding = (0,24)")
    crop = left.crop(box)
    white = color_box(crop, (255, 255, 255))
    assert white is not None and white[0] < 80 * density
    assert abs((white[1] + white[3]) / 2 - (y1 - y0) / 2) < 20 * density
    record("padding_and_native_vertical_gravity", {"text_bounds": white})

    ripple_before = run(
        "ripple", "button.style.corner_radius = 24", 'button.style.ripple_color = "#80ffffff"'
    )
    try:
        rippled = touch("ripple_down")
        delta = ImageChops.difference(rippled.crop(box), ripple_before.crop(box)).getbbox()
        assert delta is not None
        expect(rippled.getpixel((x0 + 1, y0 + 1)), (0, 16, 32))
    finally:
        touch("ripple_up", False)
    record("native_ripple", {"changed_region": delta, "rounded_mask_kept": True})

    focused = run("focused", 'button.style.focused.bg.color = "#ff8800"')
    command("shell", "input", "keyevent", "KEYCODE_TAB")
    time.sleep(0.2)
    focused = capture("focused_tab")
    expect(focused.getpixel(sample), (255, 136, 0))
    record("focused_state", {"pixel": focused.getpixel(sample)})

    command("shell", "uiautomator", "dump", "/data/local/tmp/anpyra-button.xml")
    xml = command("shell", "cat", "/data/local/tmp/anpyra-button.xml")
    tree = ElementTree.fromstring(xml[xml.index("<?xml") :])
    node = next(
        node
        for node in tree.iter("node")
        if node.attrib.get("package") == args.package
        and node.attrib.get("content-desc") == "Button test"
    )
    assert node.attrib["class"] == "android.widget.Button" and node.attrib["clickable"] == "true"
    record(
        "native_button_accessibility",
        {
            "class": node.attrib["class"],
            "text": node.attrib["text"],
            "clickable": node.attrib["clickable"],
        },
    )
    print(f"Button device checks passed: {len(checks)} cases; {root}", flush=True)


if __name__ == "__main__":
    main()
