# Freezer :snowflake:

**Auto-suspend inactive GUI apps to save RAM**

Freezer is a lightweight daemon for GNOME/Wayland that monitors process CPU activity via `/proc` and automatically sends `SIGSTOP` to applications that have been idle for a configurable period. When you focus a frozen window, the companion GNOME Shell extension detects the event and the daemon instantly thaws the process with `SIGCONT` — no perceptible delay.

## Feature comparison

| Feature | Freezer | XSuspender | Nyrna | Hyprfreeze |
|---|---|---|---|---|
| Wayland support | Yes | No (X11 only) | No (X11 only) | Yes |
| GNOME support | Yes | Yes | Yes | No (Hyprland) |
| Auto-freeze (by inactivity) | Yes | On focus loss | No (manual) | No (manual) |
| RAM-aware (RSS threshold) | Yes | No | No | No |
| Instant thaw on focus | Yes | Yes | No | No |
| Zero dependencies | Yes | libwnck, etc | Flutter/Dart | Hyprland tools |
| Panel UI | Yes | No | Yes (GTK app) | No |

## How it works

1. **Scan** — The daemon reads `/proc` every 30 seconds, tracking CPU ticks and RSS for each user-owned process.
2. **Freeze** — When a process has been idle for the configured time (default 30 min) *and* exceeds the minimum RSS threshold (default 100 MB), the daemon sends `SIGSTOP` to the entire process tree.
3. **Detect focus** — The GNOME Shell extension listens for window focus changes and click events (including clicks on frozen/unresponsive windows via the Clutter capture phase). On any such event it writes the window's PID to `/tmp/freezer-focus`.
4. **Thaw** — The daemon polls the focus file every 1 second. When it finds a PID, it walks up the process tree to locate the stopped ancestor and sends `SIGCONT` to the full tree, restoring the application instantly.
5. **Panel indicator** — A GNOME Shell panel indicator shows currently frozen processes with one-click thaw buttons.

## Installation

```bash
git clone https://github.com/VladislavTsytrikov/freezer.git
cd freezer
./install.sh
```

Then enable the extension and start the service:

```bash
gnome-extensions enable freezer@cryogen   # requires logout/login
systemctl --user enable --now freezer.service
```

## Usage

### CLI

```
freezer status           # show frozen & candidate processes
freezer freeze <name>    # manually freeze a process by name
freezer thaw [name]      # thaw a specific process (or all if no name given)
```

### GNOME panel indicator

The panel icon shows the number of currently frozen apps. Click it to see the list and thaw individual processes.

### Logs

```
~/.config/freezer/freezer.log
```

## Configuration

Config file: `~/.config/freezer/config.json`

A default config is created on first run:

```json
{
  "freeze_after_minutes": 30,
  "min_rss_mb": 100,
  "poll_interval": 1,
  "scan_interval": 30,
  "whitelist": [
    "gnome-shell",
    "gnome-session",
    "gsd-",
    "mutter",
    "Xwayland",
    "pulseaudio",
    "pipewire",
    "wireplumber",
    "gnome-terminal",
    "kitty",
    "alacritty",
    "bash",
    "zsh",
    "freezer",
    "docker",
    "systemd",
    "dbus-daemon",
    "ssh",
    "gnome-keyring"
  ]
}
```

| Field | Description |
|---|---|
| `freeze_after_minutes` | Minutes of zero CPU activity before a process is frozen |
| `min_rss_mb` | Minimum resident memory (MB) — processes below this are never frozen |
| `poll_interval` | Seconds between focus-file checks (thaw latency) |
| `scan_interval` | Seconds between full `/proc` scans |
| `whitelist` | Substring patterns matched against process name and cmdline. Any match prevents freezing. Add your terminal emulator, music player, or anything else that should never be suspended. |

## Requirements

- Python 3.6+
- GNOME Shell 45, 46, or 47
- Wayland session
- systemd (user session)

Tested on: Pop!_OS, Ubuntu 24.04+, Fedora 40+

## License

[MIT](LICENSE)
