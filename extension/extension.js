import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Clutter from 'gi://Clutter';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const FOCUS_FILE = '/tmp/freezer-focus';

export default class FreezerExtension extends Extension {
    enable() {
        this._focusId = global.display.connect('notify::focus-window', () => {
            const win = global.display.focus_window;
            if (win) this._writePid(win.get_pid());
        });

        // Capture phase — fires BEFORE event reaches the window,
        // so we detect clicks on frozen (unresponsive) windows too.
        this._captureId = global.stage.connect('captured-event', (actor, event) => {
            if (event.type() === Clutter.EventType.BUTTON_PRESS) {
                const [x, y] = event.get_coords();
                const pid = this._windowPidAtPos(x, y);
                if (pid > 0) this._writePid(pid);
            }
            return Clutter.EVENT_PROPAGATE;
        });
    }

    _windowPidAtPos(x, y) {
        const actors = global.get_window_actors();
        for (let i = actors.length - 1; i >= 0; i--) {
            const win = actors[i].meta_window;
            if (!win) continue;
            if (win.get_window_type() !== Meta.WindowType.NORMAL) continue;
            const rect = win.get_frame_rect();
            if (x >= rect.x && x < rect.x + rect.width &&
                y >= rect.y && y < rect.y + rect.height) {
                return win.get_pid();
            }
        }
        return -1;
    }

    _writePid(pid) {
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
        try { GLib.unlink(FOCUS_FILE); } catch (_) {}
    }
}
