#!/usr/bin/env python3
"""Small, strict upstream/fork regression gate; Python standard library only."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_script(path, commands):
    path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in commands))


def invoke(binary, args, log):
    result = subprocess.run([str(binary), *map(str, args)], capture_output=True, text=True, timeout=120)
    log.with_suffix(".stdout").write_text(result.stdout)
    log.with_suffix(".stderr").write_text(result.stderr)
    require(result.returncode == 0, f"{log.name}: exit {result.returncode}; inspect retained logs")
    return result.stdout


def validate_report(report, formulas):
    """Exit zero alone is insufficient: upstream permits warnings/missing cached oracles."""
    require(report.get("schema") == "gridcraft-check/1", "unknown check schema")
    require(len(report["files"]) == 1, "expected exactly one workbook")
    item = report["files"][0]
    require(item["opened"] and item["error"] is None, "workbook did not open")
    require(item["warnings"] == [], f"open warnings: {item['warnings']}")
    calc = item["calc"]
    for key in ("noOracle", "staleCache", "volatile", "mismatched", "boolAsNumber"):
        require(calc[key] == 0, f"{key} is {calc[key]}, expected zero")
    for key in ("formulaCells", "checked", "matched"):
        require(calc[key] == formulas, f"{key} is {calc[key]}, expected {formulas}")
    require(calc["mismatches"] == [], "calculation mismatches")
    trip = item["roundTrip"]
    require(trip["error"] is None and trip["differing"] == [], "round-trip mismatch")
    require(bool(trip["categories"]), "missing round-trip categories")
    for name, category in trip["categories"].items():
        require(category["equal"] and category["diffs"] == 0, f"round-trip category {name} differs")
    normalized = copy.deepcopy(report)
    normalized["files"][0]["path"] = "<workbook>"
    return normalized


def observations(binary, path, fixture, directory):
    commands = [{"command": "sheet.read", "params": r["params"]} for r in fixture["reads"]]
    commands += [{"command": "cell.get", "params": {"cell": c}} for c in fixture["inspectCells"]]
    commands += [{"command": "document.inspect", "params": {}}]
    script = directory / "observe.jsonl"
    write_script(script, commands)
    output = invoke(binary, ["run", "--in", path, "--script", script], directory / "observe")
    rows = [json.loads(line) for line in output.splitlines() if line.strip()]
    require(len(rows) == len(commands), "missing command observations")
    for row, read in zip(rows, fixture["reads"]):
        require(row["command"] == "sheet.read", "unexpected observation order")
        require(row["result"]["values"] == read["values"], f"known-value assertion failed: {row}")
    # Only filesystem location is normalized. Title, formulas, styles and all other fields stay.
    require(rows[-1]["command"] == "document.inspect", "missing workbook metadata")
    rows[-1]["result"]["path"] = "<workbook>"
    write_json(directory / "observations.json", rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--fork", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new directory; never overwritten")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.json"))
    args = parser.parse_args()
    binaries = {"upstream": args.upstream.resolve(strict=True), "fork": args.fork.resolve(strict=True)}
    manifest = json.loads(args.manifest.read_text())
    require(manifest["schema"] == "omagrid-synthetic-corpus/1", "unknown manifest schema")
    args.output.mkdir(parents=True, exist_ok=False)
    root = args.output.resolve()
    provenance = {"manifestSha256": digest(args.manifest), "manifest": manifest, "binaries": {}}
    for name, binary in binaries.items():
        version = invoke(binary, ["--version"], root / f"{name}-version").strip()
        provenance["binaries"][name] = {"path": str(binary), "sha256": digest(binary), "version": version}
    write_json(root / "provenance.json", provenance)
    for fixture in manifest["fixtures"]:
        name = fixture["name"]
        require(name and all(c.isalnum() or c == "-" for c in name), "unsafe fixture name")
        directory = root / name
        directory.mkdir()
        source = directory / "source.xlsx"
        create = directory / "create.jsonl"
        edit = directory / "edit.jsonl"
        write_script(create, fixture["create"])
        write_script(edit, fixture["edit"])
        invoke(binaries["upstream"], ["run", "--script", create, "--out", source], directory / "generate")
        source.chmod(0o444)
        source_hash = digest(source)
        results = {}
        for variant, binary in binaries.items():
            dest = directory / variant
            dest.mkdir()
            original = json.loads(invoke(binary, ["check", source, "--json"], dest / "source-check"))
            original = validate_report(original, fixture["formulaCells"])
            output = dest / f"{name}.xlsx"
            invoke(binary, ["run", "--in", source, "--script", edit, "--out", output], dest / "edit")
            report = json.loads(invoke(binary, ["check", output, "--json"], dest / "result-check"))
            report = validate_report(report, fixture["formulaCells"])
            values = observations(binary, output, fixture, dest)
            results[variant] = {"sourceCheck": original, "resultCheck": report, "observations": values}
            write_json(dest / "normalized.json", results[variant])
        require(digest(source) == source_hash, "source workbook changed")
        write_json(directory / "input.json", {"sha256": source_hash})
        require(results["upstream"] == results["fork"], f"{name}: upstream/fork semantic difference")
    for name, binary in binaries.items():
        require(digest(binary) == provenance["binaries"][name]["sha256"], f"{name} executable changed during validation")
    write_json(root / "result.json", {"status": "passed", "fixtures": len(manifest["fixtures"]), "externalOracle": False})
    print(f"PASS: {len(manifest['fixtures'])} synthetic fixtures; evidence: {root}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
