# OmaGrid upstream and behavioral compatibility policy

## Baseline

- Upstream: https://github.com/storytold/gridcraft
- Fork: https://github.com/ustaaa/omagrid
- Initial release: v0.13.0
- Initial commit: `43284377d2466037628e57d8ad0c891778fdb45c`
- Development branch: `codex/omarchy-ui`
- Rust minimum: 1.95 (record the actual compiler with every comparison)
- egui pin: `6d518fc799681571963842f95b55a6b68431b15a`
- winit pin: `a517b3846ee8457d84ee4975110bfda6797c44dc`
- craft-libs pin: `92d392cff132eaf53e13afff77f38b5c11b73aa0`

`origin` is the OmaGrid fork; `upstream` is the original repository. Existing read-only monitoring clones under `Development/upstream/` are never used as development checkouts.

## Patch boundary

No product changes in `core`, `numfmt`, `formula`, `functions`, `model`, `calc`, `xlsx`, `chart`, `pdf` or `engine`. Linux integration belongs in the host or frontend; control-token namespace isolation belongs in the L6 MCP adapter. Existing command IDs and parameter shapes are retained.

Keep ribbon layout, groups, keytips, selection/editing, undo and clipboard behavior. Windows desktop Excel is the intended behavioral reference. A matching GridCraft/OmaGrid test is evidence of no downstream regression, not proof of Excel parity. Record observed Excel differences separately, with the exact Excel version and reproducible synthetic input. Do not copy vendor assets, source, templates or private workbooks into this repo.

Appearance affects application chrome and interaction affordances only. Workbook styles, document fonts, chart palettes, file serialization, print and PDF content remain unchanged. Theme changes must not alter the document revision, undo history or dirty state.

## Upgrade procedure

1. Preserve baseline reports and original corpus hashes. Keep a clean upstream-only checkout and a separate downstream checkout.
2. Resolve a candidate release to an exact commit; do not implicitly absorb moving main or change dependency pins independently.
3. Inspect the upstream diff and dependency changes. Use the read-only merge preview in `tools/omarchy-validation` before an actual integration.
4. Integrate on a separate branch, preserving the working branch and unrelated changes. The user authorized Codex to review, commit and push OmaGrid directly on 2026-10-29; no Nomura prerequisite applies to this project. OmarchyMax's `~/Development/omagrid` is the primary development checkout.
5. Build upstream-only and downstream candidates using the same toolchain, dependency lock, fonts, profile and target machine. Run CI, behavioral/corpus comparison and desktop acceptance.
6. Distinguish an upstream regression from a downstream regression. Do not publish a candidate with unresolved data-loss or core workflow failures.
7. Record the accepted base SHA, changed pins, actual results and remaining limitations in the handoff. Retain the previous package for rollback.

Do not automatically update user installations or push a branch named `release`. Fork publication workflows must remain non-publishing until fork-owned release infrastructure is explicitly established.

## Identity

- Display name: OmaGrid
- Executables: `omagrid`, `omagrid-cli`
- Linux app/desktop ID: `io.github.ustaaa.OmaGrid`
- XDG config namespace: `omagrid`
- Updates: package-managed; no upstream direct self-update

MIME types describe formats; they are not renamed. Installing a development package must not change the user's default file handlers or overwrite GridCraft settings/binaries. Internal Cargo package names and compatible command schemas intentionally retain GridCraft naming.

## Environment findings (2026-10-29)

- UrazStudio: macOS arm64 authoring checkout at `/Users/irtek/Development/omagrid`.
- OmarchyMax: Linux aarch64, Omarchy `4.0.0.r7218.gbe54892-1`, Hyprland 0.56.2, 5120x2160 at scale 2. Active palette `urazhalo-dusk-golden-gate`; fontconfig monospace resolves JetBrainsMono Nerd Font. Previously installed GridCraft is 0.10.0; leave it intact.
- UrazHalo: Linux x86_64, Ubuntu 26.04.1, GNOME Shell 50.1 installed. A GNOME graphical user session was not active during planning; do not report it as runtime-tested without a real session.
- Upstream's `plan/` instructions are untracked and not present in the public clone. The referenced `storytold/craftrules/AGENTS.md` returned 404 through both the connector and authenticated GitHub CLI. In-repo `AGENTS.md`, workspace guidance and explicit user instructions remain available.
