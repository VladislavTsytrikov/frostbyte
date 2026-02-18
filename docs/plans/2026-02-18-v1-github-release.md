# Freezer v1.0 GitHub Release — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Polish Freezer daemon + GNOME extension for public GitHub release — fix all bugs, add panel popup UI, create README/LICENSE.

**Architecture:** Single-file Python daemon communicates with GNOME Shell extension via temp files. Daemon writes status JSON for extension to read. Extension writes focus/thaw-request PIDs for daemon to act on.

**Tech Stack:** Python 3 (stdlib only), GJS (GNOME Shell extension API — St, PanelMenu, PopupMenu), systemd user service.

---

### Task 1: Init git repo + .gitignore + LICENSE

**Files:**
- Create: `.gitignore`
- Create: `LICENSE`

**Step 1: Init git repo**

Run: `cd /data/projects/freezer && git init`

**Step 2: Create .gitignore**

```
__pycache__/
*.pyc
*.log
.idea/
.vscode/
*.swp
*~
```

**Step 3: Create LICENSE (MIT)**

Standard MIT license, copyright 2025 cryogen.

**Step 4: Initial commit**

```bash
git add .gitignore LICENSE
git commit -m "init: add .gitignore and MIT license"
```

---

### Task 2: Fix daemon — file descriptor leaks + proc reader helper

**Files:**
- Modify: `freezer` (lines 12-22 imports, lines 130-190 scan, lines 194-210 _children, lines 232-300 thaw/focus, lines 380-430 print_status, lines 447-497 cmd_thaw/cmd_freeze)

**Step 1: Add `_read_file` helper after the constants block (after line 27)**

Replace every bare `open(f"/proc/...").read()` with this helper:

```python
def _read_file(path: str) -> str:
    with open(path) as f:
        return f.read()
```

**Step 2: Replace all bare `open().read()` calls throughout the file**

Every instance of `open(f"/proc/{pid}/stat").read()` becomes `_read_file(f"/proc/{pid}/stat")`
Every instance of `open(f"/proc/{pid}/status").read()` becomes `_read_file(f"/proc/{pid}/status")`
Every instance of `open(f"/proc/{pid}/cmdline").read()` becomes `_read_file(f"/proc/{pid}/cmdline")`
Same for `open(f"/proc/{entry}/stat")` variants.

Locations to fix:
- `scan()` lines 140, 148, 156
- `_children()` line 201
- `thaw_pid()` line 243
- `_is_stopped()` line 280
- `_find_stopped_ancestor()` line 295
- `print_status()` line 391
- `cmd_thaw()` lines 456, 470

**Step 3: Commit**

```bash
git add freezer
git commit -m "fix: close file descriptors via context manager"
```

---

### Task 3: Fix daemon — PID lock to prevent duplicate instances

**Files:**
- Modify: `freezer` — `run()` method (around line 350)

**Step 1: Add `_check_already_running` method to FreezerDaemon class, before `run()`**

```python
def _check_already_running(self):
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 0)
            print(f"Freezer already running (PID {old_pid})", file=sys.stderr)
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass
        except PermissionError:
            print(f"Freezer already running (PID {old_pid})", file=sys.stderr)
            sys.exit(1)
```

**Step 2: Call it at the start of `run()`**

Insert `self._check_already_running()` as the first line of `run()`, before `_save_default_config()`.

**Step 3: Commit**

```bash
git add freezer
git commit -m "fix: prevent duplicate daemon instances via PID lock"
```

---

### Task 4: Fix daemon — optimize _children() with ppid_map

**Files:**
- Modify: `freezer` — `__init__()`, `scan()` method, `_children()` method

**Step 1: Add `self._ppid_map` to `__init__`**

```python
self._ppid_map: Dict[int, List[int]] = {}
```

**Step 2: Build ppid_map at the end of scan(), before "purge dead"**

```python
self._ppid_map = {}
for pid in seen:
    try:
        raw = _read_file(f"/proc/{pid}/stat")
        rp = raw.rindex(")")
        ppid = int(raw[rp + 2:].split()[1])
        self._ppid_map.setdefault(ppid, []).append(pid)
    except Exception:
        continue
```

**Step 3: Rewrite `_children()` to use the map**

```python
def _children(self, pid: int) -> List[int]:
    kids = []
    for child in self._ppid_map.get(pid, []):
        kids.append(child)
        kids.extend(self._children(child))
    return kids
```

**Step 4: Commit**

```bash
git add freezer
git commit -m "perf: build ppid_map in scan() instead of scanning /proc per _children() call"
```

---

### Task 5: Fix daemon — config parse warning + UID-scoped temp files

**Files:**
- Modify: `freezer` — constants (lines 23-27), `_load_config()`

**Step 1: UID-scope all temp file paths**

Replace the constants block:

```python
_UID = os.getuid()
FOCUS_FILE = Path(f"/tmp/freezer-focus-{_UID}")
STATUS_FILE = Path(f"/tmp/freezer-status-{_UID}.json")
THAW_FILE = Path(f"/tmp/freezer-thaw-{_UID}")
CONFIG_DIR = Path.home() / ".config" / "freezer"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "freezer.log"
PID_FILE = Path(f"/tmp/freezer-{_UID}.pid")
```

