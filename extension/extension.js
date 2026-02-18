import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Clutter from 'gi://Clutter';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

function getUid() {
    try {
        const [ok, contents] = GLib.file_get_contents('/proc/self/status');
        const m = new TextDecoder().decode(contents).match(/^Uid:\t(\d+)/m);
        return m ? m[1] : '1000';
    } catch (_) {
        return '1000';
    }
}

const UID = getUid();
const FOCUS_FILE = `/tmp/freezer-focus-${UID}`;
const STATUS_FILE = `/tmp/freezer-status-${UID}.json`;
const THAW_FILE = `/tmp/freezer-thaw-${UID}`;

export default class FreezerExtension extends Extension {
    enable() {
        // --- Focus tracking (existing logic) ---
        this._focusId = global.display.connect('notify::focus-window', () => {
            const win = global.display.focus_window;
            if (win) this._writeFocus(win.get_pid());
        });

        this._captureId = global.stage.connect('captured-event', (actor, event) => {
            if (event.type() === Clutter.EventType.BUTTON_PRESS) {
                const [x, y] = event.get_coords();
                const pid = this._windowPidAtPos(x, y);
                if (pid > 0) this._writeFocus(pid);
            }
            return Clutter.EVENT_PROPAGATE;
        });

        // --- Panel indicator ---
        this._indicator = new PanelMenu.Button(0.0, 'Freezer', false);

        this._icon = new St.Label({
            text: '\u2744',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'system-status-icon',
            style: 'font-size: 16px; padding: 0 4px;',
        });
        this._indicator.add_child(this._icon);

        this._buildMenu();

        this._indicator.menu.connect('open-state-changed', (_menu, open) => {
            if (open) {
                this._refresh();
                this._pollId = GLib.timeout_add_seconds(
                    GLib.PRIORITY_DEFAULT, 3, () => {
                        if (this._indicator?.menu?.isOpen) {
                            this._refresh();
                            return GLib.SOURCE_CONTINUE;
                        }
                        return GLib.SOURCE_REMOVE;
                    });
            } else if (this._pollId) {
                GLib.source_remove(this._pollId);
                this._pollId = null;
            }
        });

        Main.panel.addToStatusArea('freezer', this._indicator);
    }

    _buildMenu() {
        const menu = this._indicator.menu;
        menu.removeAll();

        // Toggle
        this._toggleItem = new PopupMenu.PopupSwitchMenuItem('Freezer', true);
        this._toggleItem.connect('toggled', (_item, state) => {
            const cmd = state ? 'start' : 'stop';
            try {
                GLib.spawn_command_line_async(
                    `systemctl --user ${cmd} freezer.service`);
            } catch (_) {}
        });
        menu.addMenuItem(this._toggleItem);

        menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Frozen section
        this._frozenSection = new PopupMenu.PopupMenuSection();
        menu.addMenuItem(this._frozenSection);

        // Footer
        menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this._footerItem = new PopupMenu.PopupMenuItem('', {reactive: false});
        this._footerItem.label.style = 'font-style: italic; color: #999;';
        menu.addMenuItem(this._footerItem);
    }

    _refresh() {
        try {
            const [ok, contents] = GLib.file_get_contents(STATUS_FILE);
            const data = JSON.parse(new TextDecoder().decode(contents));

            this._toggleItem.setToggleState(data.active !== false);

            this._frozenSection.removeAll();

            if (data.frozen && data.frozen.length > 0) {
                for (const proc of data.frozen) {
                    const item = new PopupMenu.PopupMenuItem(
                        `\u2744  ${proc.name}   ${proc.rss_mb} MB`);
                    item.connect('activate', () => {
                        this._requestThaw(proc.pid);
                    });
                    this._frozenSection.addMenuItem(item);
                }
                this._footerItem.label.text =
                    `Saved: ~${data.saved_mb} MB`;
            } else {
                const empty = new PopupMenu.PopupMenuItem(
                    'No frozen processes', {reactive: false});
                empty.label.style = 'font-style: italic; color: #888;';
                this._frozenSection.addMenuItem(empty);
                this._footerItem.label.text = '';
            }

            const count = data.frozen ? data.frozen.length : 0;
            this._icon.text = count > 0 ? `\u2744${count}` : '\u2744';

        } catch (_) {
            this._frozenSection.removeAll();
            const offline = new PopupMenu.PopupMenuItem(
                'Daemon not running', {reactive: false});
            offline.label.style = 'font-style: italic; color: #c62828;';
            this._frozenSection.addMenuItem(offline);
            this._toggleItem.setToggleState(false);
            this._icon.text = '\u2744';
            this._footerItem.label.text = '';
        }
    }

    _requestThaw(pid) {
        try {
            GLib.file_set_contents(THAW_FILE, `${pid}\n`);
        } catch (_) {}
    }

    _windowPidAtPos(x, y) {
        const actors = global.get_window_actors();
        for (let i = actors.length - 1; i >= 0; i--) {
            const win = actors[i].meta_window;
            if (!win) continue;
            if (win.get_window_type() !== Meta.WindowType.NORMAL) continue;
            const rect = win.get_frame_rect();
            if (x >= rect.x && x < rect.x + rect.width &&
                y >= rect.y && y < rect.y + rect.height)
                return win.get_pid();
        }
        return -1;
    }

    _writeFocus(pid) {
        if (pid > 0) {
            try {
                GLib.file_set_contents(FOCUS_FILE, `${pid}\n`);
            } catch (_) {}
        }
    }

    disable() {
        if (this._focusId) {
            global.display.disconnect(this._focusId);
            this._focusId = null;
        }
        if (this._captureId) {
            global.stage.disconnect(this._captureId);
            this._captureId = null;
        }
        if (this._pollId) {
            GLib.source_remove(this._pollId);
            this._pollId = null;
        }
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
        try { GLib.unlink(FOCUS_FILE); } catch (_) {}
    }
}
