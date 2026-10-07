"""Opt-in generic callback, input and saved-instance-state checks on Android."""

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree

from anpyra import build_project, load_project
from anpyra.scaffold import init_project

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--work-dir", type=Path, default=Path("build/event-device-checks"))
    args = parser.parse_args()
    executable = shutil.which(args.adb)
    if executable is None:
        raise ValueError("adb not found")
    adb = [executable, "-s", args.serial]
    root = args.work_dir.resolve()
    package = "dev.anpyra.eventchecks"
    project = (
        load_project(root)
        if root.exists()
        else init_project(root, package=package, label="Event checks")
    )
    if project.config.package != package:
        raise ValueError("work directory belongs to another package")
    text = (ROOT / "examples/counter/app.py").read_text(encoding="utf-8")
    (root / "app.py").write_text(text, encoding="utf-8")
    checks = []

    def command(*parts):
        return subprocess.check_output(
            adb + list(parts), text=True, encoding="utf-8", errors="replace"
        )

    def nodes():
        path = "/data/local/tmp/anpyra-events.xml"
        command("shell", "uiautomator", "dump", path)
        raw = command("shell", "cat", path)
        command("shell", "rm", path)
        result = [
            dict(n.attrib)
            for n in ElementTree.fromstring(raw[raw.index("<?xml") :]).iter("node")
            if n.attrib.get("package") == package
        ]
        if not result:
            raise RuntimeError("Keep the phone unlocked with Event checks in the foreground")
        return result

    def find(ns, *, text=None, desc=None):
        return next(
            (
                n
                for n in ns
                if (text is None or n.get("text") == text)
                and (desc is None or n.get("content-desc") == desc)
            ),
            None,
        )

    def tap(node):
        x0, y0, x1, y1 = map(int, re.findall(r"\d+", node["bounds"]))
        command("shell", "input", "tap", str((x0 + x1) // 2), str((y0 + y1) // 2))

    def click(label):
        for _ in range(5):
            ns = nodes()
            node = find(ns, text=label)
            if node is not None:
                tap(node)
                time.sleep(0.2)
                return
            scroll = next(n for n in ns if n.get("class") == "android.widget.ScrollView")
            x0, y0, x1, y1 = map(int, re.findall(r"\d+", scroll["bounds"]))
            command(
                "shell",
                "input",
                "swipe",
                str((x0 + x1) // 2),
                str(y1 - 30),
                str((x0 + x1) // 2),
                str(y0 + 30),
                "350",
            )
        raise AssertionError("button not visible: " + label)

    def top():
        for _ in range(2):
            command("shell", "input", "swipe", "360", "300", "360", "900", "300")

    def value(desc):
        ns = nodes()
        node = find(ns, desc=desc)
        if node is None:
            top()
            node = find(nodes(), desc=desc)
        assert node is not None, desc
        return node["text"]

    def fresh():
        command("shell", "am", "force-stop", package)
        command("shell", "am", "start", "-W", "-n", package + "/.MainActivity", "-f", "0x10008000")
        time.sleep(2)

    def record(name):
        checks.append(name)
        print("PASS: " + name, flush=True)

    def build(source):
        (root / "app.py").write_text(source, encoding="utf-8")
        result = build_project(root)
        command("install", "-r", str(result.apk_path))
        fresh()

    build(text)
    assert value("counter-value") == "0"
    record("cold_initial_state")
    plus = find(nodes(), text="+")
    for _ in range(20):
        tap(plus)
    assert value("counter-value") == "20"
    record("repeated_click_updates")
    click("Reset")
    click("−")
    assert value("counter-value") == "-1"
    record("decrement_and_reset")
    click("Pause")
    top()
    ns = nodes()
    assert find(ns, text="+")["enabled"] == "false" and value("counter-status") == "Paused: True"
    tap(find(ns, text="+"))
    assert value("counter-value") == "-1"
    record("typed_bool_and_native_disabled_button")
    click("Resume")
    top()
    click("Reset")
    click("+")
    click("+")
    entry = find(nodes(), desc="name-input")
    tap(entry)
    time.sleep(1)
    command("shell", "input", "text", "Babar")
    time.sleep(1)
    click("Show name")
    assert value("name-preview") == "Hello, Babar!"
    record("input_getter_and_dynamic_string")
    click("Pause")
    click("Recreate screen • restore count/name")
    time.sleep(2)
    top()
    assert value("counter-value") == "2"
    assert value("counter-status") == "Paused: False"
    click("Show name")
    assert value("name-preview") == "Hello, Babar!"
    record("recreation_restores_opted_in_int_and_string")
    record("nonpersistent_bool_resets_on_recreation")
    fresh()
    assert value("counter-value") == "0"
    record("new_task_resets_saved_instance_state")
    # Real ART checks for the numeric/boolean/string bytecode boundary cases.
    cases = (
        (
            "self.count: int = State(0, persist=True)",
            "self.count: int = State(2147483647, persist=True)",
            "+",
            "-2147483648",
            "signed_int32_add_wrap",
        ),
        (
            "self.count: int = State(0, persist=True)",
            "self.count: int = State(-2147483648, persist=True)",
            "−",
            "2147483647",
            "signed_int32_sub_wrap",
        ),
        (
            "self.paused: bool = False",
            "self.paused: bool = State(False, persist=True)",
            "Pause",
            "Paused: True",
            "opted_in_bool_restoration",
        ),
    )
    for original, replacement, label, expected, name in cases:
        build(text.replace(original, replacement))
        click(label)
        if label == "Pause":
            click("Recreate screen • restore count/name")
            time.sleep(2)
        top()
        assert value("counter-status" if label == "Pause" else "counter-value") == expected
        record(name)
    build(text)
    click("+")
    (root / "counter.png").write_bytes(
        subprocess.check_output(adb + ["exec-out", "screencap", "-p"])
    )
    metadata = {
        "model": command("shell", "getprop", "ro.product.model").strip(),
        "api": command("shell", "getprop", "ro.build.version.sdk").strip(),
        "checks": checks,
        "settings_changed": False,
    }
    (root / "report.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Event device checks passed: {len(checks)}; {root}", flush=True)


if __name__ == "__main__":
    main()
