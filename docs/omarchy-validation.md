# OmaGrid validation and upstream updates

The first release preserves GridCraft's engine and file-format code. Passing these checks means the selected fork changes have not introduced a detected regression; it does not establish Excel replacement or lossless support for arbitrary workbooks.

Baseline: upstream `storytold/gridcraft`, release `v0.13.0`, commit `43284377d2466037628e57d8ad0c891778fdb45c`. Keep this exact revision and the fork revision in every validation record. A moving `main` branch is not a reproducible baseline.

## Reproducible synthetic corpus

`tools/omarchy-validation/manifest.json` defines three tiny synthetic workbooks using existing engine commands: calculation dependencies plus undo/redo, cross-sheet references, and literal text plus formatting/merges/frozen panes. No workbook binary is checked in. The upstream executable creates the inputs once; both executables open the same immutable inputs, apply identical edits, save to separate outputs, reopen, and inspect them.

Build the baseline in a separate checkout of the exact SHA. Build the fork with the same Rust toolchain/profile and features. Keep separate Cargo target directories. The workspace package names remain `gridcraft-cli`; the fork executable is `omagrid-cli`.

```sh
# In each respective checkout; use distinct absolute CARGO_TARGET_DIR paths.
cargo build --locked --release -p gridcraft-cli

# From the fork. The output directory must not exist; use a fresh path per run.
python3 tools/omarchy-validation/corpus.py \
  --upstream /absolute/upstream-target/release/gridcraft-cli \
  --fork /absolute/fork-target/release/omagrid-cli \
  --output /tmp/omagrid-corpus-run-001

# Gate fault-injection tests, no Rust build needed.
python3 -B -m unittest discover -s tools/omarchy-validation -p 'test_*.py'
```

The output retains CLI stdout/stderr, generated command scripts, raw checker reports, normalized comparisons, input hashes, executable hashes and versions, and a copied manifest. Executable hashes identify the tested artifacts; they cannot prove which source produced them. Record build commands, source SHA, `git status --porcelain`, Rust version, platform and features separately. The manifest's base SHA is a declared baseline, not automatic executable attestation.

The gate requires `gridcraft-check/1`, successful open, zero warnings, zero `noOracle`, stale caches, volatile skips, Boolean coercions and mismatches, and exactly the expected number of checked/matched formula cells. It checks each round-trip category, checks known numeric/text results independently, and compares the upstream/fork observations including cell styles and workbook metadata. Only filesystem paths are normalized; ZIP bytes are not compared. Existing output directories are never reused. A failure preserves evidence and exits nonzero; there is no broad warning allowlist or automatic baseline update.

These cached values originate from GridCraft itself. Matching them is a regression test, not an independent Excel calculation oracle. A broader release gate needs an external, pinned and SHA256-verified corpus stored outside this repository, with documented expected values and explicit unsupported-feature cases. Keep permitted originals read-only, save to copies, and investigate every new warning, missing cache or dropped-feature report. No user workbooks belong in public logs or commits.

## Appearance and engine gates

`crates/ui-egui/tests/omarchy_parity.rs` renders the same command sequence with and without injected dark/light palettes on Linux and Windows platform settings. It compares values, formula/style metadata, workbook state, undo history and ribbon selection. A separate contract test checks that paper/ink and sheet-control roles retain upstream values and removing the override restores the entire original token set. The injected palette replaces filesystem discovery for determinism; it does not test Linux watcher lifecycle or a real compositor.

```sh
cargo test --locked -p gridcraft-ui-egui --test omarchy_parity
cargo test --locked -p gridcraft-ui-egui --test it system_theme::
cargo test --locked -p gridcraft-engine --test it command_sequence_fuzz::
cargo xtask ci
```

Use the existing engine sequence-fuzz suite for structural edits, incremental/full-recalc agreement, save/reload and undo/redo invariants. An optional soak, after the ordinary gate passes:

```sh
GRIDCRAFT_FUZZ_SEEDS=200 GRIDCRAFT_FUZZ_STEPS=200 \
  cargo test --locked --release -p gridcraft-engine --test it command_sequence_fuzz::
```

Use `crates/engine/examples/perf.rs` and `write_perf.rs` for paired upstream/fork measurements with identical inputs, release builds, hardware and power state. Report raw timings and variance; a UI-only change should not claim a calculation-speed improvement. First-paint and live theme refresh latency require separate real desktop measurements.

