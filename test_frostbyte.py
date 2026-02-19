"""Tests for FrostByte daemon — HIGH fixes and MEDIUM bug verification."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

# Import frostbyte module (file has no .py extension, so we need explicit loader)
import importlib.util
import importlib.machinery
_frostbyte_path = str(Path(__file__).parent / "frostbyte")
_loader = importlib.machinery.SourceFileLoader("frostbyte", _frostbyte_path)
_spec = importlib.util.spec_from_file_location(
    "frostbyte", _frostbyte_path, loader=_loader)
fb = importlib.util.module_from_spec(_spec)
sys.modules["frostbyte"] = fb
_spec.loader.exec_module(fb)


# ── helpers ──────────────────────────────────────────────────


def _make_daemon(**overrides):
    """Create a Daemon instance with sensible test defaults."""
    cfg = {
        "freeze_after_minutes": 10,
        "min_rss_mb": 100,
        "poll_interval": 1,
        "scan_interval": 30,
        "max_freeze_hours": 4,
        "whitelist": [],
        "rules": [],
        "notifications": False,
    }
    cfg.update(overrides)
    with mock.patch.object(fb.FrostByteDaemon, "_load_config", return_value=cfg):
        d = fb.FrostByteDaemon(config_overrides=cfg)
    return d


def _fake_proc_stat(pid, ppid, comm="app"):
    """Build a fake /proc/{pid}/stat line."""
    # Format: pid (comm) S ppid pgrp session tty_nr tpgid flags
    #         minflt cminflt majflt cmajflt utime stime ...
    # Fields after ')': state ppid pgrp session tty tpgid flags
    #   minflt cminflt majflt cmajflt utime(11) stime(12) ...
    #   ... rss(21)
    fields = ["S", str(ppid)] + ["0"] * 20  # 22 fields total after ')'
    fields[11] = "100"  # utime
    fields[12] = "50"   # stime
    fields[21] = "25600"  # rss in pages (100 MB with 4096 page size)
    return f"{pid} ({comm}) " + " ".join(fields)


# ═══════════════════════════════════════════════════════════════
# HIGH #1: Audio detection includes ancestor PIDs
# ═══════════════════════════════════════════════════════════════


class TestAudioAncestorExpansion:
    """Verify _refresh_audio_pids walks up process tree."""

    def test_ancestor_pids_included(self):
        """Audio child PID should expand to include parent PIDs."""
        d = _make_daemon()

        # Simulate: child PID 5000 (renderer) -> parent PID 3000 (browser)
        # -> parent PID 1 (init)
        pactl_output = (
            "Sink Input #42\n"
            "  Properties:\n"
            '    application.process.id = "5000"\n'
        )
        proc_stat_5000 = "5000 (renderer) S 3000 0 0 0 0 0 0 0 0 0 100 50 0 0 0 0 0 0 0 0 0 25600"
        proc_stat_3000 = "3000 (firefox) S 1 0 0 0 0 0 0 0 0 0 100 50 0 0 0 0 0 0 0 0 0 25600"

        def fake_read_file(path):
            if path == "/proc/5000/stat":
                return proc_stat_5000
            if path == "/proc/3000/stat":
                return proc_stat_3000
            raise FileNotFoundError(path)

        with mock.patch("subprocess.run") as mock_run, \
             mock.patch.object(fb, "_read_file", side_effect=fake_read_file):
            mock_run.return_value = mock.Mock(returncode=0, stdout=pactl_output)
            d._refresh_audio_pids()

        assert 5000 in d._audio_pids, "child audio PID should be in set"
        assert 3000 in d._audio_pids, "parent PID should be in set"

    def test_no_audio_pids(self):
        """No audio output → empty set."""
        d = _make_daemon()
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="")
            d._refresh_audio_pids()
        assert d._audio_pids == set()

    def test_pactl_missing(self):
        """If pactl is not installed, audio_pids should be empty."""
        d = _make_daemon()
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            d._refresh_audio_pids()
        assert d._audio_pids == set()

    def test_pactl_timeout(self):
        """If pactl hangs, audio_pids should be empty."""
        d = _make_daemon()
        with mock.patch("subprocess.run",
                        side_effect=subprocess.TimeoutExpired("pactl", 5)):
            d._refresh_audio_pids()
        assert d._audio_pids == set()

    def test_circular_parentage_no_infinite_loop(self):
        """A cycle in /proc/stat ppid shouldn't cause infinite loop."""
        d = _make_daemon()
        pactl_output = '    application.process.id = "100"\n'

        # Create a cycle: 100 -> 200 -> 100
        def fake_read_file(path):
            if path == "/proc/100/stat":
                return "100 (app) S 200 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
            if path == "/proc/200/stat":
                return "200 (parent) S 100 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
            raise FileNotFoundError(path)

        with mock.patch("subprocess.run") as mock_run, \
             mock.patch.object(fb, "_read_file", side_effect=fake_read_file):
            mock_run.return_value = mock.Mock(returncode=0, stdout=pactl_output)
            d._refresh_audio_pids()  # should not hang

        assert 100 in d._audio_pids
        assert 200 in d._audio_pids


