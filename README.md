<p align="center">
  <img src="assets/social-preview.png" alt="FrostByte" width="180">
  <br><br>
  <b>Your idle apps are wasting gigabytes of RAM.<br>FrostByte fixes that.</b>
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GNOME-45_|_46_|_47-4a86cf.svg?style=for-the-badge&logo=gnome&logoColor=white" alt="GNOME Shell">
  <img src="https://img.shields.io/badge/Wayland-native-green.svg?style=for-the-badge&logo=wayland&logoColor=white" alt="Wayland">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen.svg?style=for-the-badge" alt="Zero deps">
</p>

<p align="center">
  <img src="assets/demo.gif" alt="FrostByte TUI Demo" width="900">
</p>

---

## The Problem

Modern apps are hungry. Firefox, Slack, VS Code, Spotify sit on **4+ GB of RAM** while you're not looking at them. Linux won't reclaim pages that apps are technically "using" just by being alive.

## The Solution

**FrostByte** puts idle apps into cold storage:

1. **Freeze** — Idle apps above a RAM threshold get `SIGSTOP`. The OS instantly reclaims their physical memory.
2. **Thaw** — Focus or click a frozen window → the GNOME extension fires `SIGCONT`. **Instant. Transparent.**

> Your system stays snappy, swap stays empty, battery lasts longer. ❄️

---

## Features

| | |
|---|---|
| **🚀 Instant Wake-up** | Zero-latency thawing via native GNOME Shell extension |
| **📊 Gorgeous TUI** | Real-time dashboard — frozen apps, candidates, RAM saved |
| **🛡️ Smart Thawing** | Wakes entire process trees (children first) to prevent IPC races |
| **🧊 Auto-Freeze** | Scans `/proc` for RAM-heavy apps idle beyond threshold |
| **🖱️ Mouse-Friendly** | Click frozen windows to thaw, even without focus |
| **🧩 Panel Indicator** | GNOME top bar menu with live frozen count |
| **🌐 Bilingual** | English / Russian — toggle with `L` |
| **⚙️ Zero Dependencies** | Pure Python, works out of the box |

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main/install.sh | bash
```

One command. Installs the daemon, GNOME extension, and systemd service.

<details>
<summary><b>Install from source</b></summary>

```bash
git clone https://github.com/VladislavTsytrikov/frostbyte.git
cd frostbyte
bash install.sh
```
</details>

---

## Live Monitor

```bash
frostbyte monitor
```

| Key | Action |
|-----|--------|
| `↑` `↓` / scroll | Navigate processes |
| `Enter` | Freeze / Thaw selected |
| `e` | Exclude from auto-freezing |
| `f` / `t` | Quick-search freeze / thaw by name |
| `Tab` | Switch tab: Frozen → Candidates → Exclusions |
| `L` | Toggle language (EN / RU) |
| `q` | Quit |

---

## Configuration

`~/.config/frostbyte/config.json`

```json
{
  "freeze_after_minutes": 30,
  "min_rss_mb": 150,
  "poll_interval": 1,
  "scan_interval": 30,
  "max_freeze_hours": 4,
  "whitelist": ["gnome-shell", "pipewire", "spotify", "..."]
}
```

| Option | Description |
|--------|-------------|
| `freeze_after_minutes` | Idle time before auto-freeze |
| `min_rss_mb` | Minimum RSS to consider freezing |
| `max_freeze_hours` | Auto-thaw after this many hours |
| `whitelist` | Never freeze these processes |

---

## Alternatives

| | **FrostByte** | Nyrna | XSuspender |
|---|:---:|:---:|:---:|
| Wayland | ✅ | ❌ | ❌ |
| GNOME integration | ✅ | ✅ | ✅ |
| Auto-freeze (RAM aware) | ✅ | ❌ | ❌ |
| Instant thaw on focus | ✅ | ❌ | ✅ |
| Zero dependencies | ✅ | ❌ | ✅ |
| TUI dashboard | ✅ | ❌ | ❌ |

---

## License

[MIT](LICENSE)
