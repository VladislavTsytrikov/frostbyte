<p align="center">
  <img src="assets/social-preview.png" alt="FrostByte Logo" width="200">
  <br>
  <code>&nbsp;❄️ FrostByte &nbsp;</code>
  <br><br>
  <strong>Your idle apps are wasting gigabytes of RAM. FrostByte fixes that.</strong>
  <br>
  <sub>Automatic RAM recovery for GNOME. Freeze the bloat, thaw instantly on focus.</sub>
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-3776ab.svg?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/GNOME_Shell-45_|_46_|_47-4a86cf.svg?style=for-the-badge" alt="GNOME Shell">
  <img src="https://img.shields.io/badge/Wayland-native-green.svg?style=for-the-badge" alt="Wayland">
</p>

---

<p align="center">
  <img src="assets/demo.gif" alt="FrostByte TUI Demo" width="850">
</p>

### 🧠 Stop the Memory Leak

Modern apps are hungry. Firefox, Slack, VS Code, and Spotify can easily sit on **4GB+ of RAM** while you're not even looking at them. Linux handles memory well, but it won't swap out pages that apps are technically "using" just by being alive.

**FrostByte** puts your inactive apps into "Cold Storage":
1. **Freeze** &mdash; Idle apps (no CPU activity) above a RAM threshold are sent `SIGSTOP`. The OS instantly reclaims their physical memory.
2. **Thaw** &mdash; The moment you focus or click a frozen window, the GNOME extension wakes it up with `SIGCONT`. It's **instant** and **transparent**.

> **The Result:** Your system stays snappy, your swap stays empty, and your battery lasts longer. ❄️

---

## ✨ Features

- **🚀 Instant Wake-up:** Zero-latency thawing via a native GNOME Shell extension.
- **📊 Gorgeous TUI:** Real-time dashboard to monitor frozen apps, candidates, and total RAM saved.
- **🛡️ Smart Thawing:** Wakes up entire process trees (children first!) to prevent IPC race conditions in browsers.
- **🧊 Auto-Freeze:** Scans `/proc` to find RAM-heavy apps that have been idle for too long.
- **🖱️ Mouse-Friendly:** Thaws apps when you click their frozen windows, even if they aren't focused.
- **🧩 Panel Indicator:** Quick-access menu in the GNOME top bar with a live frozen process count.
- **⚙️ Zero Dependencies:** Pure Python, no heavy libraries, works out of the box.

---

## 🖥️ Live Monitor (TUI)

Launch the dashboard with `frostbyte monitor`. It's not just a status tool; it's a full command center:

- **↑/↓**: Navigate processes.
- **Enter**: Manually Freeze/Thaw a process.
- **e**: Exclude a process from auto-freezing (adds to whitelist).
- **f/t**: Quick-search freeze/thaw by name.
- **Tab**: Switch between "Frozen" and "Candidates".

---

## 🛠️ Installation

### One-liner (Fastest)
```bash
curl -fsSL https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main/install.sh | bash
```

### From Source
```bash
git clone https://github.com/VladislavTsytrikov/frostbyte.git
cd frostbyte
./install.sh
```

### Post-Install
1. **Enable the extension**: `gnome-extensions enable frostbyte@cryogen` (you might need to log out/in or restart GNOME Shell).
2. **Start the daemon**: `systemctl --user enable --now frostbyte.service`

---

## ⚙️ Configuration

Located at `~/.config/frostbyte/config.json`:

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

---

## ⚖️ Alternatives

| | **FrostByte** | Nyrna | XSuspender |
|---|:---:|:---:|:---:|
| **Wayland Support** | ✅ | ❌ | ❌ |
| **GNOME Integration** | ✅ | ✅ | ✅ |
| **Auto-Freeze (RAM aware)**| ✅ | ❌ | ❌ |
| **Instant Thaw** | ✅ | ❌ | ✅ |
| **Minimal Dependencies** | ✅ | ❌ | ✅ |

---

## 📝 License

[MIT](LICENSE) &copy; 2026 Vladislav Tsytrikov