## Release acceptance record

This document specifies gates; it is not evidence that they ran. Fill a dated run record with artifact paths and outcomes. Until recorded, every item below is **unverified**:

- Exact baseline/fork builds and the synthetic corpus pass; engine/XLSX production diff is empty.
- Full repository quality gates pass, including WASM and existing ribbon, keyboard, file-dialog and window tests.
- On the actual Omarchy machine: Wayland launch, dark/light switch while editing, fallback when theme files disappear or are malformed, live font change, 100/125/150/200% scaling, clipboard, IME, multiple windows, save/reopen, printing and PDF export.
- Native title/decorations, application ID, executable names, desktop/MIME metadata and config/control-token namespace identify OmaGrid and do not overwrite GridCraft settings. Test both installed applications together.
- Upstream release/update checks and installation actions are inert in the fork; release workflows do not publish automatically; downloaded artifacts cannot replace OmaGrid with upstream GridCraft.
- An accessibility review on real Linux assistive technology, contrast/focus checks, and a keyboard-only pass cover the actual UI. Headless accessibility-tree success alone is insufficient.
- A separately curated external-format corpus and warning review establish the supported workbook boundary. Advanced OOXML/passthrough, macros, external links and imported formats remain explicit risks.

The upstream checker is bounded: some round-trip categories compare counts rather than every property. OOXML passthrough can preserve selected opaque parts without updating references inside them after structural edits. Save success cannot by itself promise semantic preservation of arbitrary unsupported content. Keep v1 focused on appearance and identity, and treat changes to save/engine behavior as a separate reviewed project.

## Safe upstream merge rehearsal

Fetch a chosen upstream release through the normal reviewed workflow. Do not automatically track `main`. The default mode rehearses committed changes with an actual Git merge and therefore requires a clean source checkout:

```sh
python3 tools/omarchy-validation/rehearse_merge.py upstream/release \
  --repo /absolute/path/to/omagrid \
  --report /tmp/omagrid-merge-rehearsal-001.json
```

The default mode resolves the already-local candidate to a commit, refuses dirty source checkouts and existing reports, and imports only local history into a disposable repository. It performs `merge --no-commit --no-ff` there with hooks/signing/rerere disabled, records conflicts and exit status, then removes that temporary repository. Conflict blobs and logs remain beside the report in a `.evidence` directory. It never checks out the source directory, commits, pushes or updates source refs. A clean textual merge is only the first gate; it runs no tests.

To investigate an uncommitted fork without creating a temporary commit, explicitly select the working-tree snapshot mode:

```sh
python3 tools/omarchy-validation/rehearse_merge.py main \
  --candidate-source https://github.com/storytold/gridcraft.git \
  --include-working-tree \
  --repo /absolute/path/to/omagrid \
  --report /tmp/omagrid-dirty-rehearsal-001.json
```

This explicit source option fetches the requested revision only into the disposable repository. Snapshot mode captures the combined staged/unstaged tracked delta plus nonignored untracked files, including symlinks and modes. It checks that the files did not change during copying, retains the patch and untracked contents, and records the resulting tree ID. Generated ignored files such as build outputs are excluded. Source HEAD and index hashes must remain unchanged; optional Git index refresh writes are disabled.

Because no synthetic commit is created, this mode is a **three-way patch rehearsal**, not a full rename-aware Git merge. It classifies add/add and delete/modify conflicts from the base/fork/upstream trees, preserves their available base/ours/theirs blobs, excludes those unresolved paths, and applies the remaining complete upstream patch with `git apply --3way --index`. Any structural conflict or textual conflict makes the overall command fail, even if the remaining patch applied successfully. The report's `exitCode` is the underlying apply/merge exit code; `status` is the overall result. A no-change candidate is rejected in snapshot mode. A subsequent real reviewed merge may follow renames differently and must still run all gates.

After reviewing this report, the normal owner can perform the actual merge in an isolated reviewed branch. Audit identity/updater/packaging and theme adapter diffs first, then run the synthetic comparisons, appearance tests and full upstream gates against the new baseline. Update the manifest SHA only after the baseline is intentionally accepted. Retain previous reports so a newly unsupported workbook or warning cannot disappear through baseline replacement.

## Tooling smoke record — 2026-10-29