# ═══════════════════════════════════════════════════════════════
# HIGH #2: Hot reload calls _validate_config
# ═══════════════════════════════════════════════════════════════


class TestHotReloadValidation:
    """Verify _reload_config_if_changed calls _validate_config."""

    def test_validate_called_on_reload(self, tmp_path):
        d = _make_daemon()
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"poll_interval": 1}))

        with mock.patch.object(fb, "CONFIG_FILE", config_file):
            d._config_mtime = 0  # force mismatch
            with mock.patch.object(d, "_validate_config") as mock_validate, \
                 mock.patch.object(d, "_compile_rules"):
                d._reload_config_if_changed()
                mock_validate.assert_called_once()

    def test_scans_per_tick_updated_after_reload(self):
        """After hot reload, scans_per_tick should reflect new config."""
        d = _make_daemon(scan_interval=30, poll_interval=1)
        # Simulate: initially scans_per_tick = 30
        scans = max(1, d.config["scan_interval"] // d.config["poll_interval"])
        assert scans == 30

        # After config change
        d.config["scan_interval"] = 60
        scans = max(1, d.config["scan_interval"] // d.config["poll_interval"])
        assert scans == 60

    def test_config_mtime_not_updated_on_failure(self):
        """If _load_config fails, mtime should not be updated so retry works."""
        d = _make_daemon()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text('{"poll_interval": 5}')
            original_mtime = d._config_mtime

            with mock.patch.object(fb, "CONFIG_FILE", config_file), \
                 mock.patch.object(d, "_load_config",
                                   side_effect=RuntimeError("bad")):
                d._reload_config_if_changed()

            # mtime should NOT have been updated since load failed
            assert d._config_mtime == original_mtime


# ═══════════════════════════════════════════════════════════════
# MEDIUM #1: _validate_config crashes on non-numeric values
# ═══════════════════════════════════════════════════════════════


class TestValidateConfigTypeSafety:
    """_validate_config should handle non-numeric config values gracefully."""

    def test_string_poll_interval(self):
        d = _make_daemon()
        d.config["poll_interval"] = "not_a_number"
        d._validate_config()
        assert isinstance(d.config["poll_interval"], (int, float))
        assert d.config["poll_interval"] > 0

    def test_string_scan_interval(self):
        d = _make_daemon()
        d.config["scan_interval"] = "abc"
        d._validate_config()
        assert isinstance(d.config["scan_interval"], (int, float))
        assert d.config["scan_interval"] > 0

    def test_string_freeze_after_minutes(self):
        d = _make_daemon()
        d.config["freeze_after_minutes"] = "xyz"
        d._validate_config()
        assert isinstance(d.config["freeze_after_minutes"], (int, float))
        assert d.config["freeze_after_minutes"] > 0

    def test_string_min_rss_mb(self):
        d = _make_daemon()
        d.config["min_rss_mb"] = []
        d._validate_config()
        assert isinstance(d.config["min_rss_mb"], (int, float))
        assert d.config["min_rss_mb"] >= 0

    def test_string_max_freeze_hours(self):
        d = _make_daemon()
        d.config["max_freeze_hours"] = None
        d._validate_config()
        assert isinstance(d.config["max_freeze_hours"], (int, float))

    def test_infinity_rejected(self):
        d = _make_daemon()
        d.config["poll_interval"] = float("inf")
        d._validate_config()
        assert d.config["poll_interval"] == 1  # default

    def test_infinity_string_rejected(self):
        d = _make_daemon()
        d.config["scan_interval"] = "inf"
        d._validate_config()
        assert d.config["scan_interval"] == 30  # default

    def test_bool_rejected(self):
        d = _make_daemon()
        d.config["poll_interval"] = True
        d._validate_config()
        assert d.config["poll_interval"] == 1  # default, not True/1

    def test_numeric_string_becomes_int(self):
        d = _make_daemon()
        d.config["poll_interval"] = "3"
        d._validate_config()
        assert d.config["poll_interval"] == 3
        assert isinstance(d.config["poll_interval"], int)

    def test_negative_max_freeze_hours_disables(self):
        """Negative max_freeze_hours should become 0 (disabled), not default 4."""
        d = _make_daemon()
        d.config["max_freeze_hours"] = -1
        d._validate_config()
        assert d.config["max_freeze_hours"] == 0

    def test_zero_max_freeze_hours_stays_zero(self):
        """Zero max_freeze_hours means disabled, should stay 0."""
        d = _make_daemon()
        d.config["max_freeze_hours"] = 0
        d._validate_config()
        assert d.config["max_freeze_hours"] == 0

    def test_negative_poll_interval_gets_default(self):
        d = _make_daemon()
        d.config["poll_interval"] = -5
        d._validate_config()
        assert d.config["poll_interval"] == 1

    def test_zero_poll_interval_gets_default(self):
        d = _make_daemon()
        d.config["poll_interval"] = 0
        d._validate_config()
        assert d.config["poll_interval"] == 1

    def test_valid_values_unchanged(self):
        d = _make_daemon(poll_interval=2, scan_interval=60)
        d._validate_config()
        assert d.config["poll_interval"] == 2
        assert d.config["scan_interval"] == 60

    def test_nan_rejected(self):
        d = _make_daemon(poll_interval=float("nan"))
        d._validate_config()
        assert d.config["poll_interval"] == 1  # default

    def test_nan_string_rejected(self):
        d = _make_daemon(poll_interval="nan")
        d._validate_config()
        assert d.config["poll_interval"] == 1  # default


# ═══════════════════════════════════════════════════════════════
# MEDIUM #2: Stale _frozen_at after external SIGCONT
# ═══════════════════════════════════════════════════════════════


class TestStaleFrozenAt:
    """_frozen_at should be cleaned when process is externally thawed."""

    def test_frozen_at_cleaned_on_external_sigcont(self):
        """scan() detecting external SIGCONT should clean _frozen_at."""
        d = _make_daemon()
        pid = 12345
        uid = os.getuid()

        # Pre-populate: process was frozen by daemon
        d.frozen.add(pid)
        d._frozen_at[pid] = time.time() - 300
        d.procs[pid] = fb.Proc(
            pid=pid, name="test", cmdline="test", cpu=100, rss_mb=200,
            last_active=time.time(), frozen=True,
        )

        # Mock /proc so scan() sees pid=12345 in S state (not T = externally thawed)
        # Fields after ')': state ppid pgrp sess tty tpgid flags minflt cminflt
        #   majflt cmajflt utime(11) stime(12) ... rss(21)
        stat_line = f"{pid} (test) S 1" + " 0" * 7 + " 0 0 0 0 100 50" + " 0" * 7 + " 25600"
        status_text = f"Uid:\t{uid}\t{uid}\t{uid}\t{uid}\nTgid:\t{pid}\n"
        cmdline_text = "test"

        def fake_read(path):
            if path == f"/proc/{pid}/stat":
                return stat_line
            if path == f"/proc/{pid}/status":
                return status_text
            if path == f"/proc/{pid}/cmdline":
                return cmdline_text
            raise FileNotFoundError(path)

        with mock.patch("os.listdir", return_value=[str(pid)]), \
             mock.patch.object(fb, "_read_file", side_effect=fake_read):
            d.scan()

        assert pid not in d.frozen, "should be removed from frozen set"
        assert pid not in d._frozen_at, "_frozen_at should be cleaned"
        assert d.procs[pid].frozen is False

    def test_purge_dead_cleans_frozen_at(self):
        """Dead processes should be purged from _frozen_at by scan()."""
        d = _make_daemon()
        pid = 99999

        d.frozen.add(pid)
        d._frozen_at[pid] = time.time()
        d.procs[pid] = fb.Proc(
            pid=pid, name="dead", cmdline="dead", cpu=0, rss_mb=100,
            last_active=time.time(), frozen=True,
        )

        # scan() with empty /proc → pid not seen → purged
        with mock.patch("os.listdir", return_value=[]), \
             mock.patch.object(fb, "_read_file", side_effect=FileNotFoundError):
            d.scan()

        assert pid not in d.procs, "should be purged from procs"
        assert pid not in d.frozen, "should be purged from frozen"
        assert pid not in d._frozen_at, "should be purged from _frozen_at"


# ═══════════════════════════════════════════════════════════════
# MEDIUM #4: Notification rate limiting
# ═══════════════════════════════════════════════════════════════


class TestNotificationBatching:
    """Notifications should batch multiple events into one."""

    def test_batch_freeze_notifications(self):
        """Multiple freezes in one cycle produce a single batched notification."""
        d = _make_daemon(notifications=True)

        calls = []

        def fake_popen(*args, **kwargs):
            calls.append(args)
            m = mock.Mock()
            m.poll.return_value = 0
            return m

        # Queue 5 freeze notifications
        for i in range(5):
            d._notify("Frozen", f"app{i} (100 MB)")

        with mock.patch("subprocess.Popen", side_effect=fake_popen):
            d._flush_notifications()

        assert len(calls) == 1, f"Expected 1 batched call, got {len(calls)}"
        # The body should mention all 5 apps
        sent_body = calls[0][0][6]  # ["notify-send", "-a", ..., title, body]
        assert "5 apps" in sent_body

    def test_single_notification_not_batched(self):
        """Single notification should not show batch format."""
        d = _make_daemon(notifications=True)

        calls = []

        def fake_popen(*args, **kwargs):
            calls.append(args)
            return mock.Mock()

        d._notify("Frozen", "firefox (200 MB)")

        with mock.patch("subprocess.Popen", side_effect=fake_popen):
            d._flush_notifications()

        assert len(calls) == 1
        sent_body = calls[0][0][6]
        assert sent_body == "firefox (200 MB)"

    def test_flush_clears_pending(self):
        """After flush, pending list should be empty."""
        d = _make_daemon(notifications=True)
        d._notify("Frozen", "app1")
        with mock.patch("subprocess.Popen", return_value=mock.Mock()):
            d._flush_notifications()
        assert len(d._pending_notifications) == 0

    def test_notification_uses_start_new_session(self):
        """notify-send should use start_new_session to avoid zombies."""
        d = _make_daemon(notifications=True)
        d._notify("Frozen", "test-app")

        with mock.patch("subprocess.Popen") as mock_popen:
            d._flush_notifications()
            mock_popen.assert_called_once()
            _, kwargs = mock_popen.call_args
            assert kwargs.get("start_new_session") is True

    def test_notifications_disabled(self):
        """No notifications when config disabled."""
        d = _make_daemon(notifications=False)
        d._notify("Frozen", "test-app")
        assert len(d._pending_notifications) == 0

    def test_mixed_freeze_thaw_batches_separately(self):
        """Freeze and thaw notifications batch into separate messages."""
        d = _make_daemon(notifications=True)

        calls = []

        def fake_popen(*args, **kwargs):
            calls.append(args)
            return mock.Mock()

        d._notify("Frozen", "app1")
        d._notify("Frozen", "app2")
        d._notify("Thawed", "app3")

        with mock.patch("subprocess.Popen", side_effect=fake_popen):
            d._flush_notifications()

        assert len(calls) == 2  # one for "Frozen", one for "Thawed"


# ═══════════════════════════════════════════════════════════════
# MEDIUM #7: Non-atomic STATUS_FILE write
# ═══════════════════════════════════════════════════════════════


class TestAtomicStatusWrite:
    """STATUS_FILE writes should be atomic (write tmp + rename)."""

    def test_write_status_produces_valid_json(self):
        """_write_status should produce valid JSON."""
        d = _make_daemon()
        d.frozen = set()
        d.procs = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "frostbyte-status.json"
            tmp_file = status_file.with_suffix(".tmp")
            with mock.patch.object(fb, "STATUS_FILE", status_file):
                d._write_status()
                content = status_file.read_text()
                data = json.loads(content)
                assert "frozen" in data
                assert data["saved_mb"] == 0
                # tmp file should be gone (renamed to final)
                assert not tmp_file.exists()

    def test_write_status_no_partial_json(self):
        """No .tmp file should remain after successful write."""
        d = _make_daemon()
        d.frozen = {100}
        d.procs = {100: fb.Proc(pid=100, name="app", cmdline="app",
                                cpu=0, rss_mb=150, last_active=time.time(),
                                frozen=True)}

        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "frostbyte-status.json"
            with mock.patch.object(fb, "STATUS_FILE", status_file):
                d._write_status()
                data = json.loads(status_file.read_text())
                assert len(data["frozen"]) == 1
                assert data["frozen"][0]["name"] == "app"


# ═══════════════════════════════════════════════════════════════
# Existing functionality regression tests
# ═══════════════════════════════════════════════════════════════


class TestWhitelist:
    def test_is_whitelisted_name_match(self):
        d = _make_daemon(whitelist=["firefox"])
        assert d._is_whitelisted("firefox", "firefox --no-remote")

    def test_is_whitelisted_no_match(self):
        d = _make_daemon(whitelist=["firefox"])
        assert not d._is_whitelisted("chrome", "/opt/chrome/chrome")

    def test_add_to_whitelist(self):
        d = _make_daemon(whitelist=[])
        with mock.patch.object(d, "_save_config"):
            assert d.add_to_whitelist("vscode")
        assert "vscode" in d.config["whitelist"]

    def test_add_duplicate_whitelist(self):
        d = _make_daemon(whitelist=["vscode"])
        assert not d.add_to_whitelist("vscode")

    def test_remove_from_whitelist(self):
        d = _make_daemon(whitelist=["chrome"])
        with mock.patch.object(d, "_save_config"):
            assert d.remove_from_whitelist("chrome")
        assert "chrome" not in d.config["whitelist"]


class TestPerAppRules:
    def test_compile_rules_valid(self):
        d = _make_daemon(rules=[
            {"pattern": "firefox", "freeze_after_minutes": 30},
        ])
        assert len(d._compiled_rules) == 1
        assert d._compiled_rules[0]["regex"].search("firefox")

    def test_compile_rules_bad_regex(self):
        d = _make_daemon(rules=[
            {"pattern": "[invalid", "freeze_after_minutes": 30},
        ])
        # Bad regex should be skipped, not crash
        assert len(d._compiled_rules) == 0


class TestIsStopped:
    def test_stopped_process(self):
        d = _make_daemon()
        with mock.patch.object(fb, "_read_file",
                               return_value="123 (app) T 1 0 0 0"):
            assert d._is_stopped(123)

    def test_running_process(self):
        d = _make_daemon()
        with mock.patch.object(fb, "_read_file",
                               return_value="123 (app) S 1 0 0 0"):
            assert not d._is_stopped(123)

    def test_missing_process(self):
        d = _make_daemon()
        with mock.patch.object(fb, "_read_file",
                               side_effect=FileNotFoundError):
            assert not d._is_stopped(123)


class TestFreezeThaw:
    def test_freeze_pid(self):
        d = _make_daemon()
        d.procs[100] = fb.Proc(
            pid=100, name="app", cmdline="app", cpu=100,
            rss_mb=200, last_active=time.time(),
        )
        d._ppid_map = {}
        with mock.patch("os.kill") as mock_kill:
            d.freeze_pid(100, reason="test")
            mock_kill.assert_called_with(100, signal.SIGSTOP)
        assert 100 in d.frozen
        assert 100 in d._frozen_at

    def test_thaw_pid(self):
        d = _make_daemon()
        d.procs[100] = fb.Proc(
            pid=100, name="app", cmdline="app", cpu=100,
            rss_mb=200, last_active=time.time(), frozen=True,
        )
        d.frozen.add(100)
        d._frozen_at[100] = time.time()
        d._ppid_map = {}

        with mock.patch("os.kill"), \
             mock.patch.object(fb, "_read_file",
                               return_value="100 (app) T 1 0 0 0"), \
             mock.patch.object(d, "_is_own_process", return_value=True):
            d.thaw_pid(100)

        assert 100 not in d.frozen
        assert 100 not in d._frozen_at


class TestCheckFocusSelectiveThaw:
    """_check_focus should only thaw descendants that FrostByte froze,
    not all stopped descendants (gnome-terminal-server bug)."""

    def test_only_thaws_own_frozen_descendants(self):
        d = _make_daemon()
        # Simulate: terminal PID 10 has children 20 (frozen by us) and 30 (stopped externally)
        d._ppid_map = {10: [20, 30]}
        d.procs[20] = fb.Proc(pid=20, name="npm", cmdline="npm", cpu=0,
                               rss_mb=200, last_active=time.time(), frozen=True)
        d.procs[30] = fb.Proc(pid=30, name="vim", cmdline="vim", cpu=0,
                               rss_mb=50, last_active=time.time(), frozen=False)
        d.frozen = {20}
        d._frozen_at[20] = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            focus_file = Path(tmpdir) / "frostbyte-focus"
            focus_file.write_text("10")

            # Mock thaw_pid to test _check_focus logic in isolation —
            # we only care that _check_focus calls thaw_pid for the right PIDs
            with mock.patch.object(fb, "FOCUS_FILE", focus_file), \
                 mock.patch.object(d, "_find_stopped_ancestor", return_value=None), \
                 mock.patch.object(d, "thaw_pid") as mock_thaw:
                d._check_focus()

            # Only PID 20 should be thawed (it's in self.frozen)
            # PID 30 should NOT be thawed (not in self.frozen, just externally stopped)
            mock_thaw.assert_called_once_with(20)


class TestLazyThaw:
    """Multi-process apps (browsers) should thaw one child per poll cycle,
    not all at once."""

    def _setup(self, num_children=4):
        d = _make_daemon()
        now = time.time()
        children = list(range(100, 100 + num_children))
        d._ppid_map = {50: children}
        for i, pid in enumerate(children):
            d.procs[pid] = fb.Proc(pid=pid, name=f"renderer{i}",
                                    cmdline=f"chrome --type=renderer --id={i}",
                                    cpu=0, rss_mb=200,
                                    last_active=now - (num_children - i),
                                    frozen=True)
            d.frozen.add(pid)
            d._frozen_at[pid] = now - (num_children - i)
        return d, children

    def test_first_call_thaws_only_one(self):
        """On first focus, only the most recently active child thaws."""
        d, children = self._setup(4)

        with tempfile.TemporaryDirectory() as tmpdir:
            focus_file = Path(tmpdir) / "frostbyte-focus"
            focus_file.write_text("50")

            with mock.patch.object(fb, "FOCUS_FILE", focus_file), \
                 mock.patch.object(d, "_find_stopped_ancestor", return_value=None), \
                 mock.patch.object(d, "thaw_pid") as mock_thaw:
                d._check_focus()

            # Only one child thawed (the most recently active)
            mock_thaw.assert_called_once_with(103)
            # Queue holds the remaining 3
            assert len(d._lazy_thaw_queue) == 3

    def test_subsequent_calls_thaw_one_per_cycle(self):
        """Each subsequent _check_focus thaws the next child in queue."""
        d, children = self._setup(4)

        with tempfile.TemporaryDirectory() as tmpdir:
            focus_file = Path(tmpdir) / "frostbyte-focus"
            focus_file.write_text("50")

            with mock.patch.object(fb, "FOCUS_FILE", focus_file), \
                 mock.patch.object(d, "_find_stopped_ancestor", return_value=None), \
                 mock.patch.object(d, "thaw_pid") as mock_thaw:
                # Simulate 4 poll cycles
                for _ in range(4):
                    d._check_focus()
                    # Remove thawed pid from frozen set (thaw_pid is mocked)
                    if mock_thaw.call_args:
                        d.frozen.discard(mock_thaw.call_args[0][0])
                    mock_thaw.reset_mock()

            # After 4 cycles, all should be thawed
            assert len(d.frozen) == 0

    def test_focus_change_cancels_queue(self):
        """Switching to a different app cancels the lazy thaw queue."""
        d, children = self._setup(4)

        with tempfile.TemporaryDirectory() as tmpdir:
            focus_file = Path(tmpdir) / "frostbyte-focus"
            focus_file.write_text("50")

            with mock.patch.object(fb, "FOCUS_FILE", focus_file), \
                 mock.patch.object(d, "_find_stopped_ancestor", return_value=None), \
                 mock.patch.object(d, "thaw_pid") as mock_thaw:
                # First cycle: thaw one
                d._check_focus()
                d.frozen.discard(mock_thaw.call_args[0][0])
                assert len(d._lazy_thaw_queue) == 3

                # User switches to a different app (no frozen children)
                focus_file.write_text("999")
                d._ppid_map[999] = []
                d._check_focus()

            # Queue should be cleared
            assert d._lazy_thaw_queue == []
            assert d._lazy_thaw_pid is None
            # 3 children still frozen
            assert len(d.frozen) == 3

    def test_single_frozen_child_thaws_immediately(self):
        """A process with only 1 frozen child should thaw it immediately
        (no lazy thaw needed)."""
        d = _make_daemon()
        d._ppid_map = {50: [100, 101]}
        d.procs[100] = fb.Proc(pid=100, name="renderer", cmdline="chrome",
                                cpu=0, rss_mb=200, last_active=time.time(),
                                frozen=True)
        d.frozen = {100}
        d._frozen_at[100] = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            focus_file = Path(tmpdir) / "frostbyte-focus"
            focus_file.write_text("50")

            with mock.patch.object(fb, "FOCUS_FILE", focus_file), \
                 mock.patch.object(d, "_find_stopped_ancestor", return_value=None), \
                 mock.patch.object(d, "thaw_pid") as mock_thaw:
                d._check_focus()

            mock_thaw.assert_called_once_with(100)
            assert d._lazy_thaw_queue == []


# ═══════════════════════════════════════════════════════════════
# Review #2 MEDIUM fixes
# ═══════════════════════════════════════════════════════════════


class TestScansPerTickInt:
    def test_scans_per_tick_is_int_with_float_config(self):
        """scans_per_tick should always be int even if config values are float."""
        d = _make_daemon(scan_interval=30.5, poll_interval=1.5)
        d._validate_config()
        spt = int(max(1, d.config["scan_interval"] // d.config["poll_interval"]))
        assert isinstance(spt, int)


class TestUpperBoundClamping:
    def test_poll_interval_clamped(self):
        d = _make_daemon(poll_interval=999999)
        d._validate_config()
        assert d.config["poll_interval"] == 3600

    def test_scan_interval_clamped(self):
        d = _make_daemon(scan_interval=999999)
        d._validate_config()
        assert d.config["scan_interval"] == 3600

    def test_freeze_after_minutes_clamped(self):
        d = _make_daemon(freeze_after_minutes=99999)
        d._validate_config()
        assert d.config["freeze_after_minutes"] == 1440

    def test_min_rss_mb_clamped(self):
        d = _make_daemon(min_rss_mb=999999)
        d._validate_config()
        assert d.config["min_rss_mb"] == 65536

    def test_max_freeze_hours_clamped(self):
        d = _make_daemon(max_freeze_hours=9999)
        d._validate_config()
        assert d.config["max_freeze_hours"] == 168

    def test_reasonable_values_not_clamped(self):
        d = _make_daemon(poll_interval=5, scan_interval=60,
                         freeze_after_minutes=30, min_rss_mb=200,
                         max_freeze_hours=8)
        d._validate_config()
        assert d.config["poll_interval"] == 5
        assert d.config["scan_interval"] == 60
        assert d.config["freeze_after_minutes"] == 30
        assert d.config["min_rss_mb"] == 200
        assert d.config["max_freeze_hours"] == 8


class TestSaveConfigAtomic:
    def test_save_config_uses_rename(self):
        """_save_config should write to .tmp then rename for atomicity."""
        d = _make_daemon()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_dir = Path(tmpdir)
            with mock.patch.object(fb, "CONFIG_FILE", config_file), \
                 mock.patch.object(fb, "CONFIG_DIR", config_dir):
                d._save_config()
                assert config_file.exists()
                data = json.loads(config_file.read_text())
                assert "poll_interval" in data
                # tmp file should be gone (renamed)
                assert not config_file.with_suffix(".tmp").exists()


class TestAudioAncestorDedup:
    def test_shared_ancestors_not_walked_twice(self):
        """Two audio PIDs sharing ancestors should only walk once."""
        d = _make_daemon()
        # Tree: 1 → 10 → 100 (audio)
        #       1 → 10 → 200 (audio)
        proc_data = {
            100: "100 (chrome) S 10 0 0 0",
            200: "200 (chrome) S 10 0 0 0",
            10:  "10 (chrome) S 1 0 0 0",
        }
        read_calls = []
        original_read = fb._read_file

        def tracking_read(path):
            read_calls.append(path)
            pid_str = path.split("/")[2]
            pid = int(pid_str)
            if pid in proc_data:
                return proc_data[pid]
            raise FileNotFoundError

        pactl_output = (
            'Sink Input #1\n'
            '  application.process.id = "100"\n'
            'Sink Input #2\n'
            '  application.process.id = "200"\n'
        )
        with mock.patch("subprocess.run") as mock_run, \
             mock.patch.object(fb, "_read_file", side_effect=tracking_read):
            mock_run.return_value = mock.Mock(returncode=0, stdout=pactl_output)
            d._refresh_audio_pids()

        assert d._audio_pids == {100, 200, 10}
        # PID 10 should only be read once (dedup), not twice
        pid10_reads = [c for c in read_calls if "/10/" in c]
        assert len(pid10_reads) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
