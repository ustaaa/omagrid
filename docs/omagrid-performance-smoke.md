# OmaGrid / upstream native Wayland performance smoke

Measured on OmarchyMax, 2026-10-29. This is a small operational comparison in the running desktop session, not a controlled benchmark or a physical input-latency measurement.

Both applications used release builds, the same pinned embedded font pack (`storytold/craft-fonts` commit `b076417b5880bd4154bd22f00695b1d28c6bea83`) and the original `--sample sales` workbook. The upstream baseline was exactly GridCraft v0.13.0, commit `43284377d2466037628e57d8ad0c891778fdb45c`. Its GUI was rebuilt with `cargo build --locked --release -j2 -p gridcraft`, `CRAFT_FONTS_DIR` pointing to that checkout and `CRAFT_FONTS_REQUIRED=1` before measurement. OmaGrid used the final tested ARM64 release binary. The binaries' SHA-256 hashes are recorded in each raw run.

Three sequential pairs alternated order: upstream/fork, fork/upstream, upstream/fork. Each process received fresh temporary XDG config, state, cache and data directories. Only `colors.toml` and an existing `light.mode` marker were copied from the live theme into its temporary state. Both applications explicitly selected System appearance after becoming control-ready. Upstream therefore retained its original interface fonts/palette, while OmaGrid used the Omarchy palette and JetBrainsMono Nerd Font; this is the intended product difference, not an identical-font rendering experiment.

All six windows were verified through Hyprland as mapped, visible, native Wayland (`xwayland: false`) at the same 433 × 512 logical size (866 × 1024 screenshot pixels). The desktop chose this tiled size. The installed user window remained running separately on port 18794. Only owned test processes on ports 18795/18796 were stopped; neither user theme nor clipboard was changed.

| Measurement | GridCraft baseline | OmaGrid |
|---|---:|---:|
| Control-ready, median (range), ms | 90.7 (90.4–111.4) | 117.2 (85.0–137.8) |
| Spawn to first completed screenshot, median (range), ms | 393.8 (364.7–403.4) | 413.2 (406.0–416.2) |
| Screenshot request round-trip, median, ms | 245.4 | 252.1 |
| RSS after idle, median (range), MiB | 179.8 (173.9–180.0) | 183.3 (180.1–184.4) |
| CPU ticks accumulated during each 10-second idle sample | 0 / 0 / 0 | 0 / 0 / 0 |
| `cell.set` control round-trip, pooled median / p95, ms | 48.6 / 74.4 | 50.4 / 74.0 |

Control-ready means a successful authenticated `ui.inspect` reply, not first visible paint. The screenshot metric includes capture settling, rendering, PNG encoding and writing a file. Each idle interval followed a three-second settling period; CPU uses `/proc/PID/stat` user+system ticks, normalized to one core, and RSS uses `/proc/PID/status`. Zero observed ticks means below the accounting resolution during this sample, not zero background work. Each run then performed 30 sequential localhost `cell.set` operations on Z1; all six final reads returned numeric 29. Command timing includes control transport, event scheduling and command execution; it is neither pure calculation speed nor physical keyboard latency.

The small sample shows a functioning low-idle-cost appearance adapter with approximately 3.5 MiB higher median RSS and 19.4 ms higher median time to a completed screenshot here. It cannot establish a statistically reliable speed difference. OS page caches were not flushed, the running desktop and power state were not controlled, and only one small workbook and window size were used. Large workbooks, sustained interaction, physical input-to-photon latency, live theme-switch frame timing and controlled power measurements remain unmeasured.

Raw JSON (all timings), six screenshots, process logs and the exact Python runner are available locally under `dist/validation/perf-arm64/`; the aggregate is `results.json` and the runner is `smoke.py`. The copied palette hash was `00aed8ea9c5850f68706cd072b6a757bd71df83743dc48d8b1bc5056e45e6c88`, matching the untouched live theme after testing. Host: Linux `7.3.0-3-omarchy`, aarch64, six Apple CPU cores. The user process PID 315981 and its port 18794 were verified still present after all test processes exited.