On the development Mac, the four Python gate fault-injection tests passed. Both scripts' `--help` paths worked. The rehearsal refused the dirty fork checkout without creating a report. A separate disposable checkout imported from the existing local Git history passed a clean `HEAD`-into-`HEAD` rehearsal and retained the same HEAD and clean status. No commits were created. This exercises safe plumbing only; a divergent/conflicting merge was not tested. Rust formatting was applied to the new integration-test file. Rust execution, real CLI corpus execution and the release acceptance items require separate recorded results.

## Actual CLI corpus record — 2026-10-29, UrazHalo

All three fixtures passed on UrazHalo (`Linux-7.0.0-38-generic-x86_64-with-glibc2.43`). Evidence is retained there at `/home/irtek/Development/omagrid/dist/validation/corpus-amd64-r2`; `provenance.json` identifies both executables and the manifest, and `result.json` records `passed` with `externalOracle: false`.

| Executable | Version | SHA256 |
| --- | --- | --- |
| Upstream | gridcraft-cli 0.13.0 | `25a750aea459f97a47e3e0ae48cb3f17c37539d0a767c1520a982e4e4b245d68` |
| Fork | omagrid-cli 0.13.0 | `86448a38c146dc92ef6bdd00d730dfc21e800c684ebb8c098df6a5fc3b9a36d8` |

Manifest SHA256: `a31c9e168002b6528b521b205628b978cfd470aba1a8a4d5f09473ed3d8096ad`. Executable hashes were unchanged at the end of the run. Each source and edited output passed both checkers with zero warnings, missing oracles, stale caches, volatile skips, mismatches and round-trip differences. Arithmetic-history checked/matched two formulas; cross-sheet and text-format-view each checked/matched one. Known values and normalized cell/workbook observations matched across binaries.

The initial run is retained at `dist/validation/corpus-amd64`. It correctly stopped at a fixture error: `range.setValues` with `parse: false` still treats leading `=` as a formula by design. The fixture now uses the existing `cell.set` apostrophe escape to enter literal `=literal`. This was a test-input correction; no engine behavior changed and no validation threshold was relaxed. The real Linux GUI, external Excel oracle and broader release gates remain separate from this CLI result.

## Divergent upstream integration record — 2026-10-29

An actual working-tree snapshot was rehearsed against upstream `main` at `2ff751791b7e5f3454f1cbd8bf87f04fac9d8649`, which contains 234 commits and changes 80 paths beyond the pinned v0.13.0 base. The result is **CONFLICT**, not integration success. Source HEAD and index remained unchanged. No commit, push, engine edit or integrated build occurred.

Evidence is archived in the development checkout's ignored `dist/validation/upstream-main-rehearsal/`: `report.json`, the upstream and fork patches, untracked fork source, conflict blobs and application logs. The report retains its original temporary evidence location; the complete retained directory is archived alongside it as `evidence/`. Fork snapshot tree: `6ab39397dee9f22c1826931b8053e4d99422cd09`; tracked patch SHA256: `0dfb2a424ea84d4c61b3173675d1132b88490c54e6021276822e9fd703c169a1`.

| Unresolved path | Observed conflict | Required integration decision |
| --- | --- | --- |
| `crates/ui-egui/src/dialogs/macros.rs` | Fork modifies display wording; upstream deletes the old dialog while adding macro UI/editor and engine/model execution code. | Review the replacement macro behavior as a separate capability change. When accepting it, port OmaGrid wording to the replacement UI and remove the obsolete dialog rather than retaining two flows. |
| `packaging/linux/flatpak/ai.storyteller.gridcraft.bundle.yml` | Fork deletes/replaces this manifest; upstream adds `--share=network` specifically for GitHub update checks. | Keep the OmaGrid manifest/identity and installation-managed update policy. Do not recreate the old manifest or import this permission merely to resolve the conflict. |
| `packaging/linux/flatpak/ai.storyteller.gridcraft.yml` | Same delete/modify conflict and network-permission addition in the source-build manifest. | Apply the same explicit OmaGrid packaging decision; independently assess any future network need. |

With those three structural conflicts explicitly excluded and still marked unresolved, the remaining upstream patch applied without textual conflict stages. That does **not** validate behavior or compilation. In particular, the new macro execution stack is beyond an appearance-only release and needs its own review, tests and user-facing policy before changing the accepted baseline. Keep v0.13.0 as the current base until this separate integration work is approved and verified.
