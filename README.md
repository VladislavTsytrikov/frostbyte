<p align="center">
  <img src="assets/banner.svg" alt="FrostByte — auto-freeze idle apps, reclaim your RAM" width="100%">
</p>

<p align="center">
  <a href="https://github.com/VladislavTsytrikov/frostbyte/releases/latest"><img src="https://img.shields.io/github/v/release/VladislavTsytrikov/frostbyte?style=for-the-badge&color=00b4d8&label=release" alt="Release"></a>
  <a href="https://github.com/VladislavTsytrikov/frostbyte/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/VladislavTsytrikov/frostbyte/test.yml?style=for-the-badge&label=tests" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GNOME-45–48-4a86cf.svg?style=for-the-badge&logo=gnome&logoColor=white" alt="GNOME Shell">
  <img src="https://img.shields.io/badge/Wayland-native-green.svg?style=for-the-badge&logo=wayland&logoColor=white" alt="Wayland">
</p>

<p align="center">
  <a href="#install">Install</a> &bull;
  <a href="#live-monitor">Live Monitor</a> &bull;
  <a href="#how-it-works">How It Works</a> &bull;
  <a href="#configuration">Configuration</a> &bull;
  <a href="#cli">CLI</a>
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

> [!TIP]
> Your system stays snappy, swap stays empty, battery lasts longer.

---

## Features

<table>
<tr><td width="40"><b>&#9889;</b></td><td><b>Instant Wake-up</b></td><td>Zero-latency thawing via native GNOME Shell extension</td></tr>
<tr><td><b>&#9608;</b></td><td><b>Live TUI</b></td><td>Real-time dashboard — frozen apps, candidates, RAM saved</td></tr>
<tr><td><b>&#9851;</b></td><td><b>Smart Thaw</b></td><td>Wakes entire process trees including child processes (TUI apps in terminals)</td></tr>
<tr><td><b>&#10052;</b></td><td><b>Auto-Freeze</b></td><td>Scans <code>/proc</code> for RAM-heavy apps idle beyond threshold</td></tr>
<tr><td><b>&#127925;</b></td><td><b>Audio-Aware</b></td><td>Skips freezing apps that are currently playing audio</td></tr>
<tr><td><b>&#128203;</b></td><td><b>Per-App Rules</b></td><td>Regex patterns with custom freeze timeouts per application</td></tr>
<tr><td><b>&#128276;</b></td><td><b>Notifications</b></td><td>Desktop notifications when apps are frozen or thawed</td></tr>
<tr><td><b>&#128260;</b></td><td><b>Hot Reload</b></td><td>Config changes apply instantly — no daemon restart needed</td></tr>
<tr><td><b>&#128433;</b></td><td><b>Mouse-Friendly</b></td><td>Click frozen windows to thaw, even without focus</td></tr>
<tr><td><b>&#9881;</b></td><td><b>Panel Indicator</b></td><td>GNOME top bar snowflake with live frozen count + quick-thaw menu</td></tr>
<tr><td><b>&#127760;</b></td><td><b>Bilingual</b></td><td>English / Russian — toggle with <code>L</code></td></tr>
<tr><td><b>&#128230;</b></td><td><b>Single File</b></td><td>One Python script. No deps. Daemon + TUI + extension + installer</td></tr>
</table>

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main/install.sh | bash
```

> [!NOTE]
> One command. Downloads a single Python script and runs `frostbyte install` which sets up the daemon, GNOME Shell extension, and systemd service.

<details>
<summary><b>Alternative methods</b></summary>

<br>

**Direct download:**
```bash
curl -fsSL https://github.com/VladislavTsytrikov/frostbyte/raw/main/frostbyte -o /tmp/frostbyte
python3 /tmp/frostbyte install
```

**From source:**
```bash
git clone https://github.com/VladislavTsytrikov/frostbyte.git
cd frostbyte
python3 frostbyte install
```
</details>

<details>
<summary><b>Uninstall</b></summary>

<br>

```bash
frostbyte uninstall          # keeps config
frostbyte uninstall --purge  # removes everything
```
</details>

---

## Live Monitor

```bash
frostbyte monitor
```

| Key | Action |
|:---:|--------|
| `Up` `Down` | Navigate processes |
| `Enter` | Freeze / Thaw selected |
| `e` | Exclude from auto-freezing |
| `f` / `t` | Quick-search freeze / thaw by name |
| `Tab` | Switch tab: Frozen / Candidates / Exclusions |
| `L` | Toggle language (EN / RU) |
| `q` | Quit |

---

## How It Works

```mermaid
flowchart LR
    subgraph daemon [" Daemon (Python)"]
        direction TB
        scan["Scan /proc\ntrack CPU time"]
        freeze["SIGSTOP\nidle app"]
        thaw["SIGCONT\nwake app"]
    end

    subgraph ext [" GNOME Extension (JS)"]
        focus["Window\nfocused"]
    end

    scan -- "idle > N min\nRSS > threshold" --> freeze
    focus -- "$XDG_RUNTIME_DIR/frostbyte-focus" --> thaw

    style daemon fill:#1a1a2e,stroke:#00b4d8,color:#e0e0e0
    style ext fill:#1a1a2e,stroke:#7c3aed,color:#e0e0e0
    style scan fill:#0d1b2a,stroke:#00b4d8,color:#e0e0e0
    style freeze fill:#0d1b2a,stroke:#e63946,color:#e0e0e0
    style thaw fill:#0d1b2a,stroke:#2ec4b6,color:#e0e0e0
    style focus fill:#0d1b2a,stroke:#7c3aed,color:#e0e0e0
