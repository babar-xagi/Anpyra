"""Opt-in Android chat acceptance with a loopback fixture server and no API key.

Only this test build uses HTTP + target SDK 27 to allow loopback fixture traffic.
The real example retains target SDK 36 and the fixed OpenAI HTTPS endpoint.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import threading
import time
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from anpyra import Project, build_project, load_project
from anpyra.scaffold import init_project

ROOT = Path(__file__).resolve().parents[1]


def message(text):
    return {
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": text, "annotations": []}],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--work-dir", type=Path, default=Path("build/chat-device-checks"))
    args = parser.parse_args()
    executable = shutil.which(args.adb)
    if executable is None:
        raise ValueError("adb not found")
    adb = [executable, "-s", args.serial]
    root = args.work_dir.resolve()
    package = "dev.anpyra.chatchecks"
    project = load_project(root) if root.exists() else init_project(root, package=package)
    if project.config.package != package:
        raise ValueError("work directory belongs to another app")
    (root / "app.py").write_text(
        (ROOT / "examples/chatbot/app.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    requests = []
    release_first = threading.Event()
    reasoning = {
        "type": "reasoning",
        "id": "rs_fixture",
        "summary": [],
        "encrypted_content": "opaque-fixture-content",
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(data)
            prompt = data["input"][-1]["content"]
            if prompt == "My name is Babar.":
                release_first.wait(30)
                output = [reasoning, message("Hello Babar!\n" + "Native chat line.\n" * 38)]
            elif prompt == "What is my name?":
                output = [message("Your name is Babar.")]
            elif prompt == "quota fixture":
                self.send_response(429)
                self.end_headers()
                self.wfile.write(b'{"error":{"code":"insufficient_quota"}}')
                return
            elif prompt == "bad JSON fixture":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"invalid-json")
                return
            elif prompt == "incomplete fixture":
                output = [message("Truncated text must not become chat history.")]
            elif prompt == "Refusal fixture":
                output = [
                    {
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "refusal", "refusal": "I cannot help with that request."}
                        ],
                    }
                ]
            else:
                output = [message("This is a fresh chat.")]
            payload = json.dumps(
                {
                    "status": "incomplete" if prompt == "incomplete fixture" else "completed",
                    "output": output,
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def command(*parts):
        return subprocess.check_output(
            adb + list(parts), text=True, encoding="utf-8", errors="replace"
        )

    def nodes():
        path = "/data/local/tmp/anpyra-chat-check.xml"
        command("shell", "uiautomator", "dump", path)
        raw = command("shell", "cat", path)
        command("shell", "rm", path)
        result = [
            dict(n.attrib)
            for n in ElementTree.fromstring(raw[raw.index("<?xml") :]).iter("node")
            if n.attrib.get("package") == package
        ]
        # Never retain or print text from an input, even though this fixture has no real key.
        for n in result:
            if n.get("class") == "android.widget.EditText":
                n["input_masked"] = n.get("password") == "true" and n.get("text") != "fixture-key"
                n["text"] = "[input redacted]"
        if not result:
            raise RuntimeError("Unlock phone and keep Chat checks in the foreground")
        return result

    def tap(node):
        left, top, right, bottom = map(int, re.findall(r"\d+", node["bounds"]))
        command("shell", "input", "tap", str((left + right) // 2), str((top + bottom) // 2))

    def button(ns, label):
        return next(
            n for n in ns if n.get("class") == "android.widget.Button" and n["text"] == label
        )

    def status(ns):
        return [n["text"] for n in ns if n.get("class") == "android.widget.TextView"][-1]

    def enter(index, text):
        tap([n for n in nodes() if n.get("class") == "android.widget.EditText"][index])
        time.sleep(1)
        command("shell", "input", "keyevent", "KEYCODE_MOVE_END")
        command("shell", "input", "keyevent", *("67" for _ in range(100)))
        command("shell", "input", "text", text.replace(" ", "%s"))
        time.sleep(1)
        # Keep the keyboard open. Back can close the Activity when the OEM's
        # reported IME visibility is stale; adjustResize keeps buttons reachable.

    def wait_reply(expected):
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            ns = nodes()
            if status(ns) != "Thinking…":
                assert status(ns) == expected, status(ns)
                assert button(ns, "Send message")["enabled"] == "true"
                return ns
            time.sleep(1)
        raise AssertionError("request did not finish")

    def send(text, expected="Reply received • ready"):
        enter(1, text)
        tap(button(nodes(), "Send message"))
        return wait_reply(expected)

    checks = []
    try:
        # All endpoint/profile overrides are scoped to this fixture; no app source changes.
        with patch("anpyra.android.chat.ENDPOINT", f"http://127.0.0.1:{port}/v1/responses"):
            result = build_project(Project(root, replace(project.config, target_sdk=27)))
        command("reverse", f"tcp:{port}", f"tcp:{port}")
        command("install", "-r", str(result.apk_path))
        command("shell", "am", "force-stop", package)
        command("shell", "am", "start", "-W", "-n", package + "/.MainActivity")
        time.sleep(2)
        tap(button(nodes(), "Send message"))
        assert status(nodes()) == "Enter your temporary API key above."
        checks.append("missing_key")
        enter(0, "fixture-key")
        assert [n for n in nodes() if n.get("class") == "android.widget.EditText"][0][
            "input_masked"
        ]
        checks.append("password_masking")
        tap(button(nodes(), "Send message"))
        assert status(nodes()) == "Type a message first."
        checks.append("missing_message")
        enter(1, "My name is Babar.")
        tap(button(nodes(), "Send message"))
        ns = nodes()
        assert status(ns) == "Thinking…", status(ns)
        assert all(
            n["enabled"] == "false"
            for n in ns
            if n.get("class") in {"android.widget.EditText", "android.widget.Button"}
        )
        tap(button(ns, "Send message"))
        release_first.set()
        ns = wait_reply("Reply received • ready")
        assert (
            next(n for n in ns if n.get("class") == "android.widget.ScrollView")["scrollable"]
            == "true"
        )
        checks.append("scrollable_long_content")
        assert len(requests) == 1
        checks.extend(("busy_guard", "native_worker_and_delivery", "long_response"))
        (root / "reply.png").write_bytes(
            subprocess.check_output(adb + ["exec-out", "screencap", "-p"])
        )
        send("What is my name?")
        assert requests[1]["input"][1] == reasoning
        assert requests[1]["input"][2]["content"][0]["text"].startswith("Hello Babar!")
        checks.append("complete_output_history")
        send("quota fixture", "Rate limit or quota reached. Please try again later.")
        send("bad JSON fixture", "Network request failed. Check internet and try again.")
        send("incomplete fixture", "Response was incomplete. Try a shorter message.")
        assert requests[2]["input"][:-1] == requests[3]["input"][:-1] == requests[4]["input"][:-1]
        checks.extend(("quota_recovery", "malformed_response_recovery", "incomplete_not_committed"))
        ns = send("Refusal fixture")
        assert (
            "I cannot help with that request."
            in [n["text"] for n in ns if n.get("class") == "android.widget.TextView"][-2]
        )
        checks.append("refusal_rendering")
        tap(button(nodes(), "New chat"))
        assert status(nodes()) == "New chat started. Your key stays on this screen."
        send("Fresh chat")
        assert len(requests[-1]["input"]) == 1
        assert all(r["model"] == "gpt-5.5" and r["store"] is False for r in requests)
        assert all(r["include"] == ["reasoning.encrypted_content"] for r in requests)
        checks.append("new_chat_reset")
        report = {
            "model": command("shell", "getprop", "ro.product.model").strip(),
            "api": command("shell", "getprop", "ro.build.version.sdk").strip(),
            "fixture_requests": len(requests),
            "checks": checks,
            "scope": "Controlled responses; no live OpenAI key or AI answer",
        }
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Chat device checks passed: {len(checks)}; {root}", flush=True)
    finally:
        release_first.set()
        # Only synthetic prompts and fixture output items are recorded; never headers.
        (root / "fixture-requests.json").write_text(
            json.dumps(requests, indent=2) + "\n", encoding="utf-8"
        )
        try:
            command("reverse", "--remove", f"tcp:{port}")
        except subprocess.CalledProcessError:
            pass  # A disconnected device must not skip host server cleanup.
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
