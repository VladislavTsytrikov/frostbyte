<p align="center">
  <img src="assets/social-preview.png" alt="FrostByte" width="180">
  <br><br>
  <b>Your idle apps are wasting gigabytes of RAM.<br>FrostByte fixes that.</b>
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GNOME-45_|_46_|_47_|_48-4a86cf.svg?style=for-the-badge&logo=gnome&logoColor=white" alt="GNOME Shell">
  <img src="https://img.shields.io/badge/Wayland-native-green.svg?style=for-the-badge&logo=wayland&logoColor=white" alt="Wayland">
  <img src="https://img.shields.io/badge/single_file-zero_deps-brightgreen.svg?style=for-the-badge" alt="Zero deps">
</p>

<p align="center">
  <img src="assets/demo.gif" alt="FrostByte TUI Demo" width="900">
</p>

---

## The Problem

Modern apps are hungry. Firefox, Slack, VS Code, Spotify sit on **4+ GB of RAM** while you're not looking at them. Linux won't reclaim pages that apps are technically "using" just by being alive.

## The Solution

**FrostByte** puts idle apps into cold storage:

1. **Freeze** — Idle apps above a RAM threshold get `SIGSTOP`. The kernel instantly reclaims their physical pages.
2. **Thaw** — Focus or click a frozen window — the GNOME extension fires `SIGCONT`. **Instant. Transparent.**

> Your system stays snappy, swap stays empty, battery lasts longer. ❄️

---

## Features

| | |
|---|---|
| **Instant Wake-up** | Zero-latency thawing via native GNOME Shell extension |
| **Live TUI** | Real-time dashboard — frozen apps, candidates, RAM saved |
| **Smart Thawing** | Wakes entire process trees including child processes (TUI apps in terminals) |
| **Auto-Freeze** | Scans `/proc` for RAM-heavy apps idle beyond threshold |
| **Mouse-Friendly** | Click frozen windows to thaw, even without focus |
| **Panel Indicator** | GNOME top bar snowflake with live frozen count and quick-thaw menu |
| **Bilingual** | English / Russian — toggle with `L` |
| **Single File** | One Python script. No dependencies. Daemon + TUI + extension + installer |

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main/install.sh | bash
```

One command. Downloads the script, installs the daemon, GNOME extension, and systemd service.

<details>
<summary><b>Alternative: direct install</b></summary>

```bash
curl -fsSL https://github.com/VladislavTsytrikov/frostbyte/raw/main/frostbyte -o /tmp/frostbyte
python3 /tmp/frostbyte install
```

Or clone and run locally:

```bash
git clone https://github.com/VladislavTsytrikov/frostbyte.git
cd frostbyte
python3 frostbyte install
```
</details>

### Uninstall

```bash
frostbyte uninstall        # keeps config
frostbyte uninstall --purge  # removes everything
```

---

## Live Monitor

```bash
frostbyte monitor
```

| Key | Action |
|-----|--------|
| `Up` `Down` / scroll | Navigate processes |
| `Enter` | Freeze / Thaw selected |
| `e` | Exclude from auto-freezing |
| `f` / `t` | Quick-search freeze / thaw by name |
| `Tab` | Switch tab: Frozen / Candidates / Exclusions |
| `L` | Toggle language (EN / RU) |
| `q` | Quit |

---

## How It Works

FrostByte is a single Python script that bundles everything:

```
frostbyte (Python)
├── daemon        — scans /proc, sends SIGSTOP/SIGCONT
├── TUI monitor   — curses dashboard
├── GNOME ext     — embedded JS, tracks focused window PID
└── installer     — writes extension + systemd service from embedded resources
```

**Freeze cycle:** The daemon polls `/proc` every second, tracking CPU time per process. If a process with RSS above the threshold shows no CPU activity for N minutes, it gets `SIGSTOP`.

**Thaw cycle:** The GNOME Shell extension writes the focused window's PID to `/tmp/frostbyte-focus-$UID`. The daemon reads this file, finds the frozen ancestor *and* stopped descendants (for TUI apps inside terminals), and sends `SIGCONT`.

**Self-coupling:** The daemon auto-enables the extension on startup. The extension auto-starts the daemon via systemd if it's not running. They can't get out of sync.

---

## Configuration

`~/.config/frostbyte/config.json`

```json
{
  "freeze_after_minutes": 10,
  "min_rss_mb": 100,
  "scan_interval": 10,
  "whitelist": ["chrome", "spotify"]
}
```

| Option | Default | Description |
|--------|---------|-------------|
| `freeze_after_minutes` | `10` | Idle time before auto-freeze |
| `min_rss_mb` | `100` | Minimum RSS (MB) to consider freezing |
| `poll_interval` | `1` | Seconds between CPU polls |
| `scan_interval` | `10` | Seconds between full `/proc` scans |
| `max_freeze_hours` | `4` | Auto-thaw after this many hours |
| `whitelist` | `[]` | Extra process names to never freeze |

> **Note:** FrostByte ships with a built-in whitelist (gnome-shell, pipewire, terminals, systemd, etc.). Your `whitelist` entries are **merged** on top — you only need to add app-specific names.

---

## CLI

```
frostbyte run           # start daemon (foreground)
frostbyte monitor       # live TUI dashboard
frostbyte status        # show frozen & candidate processes
frostbyte freeze <name> # manually freeze by name
frostbyte thaw [name]   # thaw by name (or all)
frostbyte install       # install everything
frostbyte uninstall     # remove everything
```

---

## Alternatives

| | **FrostByte** | Nyrna | XSuspender |
|---|:---:|:---:|:---:|
| Wayland | **yes** | no | no |
| GNOME 45–48 | **yes** | yes | yes |
| Auto-freeze (RAM aware) | **yes** | no | no |
| Instant thaw on focus | **yes** | no | yes |
| Child process thawing | **yes** | no | no |
| Zero dependencies | **yes** | no | yes |
| TUI dashboard | **yes** | no | no |
| Single file install | **yes** | no | no |

---

## License

[MIT](LICENSE)
