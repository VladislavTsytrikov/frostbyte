# Freezer v1.0 — GitHub Release Design

## Summary

Polish Freezer for public GitHub release: fix bugs, add GNOME Shell panel UI, create README/LICENSE.

## Bug Fixes

| Issue | Fix |
|---|---|
| File descriptor leaks (`open()` without `with`) | Helper `_read_proc(path)` with context manager |
| No PID lock — multiple daemons can conflict | Check PID_FILE at startup with `kill(pid, 0)` |
| `_children()` scans all `/proc` per call | Build `ppid_map` once in `scan()`, reuse |
| Silent config parse error | `logging.warning()` on bad JSON, fallback to defaults |
| `/tmp/freezer-focus` not UID-scoped | `/tmp/freezer-focus-{uid}` |

## GNOME Extension Panel UI

Extend existing `extension.js` with:

- **Tray icon** (snowflake unicode) with frozen count badge
- **Popup menu** on click:
  - Header: "Freezer" + ON/OFF toggle (starts/stops systemd service)
  - List of frozen processes with name, RSS, and Thaw button per item
  - Footer: "Saved: ~X.X GB"
- **Communication**: daemon writes `/tmp/freezer-status-{uid}.json` every scan cycle
  - Format: `{"frozen": [{"pid": N, "name": "...", "rss_mb": N}], "saved_mb": N, "active": true}`
  - Extension reads on popup open + polls while visible

## GitHub Structure

```
freezer/
├── README.md
├── LICENSE             (MIT)
├── .gitignore
├── freezer             (Python daemon + CLI)
├── freezer.service     (systemd user unit)
├── install.sh
└── extension/
    ├── metadata.json
    └── extension.js    (with panel popup UI)
```

## Out of Scope (YAGNI)

- SIGHUP config reload
- Desktop notifications (notify-send)
- GTK settings app
- Makefile/setup.py/pyproject.toml
- CI/CD pipelines

## Decisions

- License: MIT
- README: English only
- UI: GNOME Shell extension popup (no separate app)
