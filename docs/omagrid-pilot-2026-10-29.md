# OmaGrid pilot validation — 2026-10-29

This is a tested development pilot, not complete Excel or desktop acceptance.
Source: v0.13.0 (`43284377d2466037628e57d8ad0c891778fdb45c`) plus the
`codex/omarchy-ui` implementation. Tests and packages were produced before the initial
implementation commit; retained source manifests and package/CLI hashes identify those artifacts.
No engine, calculation, model, XLSX, chart or PDF production crate changed.

## Results

| Gate | Observed result |
| --- | --- |
| Untouched baseline full CI | PASS, all 10 steps on UrazHalo |
| Final fork full CI | PASS, all 10 steps on UrazHalo |
| Native release build | PASS on x86_64 UrazHalo and ARM64 OmarchyMax |
| Synthetic CLI corpus | 3/3 on each architecture; zero warnings, missing oracles, mismatches or round-trip differences |
| Command/MCP compatibility | 355 command metadata entries identical; protocol/capabilities/stable server name retained |
| Real Omarchy Wayland | PASS launch, app ID and compositor `xwayland: false` |
| Installed launcher | PASS desktop entry validation, launch and separate app identity |
| X11 fallback | PASS launcher opened under XWayland; not a full backend acceptance test |
| Live palette while editing | PASS draft retained, exact document inspection/undo/dirty data unchanged |
| Missing/invalid palette | PASS last-good appearance retained; captured top chrome pixels identical |
| Live fontconfig refresh | PASS JetBrainsMono → Liberation Sans in isolated config; document metadata unchanged |
| Formulas and history | PASS formula commit, undo/redo, bold, Light/Dark/System, save/reopen on live native window |
| Upstream main rehearsal | Three structural conflicts; no integrated candidate build or tests |
| Paired ARM64 performance smoke | Three native Wayland pairs; see [method and raw-result summary](omagrid-performance-smoke.md) |
| Windows Excel / GNOME desktop | Not performed |

Native UI actions used the authenticated control API on actual rendered windows. They
do not substitute for physical keyboard, IME, assistive technology or external clipboard tests.
Only synthetic sample files were used. Global Omarchy theme/font settings were not modified.

OmarchyMax: aarch64, Omarchy `4.0.0.r7218.gbe54892-1`, Hyprland 0.56.2,
5120×2160 monitor at scale 2, actual `urazhalo-dusk-golden-gate` theme, Rust 1.99.1.
UrazHalo: x86_64 Ubuntu 26.04.1 / glibc 2.43, Rust 1.98; no logged-in GNOME session.
These host-built packages target these systems, not older glibc distributions.
The committed CI recipe targets Ubuntu 24.04; that hosted workflow has not run for this fork yet.

## Appearance observations

The ribbon structure remains intact. Actual screenshots show gold/dark Omarchy chrome,
white worksheet paper and original document/chart font roles. A proportional UI font
changes the header's measured height slightly; screenshots are therefore not globally
pixel-identical across UI fonts. Document metadata and font-chain regression tests are
unchanged. Do not describe this as byte-identical document rasterization.

The native smoke test changed a copied theme under `/tmp/omagrid-final-smoke/state`;
the final installed window uses the real user theme. The initial isolated fontconfig
rule failed to override an already-resolved user alias; a corrected final rule produced
the verified font change. This was test setup, not an application failure.

## Retained local evidence

- `dist/validation/omagrid-baseline-ci-fonts.log`
- `dist/validation/omagrid-fork-ci-final.log`
- `dist/validation/amd64/` and `arm64/`: manifest, provenance, raw checker output, observations
- `dist/validation/native-arm64/`: screenshots, workbook inspection, smoke results
- `dist/validation/upstream-main-rehearsal/`: snapshot, base/candidate hashes and conflicts
- `dist/release/`: two native tarballs, each with all 13 pinned font-pack OFL notices

Final tarball SHA256:

| Architecture | SHA256 |
| --- | --- |
| aarch64 | `9e2e5a501396b16b909a0b176fed25a7d078af28b94034c98b892207dd40aeaf` |
| x86_64 | `bbf9d2a0192a893db0d0482070d6872e227fd58d430ae1a64a0eea81c7d96342` |

Remaining gates: real Windows Excel/versioned external corpus, GNOME session, file portals,
clipboard between applications, drag-and-drop, physical Turkish keyboard/AltGr/IME,
screen reader, full scale matrix, multi-window stress and physical latency measurements.
The updater remains disabled. A later DPI follow-up changed the desktop launcher and
pilot installer to set `OMAGRID_WAYLAND=1`: the user-opened window had taken the XWayland
fallback at monitor scale 1.6 because `DISPLAY` was also available. The existing binary
already supports native selection, so no engine or executable change was required.
This launcher decision does not close the outstanding native integration gates above.
Direct terminal launches retain the original backend default; see README for explicit
native and X11 fallback commands. No public package-store release has occurred.

The updated desktop entry was launched with `gtk-launch` on OmarchyMax. Its new window
reported `xwayland: false`, while the user's existing Book1 window stayed open untouched.
At scale 1.6, UI inspection measured 786.25×646.875 logical pixels and the screenshot
measured 1258×1035 physical pixels, an exact 1.6 ratio. The before/after visual check
confirmed correct scaling. Evidence: `dist/validation/dpi-160/omagrid-dpi-before.png`
and `omagrid-dpi-after.png`. Installer regression tests also passed for a fresh install
and upgrade from a legacy desktop entry, including an installation path with spaces.

The limited performance smoke measured median first completed screenshot at 393.8 ms
(upstream) versus 413.2 ms (fork), and idle RSS at 179.8 versus 183.3 MiB. All six
10-second idle samples recorded zero CPU ticks. This is not a statistically reliable
speed comparison or physical input latency measurement.
