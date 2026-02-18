<p align="center">
  <br>
  <code>&nbsp;❄️ FrostByte &nbsp;</code>
  <br><br>
  <strong>Your idle apps are wasting gigabytes of RAM. FrostByte fixes that.</strong>
  <br>
  <sub>Reclaim your RAM from idle apps. Automatically.</sub>
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.6+-3776ab.svg?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/GNOME_Shell-45_|_46_|_47-4a86cf.svg?style=for-the-badge" alt="GNOME Shell">
  <img src="https://img.shields.io/badge/Wayland-native-green.svg?style=for-the-badge" alt="Wayland">
</p>

---

<p align="center">
  <img src="assets/demo.gif" alt="FrostByte demo" width="800">
</p>

### 🧠 Stop the Memory Leak (Manually and Automatically)

Your browser, Slack, VS Code, and Spotify are eating **gigabytes** of RAM right now, even if you haven't touched them in hours. Linux is great at managing memory, but it can't swap out memory that apps are actively "using" (just sitting there).

**FrostByte** is a lightweight daemon that puts inactive GUI applications into "Cold Storage":
1. **Freeze** &mdash; Idle apps (no CPU activity) above a RAM threshold get a `SIGSTOP`. The OS instantly reclaims their physical memory pages.
2. **Thaw** &mdash; The moment you focus or click a frozen window, the GNOME extension wakes it up with `SIGCONT`. It's **instant** and **transparent**.

> **Result:** Your laptop stays cool, your swap stays empty, and your system stays fast. ❄️

## How it works

```
                    ┌─────────────────┐
                    │  GNOME Shell    │
                    │  Extension      │
                    │                 │
  click/focus ────▶ │ writes PID to   │
  on window        │ /tmp/frostbyte  │
                    └────────┬────────┘
                             │
                             ▼
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│  /proc      │───▶│  FrostByte      │───▶│  SIGSTOP     │
│  (CPU+RSS)  │    │  Daemon         │    │  (freeze)    │
└─────────────┘    │                 │    └──────────────┘
                    │  idle > 30min   │
                    │  RSS > 100MB    │───▶  SIGCONT
                    │  focus detected │    │  (thaw)
                    └─────────────────┘    └──────────────┘
```

1. **Scan** &mdash; reads `/proc` every 30s, tracking CPU ticks and RSS per process
2. **Freeze** &mdash; idle too long + above RAM threshold → `SIGSTOP` the entire process tree
3. **Detect** &mdash; extension catches window focus *and* clicks on frozen windows (Clutter capture phase)
4. **Thaw** &mdash; daemon picks up the PID, walks the process tree, sends `SIGCONT` — instant restore
5. **Panel UI** &mdash; snowflake indicator shows frozen count, click to see list and thaw individually

## Quick start

**One-liner install** (requires `curl`):

```bash
curl -fsSL https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main/install.sh | bash
```

Or clone and install locally:

```bash
git clone https://github.com/VladislavTsytrikov/frostbyte.git
cd frostbyte
./install.sh
```

Then enable the extension and start the daemon:

```bash
gnome-extensions enable frostbyte@cryogen   # requires logout/login
systemctl --user enable --now frostbyte.service
```

That's it. FrostByte runs silently in the background.

## Usage

### CLI

```bash
frostbyte status           # show frozen & candidate processes
frostbyte monitor          # live TUI dashboard
frostbyte freeze <name>    # manually freeze a process
frostbyte thaw [name]      # thaw one process or all
```

### Live monitor

`frostbyte monitor` opens a full-terminal dashboard that refreshes every 3 seconds.
It shows RAM saved, all frozen processes, and freeze candidates with idle-time
progress bars. Press `f` to freeze a process by name, `t` to thaw, `q` to quit.

### Panel indicator

The snowflake icon in your top bar shows how many apps are frozen. Click it to:
- See all frozen processes with their RAM usage
- Thaw any process with one click
- Toggle the daemon on/off

### Example output

```
$ frostbyte status

  Config: freeze after 30min idle, min RSS 100MB
  Whitelist: 24 patterns

  FROZEN (2):
     8412   842 MB  firefox
    12034   310 MB  slack

  CANDIDATES (3):
    15220   520 MB  idle  28.3m [##############------] code
     9881   180 MB  idle  12.1m [########------------] telegram
    11002   130 MB  idle   5.2m [###-----------------] nautilus
```

## Configuration

Config file: `~/.config/frostbyte/config.json` (created on first run)

```json
{
  "freeze_after_minutes": 30,
  "min_rss_mb": 100,
  "poll_interval": 1,
  "scan_interval": 30,
  "max_freeze_hours": 4,
  "whitelist": ["gnome-shell", "pipewire", "kitty", "..."]
}
```

| Option | Default | Description |
|---|---|---|
| `freeze_after_minutes` | `30` | Minutes of zero CPU activity before freezing |
| `min_rss_mb` | `100` | Minimum RSS (MB) — small processes are never frozen |
| `poll_interval` | `1` | Seconds between focus checks (thaw latency) |
| `scan_interval` | `30` | Seconds between full `/proc` scans |
| `max_freeze_hours` | `4` | Auto-thaw after this many hours frozen (0 = disabled) — prevents stale TCP connections and app crashes |
| `whitelist` | 24 patterns | Substring match on process name/cmdline — add your music player, IDE, etc. |

Logs: `~/.config/frostbyte/frostbyte.log`

## Alternatives

There are other tools in this space, but none cover the same combination of features:

| | FrostByte | [Nyrna](https://github.com/Merrit/nyrna) | [XSuspender](https://github.com/kernc/xsuspender) | [Hyprfreeze](https://github.com/Zerodya/hyprfreeze) |
|---|:---:|:---:|:---:|:---:|
| **Wayland** | :white_check_mark: | :x: | :x: | :white_check_mark: |
| **GNOME** | :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: Hyprland only |
| **Auto-freeze** | :white_check_mark: idle + RSS | :x: manual | :white_check_mark: on focus loss | :x: manual |
| **RAM-aware** | :white_check_mark: | :x: | :x: | :x: |
| **Instant thaw** | :white_check_mark: | :x: | :white_check_mark: | :x: |
| **Panel UI** | :white_check_mark: | :white_check_mark: | :x: | :x: |
| **Dependencies** | none | Flutter/Dart | libwnck | Hyprland tools |

## Requirements

- Python 3.6+
- GNOME Shell 45, 46, or 47
- Wayland session
- systemd (user session)

Tested on Pop!_OS, Ubuntu 24.04+, Fedora 40+

## Uninstall

```bash
systemctl --user disable --now frostbyte.service
rm ~/.local/bin/frostbyte
rm -rf ~/.local/share/gnome-shell/extensions/frostbyte@cryogen
rm ~/.config/systemd/user/frostbyte.service
```

## License

[MIT](LICENSE)
