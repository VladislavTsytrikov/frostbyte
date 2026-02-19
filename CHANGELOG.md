# Changelog

## [v2.4.0](https://github.com/VladislavTsytrikov/frostbyte/releases/tag/v2.4.0) — Selective Thaw

### New Features

- **Lazy thaw for multi-process apps** — when focusing a browser (Chrome, Firefox, Electron) with many frozen tabs, only the most recently active tab thaws instantly; remaining tabs thaw one per second. Switching away cancels the queue — unfocused tabs stay frozen and keep saving RAM.

### Bug Fixes

- **gnome-terminal-server shared parent bug** — focusing any terminal tab no longer thaws unrelated frozen processes in other tabs. Only processes frozen by FrostByte are thawed on focus.

### Tests

- 60 unit tests (was 55)

---

## [v2.3.0](https://github.com/VladislavTsytrikov/frostbyte/releases/tag/v2.3.0) — Hardened & Battle-Tested

16 bug fixes found by 3-round automated code review + 55 new unit tests.

### Bug Fixes (HIGH)

- **Audio detection ancestor expansion** — browser child processes producing audio now correctly protect the parent process from freezing
- **Hot reload config validation** — editing config while daemon runs now validates and clamps values
- **Stale config variable in main loop** — hot-reloaded settings now actually take effect

### Bug Fixes (MEDIUM)

- **Table-driven config validation** — unified type coercion, bool/inf/NaN rejection, upper-bound clamping
- **Stale `_frozen_at` cleanup** — freeze timestamps cleared on externally thawed processes
- **GNOME extension `_pollId` lifecycle** — prevents double-remove GLib warnings
- **Notification queue+batch** — replaced lossy rate limiter; simultaneous freezes produce a single grouped notification
- **`pactl` timeout** — reduced 5s to 2s to avoid blocking the main loop
- **Zombie `notify-send` prevention** — detached notification processes from daemon
- **Atomic file writes** — status, config, and default config all use tmp+rename for crash safety
- **Negative `max_freeze_hours`** — correctly maps to 0 (disabled) instead of default (enabled)
- **`scans_per_tick` type safety** — wrapped in `int()` to prevent float drift
- **Audio ancestor deduplication** — shared ancestor chains walked once, PID 1 excluded
- **Config reload resilience** — mtime updated only after success; catches all exceptions

### Tests

- Added `test_frostbyte.py` with **55 unit tests** covering audio detection, config validation, notifications, atomic writes, whitelist, per-app rules, freeze/thaw lifecycle

---

## [v2.2.0](https://github.com/VladislavTsytrikov/frostbyte/releases/tag/v2.2.0)

### Bug Fixes

- **Fix thread misidentification** — `scan()` no longer picks up Linux TIDs as separate processes
- **Fix whitelisted apps frozen as children** — `freeze_pid()` checks whitelist for each child before SIGSTOP
- **Startup orphan recovery** — thaws processes left stopped from a previous daemon crash

---

## [v2.1.0](https://github.com/VladislavTsytrikov/frostbyte/releases/tag/v2.1.0) — Smart Freeze

### New Features

- **Audio-aware freezing** — apps playing audio automatically skipped (PulseAudio / PipeWire)
- **Per-app rules** — custom freeze timeouts and RAM thresholds per app via regex
- **Desktop notifications** — freeze/thaw events shown as desktop notifications
- **Config hot reload** — edit config, changes apply instantly without restart

### Bug Fixes

- IPC files moved to `$XDG_RUNTIME_DIR` (prevents symlink attacks)
- Signal handler deadlock prevention
- Graceful shutdown thaws all frozen processes and children
- UID matching fixed (UID 100 no longer matches 1000)
- Single-pass `/proc` scan (eliminated redundant second pass)
- Cycle protection in process tree traversal
- UID validation in `thaw_pid()` ancestor walk
- PID file race condition fixed
- `frostbyte thaw` now uses full process-tree thawing

### TUI Improvements

- Visual redesign with icy dark theme
- Mouse hover, click-to-freeze/thaw, tab switching fixes

---

## [v2.0.0](https://github.com/VladislavTsytrikov/frostbyte/releases/tag/v2.0.0) — Single-File Architecture

### Breaking Changes

- Separate `extension/` directory and `frostbyte.service` removed (now embedded)

### Highlights

- **Single-file architecture** — extension JS, systemd unit, metadata all embedded in one Python script
- **`frostbyte install` / `uninstall`** — built-in installer from embedded resources
- **Smart whitelist merge** — user entries extend built-in defaults
- **Child process thawing** — focusing a terminal thaws stopped descendants
- **Self-coupling** — daemon auto-enables extension; extension auto-starts daemon

---

## [v1.0.0](https://github.com/VladislavTsytrikov/frostbyte/releases/tag/v1.0.0)

Initial release.

- Auto-freeze idle GUI apps via SIGSTOP after configurable timeout
- Instant thaw on window focus via GNOME Shell extension
- Process tree awareness — thaws child processes
- Live TUI monitor with 3 tabs (Frozen / Candidates / Exclusions)
- Built-in whitelist (gnome-shell, pipewire, terminals, systemd, etc.)
- GNOME panel indicator with frozen count and quick-thaw menu
- English / Russian language toggle