**Step 2: Fix `_load_config()` — warn on bad JSON**

```python
def _load_config(self) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception as e:
            logging.warning(f"Bad config {CONFIG_FILE}: {e} — using defaults")
    return cfg
```

**Step 3: Commit**

```bash
git add freezer
git commit -m "fix: UID-scope temp files, warn on bad config JSON"
```

---

### Task 6: Add daemon status file + thaw-request file

**Files:**
- Modify: `freezer` — add `_write_status()`, add `_check_thaw()`, modify main loop, modify `_shutdown()`

**Step 1: Add `_write_status()` method after `_check_freeze()`**

```python
def _write_status(self):
    frozen_list = []
    saved_mb = 0
    for pid in list(self.frozen):
        if pid in self.procs:
            p = self.procs[pid]
            frozen_list.append({"pid": pid, "name": p.name, "rss_mb": round(p.rss_mb)})
            saved_mb += p.rss_mb
    data = {"frozen": frozen_list, "saved_mb": round(saved_mb), "active": True}
    try:
        STATUS_FILE.write_text(json.dumps(data) + "\n")
    except Exception:
        pass
```

**Step 2: Add `_check_thaw()` method**

```python
def _check_thaw(self):
    try:
        if THAW_FILE.exists():
            raw = THAW_FILE.read_text().strip()
            THAW_FILE.unlink(missing_ok=True)
            if raw:
                pid = int(raw)
                self.thaw_pid(pid)
    except (ValueError, IOError):
        pass
```

**Step 3: Wire into main loop**

In `run()`, after `self._check_freeze()`, add `self._write_status()`.
In the poll loop, alongside `self._check_focus()`, add `self._check_thaw()`.

**Step 4: Clean up status file on shutdown**

In `_shutdown()`, after thawing all processes, write inactive status and clean up:
```python
try:
    STATUS_FILE.write_text(json.dumps({"frozen": [], "saved_mb": 0, "active": False}) + "\n")
except Exception:
    pass
PID_FILE.unlink(missing_ok=True)
```

**Step 5: Commit**

```bash
git add freezer
git commit -m "feat: daemon writes status JSON + watches thaw-request file"
```

---

### Task 7: Rewrite GNOME Shell extension with panel popup UI

**Files:**
- Rewrite: `extension/extension.js`

The extension must:
1. Keep the existing focus-tracking + captured-event logic
2. Add a PanelMenu.Button with snowflake icon in the top bar
3. Show popup with: toggle (start/stop service), frozen process list with thaw buttons, saved RAM counter
4. Read STATUS_FILE on popup open + poll every 3s while open
5. Thaw button writes PID to THAW_FILE
6. Get UID from /proc/self/status for temp file paths
7. Clean up all signal connections and timers in disable()

Required imports: GLib, Gio, Meta, Clutter, St, Main, PanelMenu, PopupMenu, Extension

**Step 1: Write the complete new extension.js** (see design doc for UI mockup)

**Step 2: Commit**

```bash
git add extension/
git commit -m "feat: GNOME Shell panel popup with frozen list, thaw buttons, toggle"
```

---

### Task 8: Update install.sh

**Files:**
- Modify: `install.sh`

**Step 1: Add python3 check at the start, add uninstall instructions at the end**

Add before the install steps:
```bash
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required" >&2
    exit 1
fi
```

Add at the end:
```
echo "To uninstall:"
echo "  systemctl --user disable --now freezer.service"
echo "  rm ~/.local/bin/freezer"
echo "  rm -rf ~/.local/share/gnome-shell/extensions/freezer@cryogen"
echo "  rm ~/.config/systemd/user/freezer.service"
```

**Step 2: Commit**

```bash
git add install.sh
git commit -m "chore: add python3 check and uninstall instructions to install.sh"
```

---

### Task 9: Create README.md

**Files:**
- Create: `README.md`

**Step 1: Write README.md**

Must include:
- Project name + one-line description + snowflake emoji in title
- Feature comparison table vs XSuspender, Nyrna, Hyprfreeze
- How it works section (daemon + extension architecture)
- Installation steps
- Configuration (default config, whitelist)
- CLI usage examples
- GNOME panel UI description
- Requirements (Python 3, GNOME 45-47, Wayland)
- License (MIT)

Key selling points:
- Only tool that works on Wayland + GNOME
- Automatic freeze based on idle time + RSS threshold
- RAM savings focus
- Zero external dependencies
- Native GNOME Shell panel integration

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with feature comparison and usage guide"
```

---

### Task 10: Final review + tag

**Step 1: Verify Python syntax**

Run: `python3 -c "import py_compile; py_compile.compile('/data/projects/freezer/freezer', doraise=True)"`

**Step 2: Review all files for consistency**

Check that all temp file paths match between daemon and extension (UID-scoped).
Check that STATUS_FILE, THAW_FILE, FOCUS_FILE names match.

**Step 3: Tag release**

```bash
git tag -a v1.0.0 -m "v1.0.0 — initial public release"
```
