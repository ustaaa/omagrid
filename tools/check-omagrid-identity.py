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

def validate_workflows(workflow_dir):
    expected = {"ci.yml", "macos-check.yml"}
    actual = {path.name for path in workflow_dir.glob("*.y*ml")}
    problems = [f"Unexpected active workflow: {name}" for name in sorted(actual - expected)]
    for name in sorted(expected - actual):
        problems.append(f"Missing required workflow: {name}")
    if actual != expected:
        return problems

    texts = {name: (workflow_dir / name).read_text() for name in expected}
    for name, text in texts.items():
        for action in re.findall(r"uses: ([^\s#]+)", text):
            if not re.fullmatch(r"[^@]+@[0-9a-f]{40}", action):
                problems.append(f"Unpinned action in {name}: {action}")

    def contents_read_only(text):
        match = re.search(r"(?ms)^permissions:\s*\n(.*?)(?=^jobs:)", text)
        if not match:
            return False
        permissions = [line.strip() for line in match.group(1).splitlines() if line.strip()]
        return permissions == ["contents: read"]

    ci = re.sub(r"(?m)#.*$", "", texts["ci.yml"])
    triggers = re.search(r"(?ms)^on:\s*\n(.*?)(?=^permissions:)", ci)
    if not triggers:
        problems.append("ci.yml must declare explicit workflow triggers")
    else:
        names = set(re.findall(r"^  ([A-Za-z_]+):", triggers.group(1), re.M))
        if names != {"push", "pull_request", "workflow_dispatch"}:
            problems.append("ci.yml triggers must be push, pull_request and workflow_dispatch only")
        if not re.search(r"(?m)^    branches:\s*\[\s*main\s*,\s*pilot\s*\]\s*$", triggers.group(1)):
            problems.append("ci.yml push branches must be exactly main and pilot")
    if not contents_read_only(ci):
        problems.append("ci.yml must use read-only contents permission")
    if re.search(r"(?im)^  [A-Za-z0-9_-]*(?:release|publish|upload|sign)[A-Za-z0-9_-]*:", ci):
        problems.append("ci.yml must not define release, upload, signing or publishing jobs")
    if re.search(r"(?i)(actions/upload-artifact|gh release|cargo publish|codesign|notarytool|create-dmg)", ci):
        problems.append("ci.yml must not upload, sign or publish release artifacts")

    mac = re.sub(r"(?m)#.*$", "", texts["macos-check.yml"])
    mac = re.sub(r"--release\b", "", mac)  # Cargo optimization profile, not a product release route.
    mac_triggers = re.search(r"(?ms)^on:\s*\n(.*?)(?=^permissions:)", mac)
    if not mac_triggers or set(re.findall(r"^  ([A-Za-z_]+):", mac_triggers.group(1), re.M)) != {"workflow_dispatch"}:
        problems.append("macos-check.yml must be manual-only (workflow_dispatch)")
    if not contents_read_only(mac):
        problems.append("macos-check.yml must use read-only contents permission")
    if re.search(r"(?i)release|upload|sign|publish|notary|codesign|create-dmg", mac):
        problems.append("macos-check.yml must only compile; release/upload/sign/publish routes are forbidden")
    return problems

main = read("apps/gridcraft/src/main.rs")
updates = read("crates/ui-egui/src/updates_ui.rs")
require("self_update::finish" not in main and ".start_update_check(" not in main, "Desktop updater route re-enabled")
require("craft_update" not in updates and "Updater" not in updates, "Development UI must not instantiate an updater")
require(' -u ' not in read("packaging/linux/package.sh"), "Development AppImage must not embed an update endpoint")
errors.extend(validate_workflows(ROOT / ".github/workflows"))
require(read("NOTICE").strip() != "", "Preserve upstream NOTICE")
if errors:
    raise SystemExit("OmaGrid identity check failed:\n- " + "\n- ".join(errors))
print("OmaGrid identity checks passed: binary, window, Linux metadata, icons, Flatpak and update/release isolation")
