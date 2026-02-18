<p align="center">
  <br>
  <code>&nbsp;❄️ FrostByte &nbsp;</code>
  <br><br>
  <strong>Your idle apps are wasting gigabytes of RAM. FrostByte fixes that.</strong>
  <br>
  <sub>Auto-suspend inactive GUI apps on GNOME/Wayland &mdash; thaw instantly on focus</sub>
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.6+-3776ab.svg" alt="Python">
  <img src="https://img.shields.io/badge/GNOME_Shell-45_|_46_|_47-4a86cf.svg" alt="GNOME Shell">
  <img src="https://img.shields.io/badge/Wayland-native-green.svg" alt="Wayland">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen.svg" alt="Zero deps">
</p>

---

<p align="center">
  <img src="assets/demo.gif" alt="FrostByte demo" width="700">
</p>

You open Firefox, Slack, VS Code, Telegram, Spotify... then forget about half of them. They sit there eating **gigabytes** of RAM while doing absolutely nothing.

**FrostByte** watches your apps via `/proc`. When one has been idle long enough and is hogging memory, it sends `SIGSTOP` — the process freezes in place, and the OS can reclaim its pages. The moment you click that window, the companion GNOME Shell extension fires and FrostByte instantly thaws it with `SIGCONT`. You never notice.

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

```bash
git clone https://github.com/VladislavTsytrikov/frostbyte.git
cd frostbyte
./install.sh
```

```bash
# enable the extension (requires logout/login)
gnome-extensions enable frostbyte@cryogen

# start the daemon
systemctl --user enable --now frostbyte.service
```

That's it. FrostByte runs silently in the background.

## Usage

### CLI

```bash
frostbyte status           # show frozen & candidate processes
frostbyte freeze <name>    # manually freeze a process
frostbyte thaw [name]      # thaw one process or all
```

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
  "whitelist": ["gnome-shell", "pipewire", "kitty", "..."]
}
```

| Option | Default | Description |
|---|---|---|
| `freeze_after_minutes` | `30` | Minutes of zero CPU activity before freezing |
| `min_rss_mb` | `100` | Minimum RSS (MB) — small processes are never frozen |
| `poll_interval` | `1` | Seconds between focus checks (thaw latency) |
| `scan_interval` | `30` | Seconds between full `/proc` scans |
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
