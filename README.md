# OmaGrid

Part of [OmaCraft](https://github.com/ustaaa/omacraft) - a friendly fork of ArtCraft's GridCraft.


OmaGrid is a Linux desktop adaptation of [GridCraft](https://github.com/storytold/gridcraft), with an Omarchy-aware interface and the existing Excel-style ribbon and spreadsheet engine.

This is a development fork, based on GridCraft **v0.13.0** (`43284377d2466037628e57d8ad0c891778fdb45c`). It is not an ArtCraft product or an official Omarchy application. GridCraft remains alpha; neither complete Excel behavioral parity nor lossless support for arbitrary Excel files is claimed.

## What stays the same

- Ribbon tabs, groups, command positions, keytips, dialogs and keyboard behavior.
- Formula bar, Name Box, sheet tabs, grid editing and clipboard behavior.
- Engine, calculations, document models, file formats and command protocol.
- Workbook fonts, cell/chart colors, number formats and print/PDF content.

## What OmaGrid changes

- Desktop appearance follows Omarchy palettes, with standard system appearance outside Omarchy and manual light/dark overrides.
- Linux UI font integration; workbook fonts remain document-controlled.
- A separate application identity, settings and control-token namespace.
- Package-managed updates; the upstream self-updater cannot replace OmaGrid.

The Linux desktop launcher and pilot installer set `OMAGRID_WAYLAND=1`, allowing native Wayland on Omarchy/Hyprland so the compositor's display scale reaches the application directly. This avoids the existing binary's forced X11 fallback when Hyprland also provides `DISPLAY`. Direct shell launches retain upstream behavior; use `OMAGRID_WAYLAND=1 omagrid` for the same backend selection as the launcher, or `env -u OMAGRID_WAYLAND -u GRIDCRAFT_WAYLAND omagrid` for the X11 fallback when `DISPLAY` is available. On an X11-only desktop, the launcher still lets winit select X11. Native portal, external clipboard, physical input and file-drop acceptance remain separate gates.

## Develop

Rust 1.95 or newer is required. Cargo package and crate names deliberately remain upstream-compatible; the desktop and CLI executable names are `omagrid` and `omagrid-cli`.

Full acceptance tests and distributable builds use the same pinned [craft-fonts](https://github.com/storytold/craft-fonts) checkout as CI. From this repository, prepare a sibling checkout once, or point `CRAFT_FONTS_DIR` at an existing checkout of that exact revision:

```sh
git clone https://github.com/storytold/craft-fonts ../craft-fonts
git -C ../craft-fonts checkout --detach b076417b5880bd4154bd22f00695b1d28c6bea83
export CRAFT_FONTS_DIR="$(cd ../craft-fonts && pwd)"
export CRAFT_FONTS_REQUIRED=1
umask 022
cargo xtask ci
cargo build --locked --release -p gridcraft -p gridcraft-cli
packaging/linux/package.sh --skip-build --formats tar
./target/release/omagrid --sample sales
./target/release/omagrid-cli eval '=SUM(1,2,3)'
```

Keep both exports in the shell that runs **build and packaging**, including `--skip-build`. The binaries embed the selected fonts at build time; packaging separately reads `CRAFT_FONTS_DIR` to copy their `OFL-<family>.txt` licenses into `share/doc/omagrid/`. A command-scoped assignment on `cargo build` does not carry over to the subsequent packaging command. Re-export the same font directory if packaging in a fresh shell, and preserve any custom `CARGO_TARGET_DIR` too. Font-free developer builds remain possible, but are not the full acceptance configuration: glyph coverage tests depend on the pinned font pack.

Linux builds need the upstream Wayland/X11, fontconfig, GTK file-dialog and GPU development/runtime dependencies. The pinned storytold egui, winit and craft-libs forks must be available to Cargo. Do not replace them with stock releases as part of appearance work.

See [validation](docs/omarchy-validation.md), [upstream policy](docs/omagrid-upstream.md), and [session handoff](HANDOFF.md) for exact commands, test evidence and outstanding acceptance work. Historical upstream implementation documentation remains under `docs/`; feature claims must be checked against the pinned source and tests.

## License and attribution

Based on GridCraft by the ArtCraft team and its contributors. Code remains **MIT OR Apache-2.0**; see [MIT](LICENSE-MIT), [Apache-2.0](LICENSE-APACHE), [NOTICE](NOTICE), and [asset attribution](ATTRIBUTION.md). Third-party assets retain their individual terms. ArtCraft trademarks are not licensed as OmaGrid branding.

OmaWord and OmaDeck are future directions, not applications implemented by this repository.
