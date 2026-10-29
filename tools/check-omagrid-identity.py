#!/usr/bin/env python3
"""Check installable Linux identity and disabled development release/update routes.

Uses only Python 3.11+ standard libraries. It does not build or install the app.
"""
import configparser
from pathlib import Path
import re
import struct
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
APP_ID = "io.github.ustaaa.OmaGrid"
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


def read(path):
    return (ROOT / path).read_text()


for package, binary in (("gridcraft", "omagrid"), ("gridcraft-cli", "omagrid-cli")):
    data = tomllib.loads(read(f"apps/{package}/Cargo.toml"))
    require(data["package"]["name"] == package, f"Keep internal Cargo package {package} upstream-compatible")
    require([item["name"] for item in data["bin"]] == [binary], f"Unexpected public binary in {package}")

linux = ROOT / "packaging/linux"
desktop = configparser.ConfigParser(interpolation=None)
desktop.optionxform = str
desktop.read(linux / f"{APP_ID}.desktop")
entry = desktop["Desktop Entry"]
for key, value in {"Name": "OmaGrid", "Exec": "env OMAGRID_WAYLAND=1 omagrid %F", "TryExec": "omagrid", "Icon": APP_ID, "StartupWMClass": APP_ID}.items():
    require(entry.get(key) == value, f"Desktop {key} must be {value}")

metadata = ET.fromstring((linux / f"{APP_ID}.metainfo.xml.in").read_text())
for path, value in {"id": APP_ID, "name": "OmaGrid", "launchable": f"{APP_ID}.desktop", "icon": APP_ID}.items():
    require(metadata.findtext(path) == value, f"AppStream {path} must be {value}")
require({item.text for item in metadata.findall("provides/binary")} == {"omagrid", "omagrid-cli"}, "AppStream binaries mismatch")
ET.parse(linux / f"{APP_ID}.mime.xml")
for size in (16, 24, 32, 48, 64, 128, 256, 512):
    asset = f"assets/omagrid-icon/{size}/{APP_ID}.png"
    data = (ROOT / asset).read_bytes()
    require(data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (size, size), f"Invalid icon: {asset}")
    require(asset in read("ATTRIBUTION.md"), f"Missing attribution: {asset}")
ET.parse(ROOT / f"assets/omagrid-icon/{APP_ID}.svg")
require(f".with_app_id(\"{APP_ID}\")" in read("apps/gridcraft/src/main.rs"), "Native window app ID mismatch")

# Deliberately simple line parsing for these flat, controlled YAML sections. No YAML dependency.
def field(text, key):
    return re.search(rf"^{re.escape(key)}: (.+)$", text, re.M).group(1)


def finish_args(text):
    section = text.split("finish-args:\n", 1)[1]
    section = re.split(r"^\S", section, maxsplit=1, flags=re.M)[0]
    return {line.strip()[2:] for line in section.splitlines() if line.strip().startswith("- ")}


manifests = [read(f"packaging/linux/flatpak/{APP_ID}{suffix}.yml") for suffix in ("", ".bundle")]
for manifest in manifests:
    require(field(manifest, "id") == APP_ID and field(manifest, "command") == "omagrid", "Flatpak identity mismatch")
    require("--share=network" not in finish_args(manifest), "Development Flatpak must not expose control/network by default")
require(finish_args(manifests[0]) == finish_args(manifests[1]), "Flatpak source/bundle permissions differ")
for key in ("runtime", "runtime-version", "sdk"):
    require(field(manifests[0], key) == field(manifests[1], key), f"Flatpak {key} differs")

main = read("apps/gridcraft/src/main.rs")
updates = read("crates/ui-egui/src/updates_ui.rs")
require("self_update::finish" not in main and ".start_update_check(" not in main, "Desktop updater route re-enabled")
require("craft_update" not in updates and "Updater" not in updates, "Development UI must not instantiate an updater")
require(' -u ' not in read("packaging/linux/package.sh"), "Development AppImage must not embed an update endpoint")
for workflow in (ROOT / ".github/workflows").glob("*.y*ml"):
    text = workflow.read_text()
    require(workflow.name == "ci.yml", f"Unexpected active workflow: {workflow.name}")
    require("  workflow_dispatch:" in text and "  pull_request:" in text, "Keep manual and pull-request quality checks")
    require(not re.search(r"^  (schedule|release|workflow_run):", text, re.M), "Unexpected scheduled or release trigger found")
    for action in re.findall(r"uses: ([^\s#]+)", text):
        require(bool(re.fullmatch(r"[^@]+@[0-9a-f]{40}", action)), f"Unpinned action: {action}")
require(read("NOTICE").strip() != "", "Preserve upstream NOTICE")
if errors:
    raise SystemExit("OmaGrid identity check failed:\n- " + "\n- ".join(errors))
print("OmaGrid identity checks passed: binary, window, Linux metadata, icons, Flatpak and update/release isolation")