```

**What's in the box:**

```
frostbyte (single Python file)
├── daemon        — polls /proc, sends SIGSTOP / SIGCONT
├── TUI monitor   — curses dashboard with 3 tabs
├── GNOME ext     — embedded JS, tracks focused window PID
└── installer     — writes extension + systemd service from embedded resources
```

> [!IMPORTANT]
> **Self-coupling** — the daemon auto-enables the extension on startup. The extension auto-starts the daemon via systemd if not running. They can't get out of sync.

<details>
<summary><b>Freeze / thaw in detail</b></summary>

<br>

**Freeze cycle:** the daemon polls `/proc` every second, tracking CPU time per process. If a process with RSS above the threshold shows no CPU activity for N minutes, it gets `SIGSTOP`. The kernel reclaims the physical memory pages.

**Thaw cycle:** the GNOME Shell extension writes the focused window's PID to `$XDG_RUNTIME_DIR/frostbyte-focus`. The daemon reads this file, finds the frozen ancestor *and* stopped descendants (for TUI apps inside terminals), and sends `SIGCONT`.

**Process tree awareness:** when you focus a terminal, FrostByte thaws both the terminal itself (ancestor search) and any stopped child processes like `vim`, `htop`, or `mc` inside it (descendant search).
</details>

---

## Configuration

`~/.config/frostbyte/config.json`

```jsonc
{
  "freeze_after_minutes": 10,    // idle time before auto-freeze
  "min_rss_mb": 100,             // minimum RSS to consider
  "scan_interval": 30,           // seconds between /proc scans
  "notifications": true,         // desktop notifications on freeze/thaw
  "whitelist": ["chrome"],       // your additions
  "rules": [                     // per-app overrides (regex)
    { "pattern": "firefox", "freeze_after_minutes": 30 },
    { "pattern": "code", "min_rss_mb": 200 }
  ]
}
```

| Option | Default | Description |
|--------|:-------:|-------------|
| `freeze_after_minutes` | `10` | Idle time before auto-freeze |
| `min_rss_mb` | `100` | Minimum RSS (MB) to consider freezing |
| `poll_interval` | `1` | Seconds between CPU polls |
| `scan_interval` | `30` | Seconds between full `/proc` scans |
| `max_freeze_hours` | `4` | Auto-thaw after this many hours |
| `notifications` | `true` | Desktop notifications on freeze / thaw |
| `whitelist` | `[]` | Extra process names to never freeze |
| `rules` | `[]` | Per-app rules (see below) |

> [!NOTE]
> FrostByte ships with a built-in whitelist (gnome-shell, pipewire, terminals, systemd, etc.). Your `whitelist` entries are **merged** on top — you only need to add app-specific names.

<details>
<summary><b>Per-app rules</b></summary>

<br>

Rules let you set custom freeze thresholds for specific apps using regex patterns:

```jsonc
"rules": [
  { "pattern": "firefox",  "freeze_after_minutes": 30 },  // give Firefox more time
  { "pattern": "code",     "min_rss_mb": 200 },           // only freeze VS Code above 200 MB
  { "pattern": "slack|discord", "freeze_after_minutes": 5 } // freeze chat apps faster
]
```

Each rule supports `pattern` (regex, case-insensitive), `freeze_after_minutes`, and `min_rss_mb`. The first matching rule wins. Unset fields fall back to global defaults.
</details>

<details>
<summary><b>Audio protection</b></summary>

<br>

FrostByte automatically detects apps playing audio via PulseAudio / PipeWire and skips freezing them. No configuration needed — if Spotify is playing music, it won't be frozen even if idle.
</details>

---

## CLI

```
frostbyte run             start daemon (foreground)
frostbyte monitor         live TUI dashboard
frostbyte status          show frozen & candidate processes
frostbyte freeze <name>   manually freeze by name
frostbyte thaw [name]     thaw by name (or all)
frostbyte install         install everything
frostbyte uninstall       remove everything
```

---

## Alternatives

| | **FrostByte** | Nyrna | XSuspender |
|---|:---:|:---:|:---:|
| Wayland | **yes** | no | no |
| GNOME 45–48 | **yes** | yes | yes |
| Auto-freeze (RAM-aware) | **yes** | no | no |
| Instant thaw on focus | **yes** | no | yes |
| Child process thawing | **yes** | no | no |
| Audio-aware (skip playing) | **yes** | no | no |
| Per-app rules (regex) | **yes** | no | no |
| Config hot reload | **yes** | no | no |
| Desktop notifications | **yes** | no | no |
| Zero dependencies | **yes** | no | yes |
| TUI dashboard | **yes** | no | no |
| Single file install | **yes** | no | no |

---

<p align="center">
  <a href="LICENSE">MIT License</a> &bull; Made for Linux desktops that deserve better memory management
</p>
