# OmaGrid handoff — 2026-10-29

## State and ownership

Implemented the first Omarchy appearance/identity pilot. Local source is
`~/Development/omagrid`, branch `codex/omarchy-ui`, based exactly on GridCraft
v0.13.0 / `43284377d2466037628e57d8ad0c891778fdb45c`.
`origin` is `https://github.com/ustaaa/omagrid`; `upstream` is the official repository.
The user explicitly authorized Codex to handle review/commits directly for OmaGrid,
removing the Nomura prerequisite, and selected OmarchyMax for continued development.
The implementation is recorded on `codex/omarchy-ui`; verify its HEAD and remote tracking
before continuing. Primary working directory: `/home/irtek/Development/omagrid` on
OmarchyMax. The Mac checkout is a secondary copy; avoid parallel edits on both hosts.

Read [the pilot record](docs/omagrid-pilot-2026-10-29.md),
[validation procedure](docs/omarchy-validation.md), and
[upstream policy](docs/omagrid-upstream.md) before continuing.

## Implemented

- Existing egui ribbon, command positions, editor and shortcuts retained. No GTK/Qt port.
- Omarchy v4 state path and v3 config path, live palette/fontconfig discovery, bounded
  data parsing, last-good fallback, manual Light/Dark and System behavior.
- Appearance snapshot shared by egui styles and theme tokens. Workbook font chains,
  chart/slicer text and header/footer document font roles isolated from chrome fonts.
- Live font changes defer during input/editing and preserve bound document fonts.
  Regression tests cover physical text events, IME/paste/Enter deferral and cached roles.
- Independent binaries, application ID, config/log/recovery/control-token namespaces,
  icon assets and Linux metadata. CLI/MCP command contracts retained.
- Official updater entry points disabled. No publishing workflow remains active.
- Native ARM64 and x86_64 tar packages; reversible user-local pilot installer.
- CLI corpus, appearance parity tests, identity checks and dirty-tree upstream rehearsal.
- Engine/model/calc/XLSX/chart/PDF production crates have zero changes from the base.

## Installed on OmarchyMax

Active pilot: `~/.local/share/omagrid/versions/pilot-20261029-v013-r2`.
`~/.local/share/omagrid/current` points there; binaries are under `~/.local/bin`.
Launcher: `~/.local/share/applications/io.github.ustaaa.OmaGrid.desktop`.
Existing `/usr/bin/gridcraft` and `/usr/bin/gridcraft-cli` remain separately installed.
No MIME default was assigned. Original pilot version is retained for recovery;
the r2 package adds all 13 pinned font-pack OFL notices (identical executable code).

The installed app was left open on a synthetic Sales sample with native Wayland,
control port 18794, using the actual user theme. This is a preview, not production acceptance.

```sh
~/.local/bin/omagrid                           # normal launcher behavior
OMAGRID_WAYLAND=1 ~/.local/bin/omagrid          # tested native Wayland opt-in
bash ~/Development/omagrid/packaging/linux/install-pilot.sh --uninstall
```

Uninstall removes only managed launcher links and retains version folders.
The default retains upstream X11 fallback when DISPLAY is set until portal,
clipboard and drag-and-drop gates pass. Both the desktop launcher/XWayland path
and explicit native Wayland path were launched successfully on OmarchyMax.

## Evidence and reproduction

Full `cargo xtask ci` passed for both untouched upstream and final fork on UrazHalo
with process umask 022 and pinned `craft-fonts` input. All 10 gates passed, including
WASM, tests, assets, layers, keytips and clippy. The default host umask 002 caused an
upstream permissions test failure; missing optional font assets caused two upstream
glyph tests to fail. These were environment fixes, not relaxed tests.

Font pin: `storytold/craft-fonts@b076417b5880bd4154bd22f00695b1d28c6bea83`.
On both Linux hosts: `~/Development/Codex/omagrid-craft-fonts`.
**Export CRAFT_FONTS_DIR for packaging too**, including `--skip-build`, to copy licenses.
See README for exact build commands.

Local ignored evidence is under `dist/validation/`; native packages under `dist/release/`.
Both hosts have separate baseline checkouts `~/Development/Codex/omagrid-baseline`
and task-owned fork copies `~/Development/omagrid`. Watched upstream clones were not edited.
UrazHalo targets: `~/.cache/omagrid-build/amd64` (baseline), `amd64-fork` (fork).
OmarchyMax target: `~/.cache/omagrid-build/arm64`; binary names distinguish baseline/fork.

## Next acceptance work

1. Continue on OmarchyMax's `codex/omarchy-ui`, fetching and verifying Git state first.
   Codex can review/commit this project's changes directly; preserve unrelated work.
2. Real Windows Excel reference/version and external workbook compatibility corpus.
   Current synthetic corpus is a regression oracle, not proof of Excel compatibility.
3. GNOME Wayland session on UrazHalo: GNOME is installed but no user graphical session
   was active. ARM64 Omarchy desktop testing does not cover this gate.
4. Native portal, external clipboard, file drag-and-drop, Turkish AltGr/IME,
   screen reader, multi-window and remaining scale-matrix acceptance.
5. Full performance/physical input acceptance; see any retained performance smoke
   [record](docs/omagrid-performance-smoke.md) for its deliberately limited scope.
   Three native Wayland pairs passed: median completed first PNG 393.8/413.2 ms and
   RSS 179.8/183.3 MiB (upstream/fork), zero ticks across six 10-second idle samples.
6. Upstream integration: rehearsal against main `2ff75179` found three structural
   conflicts. Do not auto-import its macro execution stack or updater network permission.
   No merged candidate build/tests have passed yet. Details in validation docs.

Do not start OmaWord/OmaDeck until the pilot and a reviewed upstream integration pass.
The referenced private/unavailable `craftrules` repository returned 404; local gitignored
`plan/` was absent. Follow available in-repo and workspace instructions, never invent
missing instructions. Halogen was used for a bounded review; findings were independently
checked. Three Codex subagents owned appearance, identity/packaging and validation.
