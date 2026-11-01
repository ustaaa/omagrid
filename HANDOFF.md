# OmaGrid engineering handoff

## Development lifecycle

OmaCraft coordinates exact revisions, independent reviews and cross-platform evidence at
https://github.com/ustaaa/omacraft. This repository keeps its own upstream history.
Use origin for the Oma fork and upstream for the original project. Work on a topic branch,
review the diff, run relevant gates, and open a draft pull request. Do not automatically
publish releases or overwrite another device's dirty checkout.

## Current pilot (2026-10-30)

Linux ARM64 and x86_64 pilot binaries have been built. Native Wayland launch and sample
rendering were checked at display scales 1.6 and 1.5 respectively. This is not full
keyboard, IME, clipboard, accessibility or document-compatibility certification.
The ribbon and command layout are retained. Appearance must not modify document state.
macOS build workflows are experimental and manual; no Oma macOS distribution is certified.

Full Linux quality gates passed during pilot preparation. Fresh synthetic corpus comparisons
passed for Grid (3 cases), Word (2) and Deck (2); Notes CLI smoke passed 20 checks.
A previous x86 Notes UI test process terminated with SIGSEGV at four test threads.
All 121 UI tests then passed serially and under a debugger; full serial CI passed.
The cause remains unresolved. Do not describe reruns as a fix or hide this risk.

## Next review

Review downstream identity, theme isolation, font reload, package/updater separation,
and the declared support matrix. Revalidate at the exact reviewed commit and record
compiler, target, commands, result, skipped checks and logs. Keep private machine paths,
notebooks, credentials and infrastructure inventory out of tracked reports.

### OmaCraft brand polish (2026-10-30)
Suite links and documentation now use ustaaa/omacraft. Original application icon
regenerated in the shared dark-tile/paper style, with a distinct application accent.
PNG/SVG/ICO structure (where applicable), deterministic regeneration and whitespace
checks passed. No engine, document, command, dependency or version changes.
Installed-app validation of these new assets is still pending; previous runtime
evidence does not cover this polish. Existing CI limitations remain open.

### Suite review follow-up (2026-10-31)
Linux launch policy is documented consistently: the pilot launcher uses native Wayland;
`OMAGRID_X11=1` forces X11, and `GRIDCRAFT_WAYLAND` remains a documented legacy alias.
Source/diff whitespace checks pass. Native clipboard/drop/portal runtime gates remain open.

### Candidate 2 review fixes (2026-10-31)
Theme root selection now promotes a valid preferred root even after the selected legacy
root disappears; invalid selected roots retain the last good palette and do not fall
back to lower-priority roots. HOME/.local/state is checked alongside custom
XDG_STATE_HOME with deduplication. X11 override accepts only `=1`. Focused Cargo tests
were blocked before compile by an unwritable shared Cargo git database; rustfmt passed.

### Upstream variable isolation by Claude (2026-10-31; branch claude/identity-env)
The control port, control token and no-preferences switch now read only
`OMAGRID_CONTROL_PORT`, `OMAGRID_CONTROL_TOKEN` and `OMAGRID_NO_PREFS`. The upstream
`GRIDCRAFT_` fallbacks are gone, so values exported for an upstream GridCraft install
cannot bind the same port, send its credential or switch off OmaGrid preferences.
`GRIDCRAFT_WAYLAND` stays as the documented backend alias. Unit tests prove upstream
names are ignored. Docs that describe driving OmaGrid now name the OmaGrid variables.

### Alpha version reporting (2026-11-01)
Downstream label `0.13.0-oma.1.alpha.1` is shown by GUI About/account and
`omagrid --version` / `omagrid-cli --version`; output names upstream GridCraft 0.13.0
separately. Linux packages use the downstream label and include `VERSION.txt` with both
versions. Cargo package versions and lockfile are unchanged. Rust builds/runtime and
package artifact verification are delegated to Halo; local formatting, shell syntax and
diff whitespace checks passed.

### GridCraft v0.14.2 integration candidate (2026-11-01)
Isolated branch `codex/upstream-grid-0.14.2` starts at OmaGrid alpha 1
`57822142c80bb6f3b08b8d5af0ca17107e963e58` and merges upstream tag `v0.14.2`,
resolved to `55850841d39f030fb42f0a07e54903decea7b067`. Downstream version label is
`0.14.2-oma.1.alpha.1`; suite tracking target is nextalpha2. The ribbon and Omarchy
chrome/theme/font paths and upstream isolation of control/auth variables remain in the
merged tree. Upstream adds macro authoring, workbook author metadata, drag/drop handling,
and CUPS print support. The old unused macros dialog was removed in favor of upstream's
new macro UI/editor.

Eight merge conflicts were resolved in AGENTS.md, Cargo.lock, apps/gridcraft/src/main.rs,
apps/gridcraft/tests/mac_menu_appkit.rs, crates/ui-egui/src/dialogs/macros.rs,
crates/ui-egui/src/updates_ui.rs and the two OmaGrid Flatpak manifests. Updater behavior
remains package-managed: no upstream startup check or binary replacement helper; the
existing manual command displays the OmaGrid policy notice. Removed the now-unused
craft-update workspace dependency and lock references. Flatpak manifests retain the Oma
application ID, Omarchy palette access and offline runtime policy; they include the new
CUPS tools/socket integration without `--share=network`.

`cargo fmt --all -- --check`, `git diff --check HEAD` and
`cargo metadata --no-deps --format-version 1 --offline` passed. Rust compilation,
component tests, package builds, and Halo runtime checks were not run here; root handles
the component gates. Cargo offline lock regeneration was unavailable because the local
crates.io index lacks `sha1`; the upstream lock was retained with the unused updater
package references removed. Local merge commit `23ee2555349695d71d3e94ee8e277fd2343a934d`
is ready for root review; it has not been pushed.
