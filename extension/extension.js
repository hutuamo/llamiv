import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import Shell from 'gi://Shell';
import Meta from 'gi://Meta';
import Clutter from 'gi://Clutter';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

// --- IPC Client ---
class IpcClient {
    constructor() {
        this._sockPath = '/tmp/llamiv.sock';
    }

    async send(command, params = {}) {
        return new Promise((resolve, reject) => {
            try {
                const address = Gio.UnixSocketAddress.new(this._sockPath);
                const client = new Gio.SocketClient();
                
                client.connect_async(address, null, (obj, res) => {
                    try {
                        const conn = client.connect_finish(res);
                        const output = conn.get_output_stream();
                        const input = conn.get_input_stream();
                        
                        const msg = JSON.stringify({ command, ...params });
                        const msgBytes = new TextEncoder().encode(msg);
                        const lenBytes = new Uint8Array(4);
                        const view = new DataView(lenBytes.buffer);
                        view.setUint32(0, msgBytes.length, false); 
                        
                        output.write_all(lenBytes, null);
                        output.write_all(msgBytes, null);
                        
                        const respLenBytes = input.read_bytes(4, null).get_data();
                        if (!respLenBytes) {
                            reject(new Error("Empty response"));
                            return;
                        }
                        const respLenView = new DataView(respLenBytes.buffer);
                        const respLen = respLenView.getUint32(0, false);
                        
                        const respData = input.read_bytes(respLen, null).get_data();
                        const respStr = new TextDecoder().decode(respData);
                        resolve(JSON.parse(respStr));
                        
                        conn.close(null);
                    } catch (e) {
                        reject(e);
                    }
                });
            } catch (e) {
                reject(e);
            }
        });
    }
}

// --- Service Manager ---
class ServiceManager {
    constructor(extensionDir) {
        this._dir = extensionDir;
        this._proc = null;
    }

    start() {
        const serviceDir = this._dir.get_child('service');
        const mainScript = serviceDir.get_child('main.py').get_path();
        
        try {
            const [success, pid] = GLib.spawn_async(
                null,
                ['python3', mainScript],
                null,
                GLib.SpawnFlags.SEARCH_PATH | GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                null
            );

            if (success) {
                this._proc = pid;
                console.log(`[Llamiv] Service started with PID ${pid}`);
            }
        } catch (e) {
            console.error(`[Llamiv] Error spawning service: ${e}`);
        }
    }

    stop() {
        if (this._proc) {
            GLib.spawn_command_line_async(`kill ${this._proc}`);
            this._proc = null;
        }
    }
}

// --- Overlay Manager ---
class OverlayManager {
    constructor(ipc) {
        this._ipc = ipc;
        this._active = false;
        this._mode = null; 
        
        this._container = new St.Widget({
            name: 'LlamivOverlay',
            visible: false,
            reactive: true,
            x: 0,
            y: 0,
        });
        
        Main.layoutManager.uiGroup.add_child(this._container);
        
        this._container.connect('key-press-event', (actor, event) => {
            return this._handleKeyPress(event);
        });
        
        this._scrollIndicator = new St.Label({
            text: ' SCROLL MODE (HJKL to scroll, ESC to exit) ',
            style_class: 'llamiv-hint-label',
            style: 'background-color: rgba(0,0,0,0.8); color: white; margin-bottom: 20px;',
            visible: false
        });
        this._container.add_child(this._scrollIndicator);
        
        this._labels = [];
        this._elements = [];
        this._inputBuffer = "";
    }

    _updateGeometry() {
        const monitor = Main.layoutManager.primaryMonitor;
        this._container.set_position(monitor.x, monitor.y);
        this._container.set_size(monitor.width, monitor.height);
        
        if (this._scrollIndicator.visible) {
            this._scrollIndicator.set_position(
                monitor.width / 2 - 150, 
                monitor.height - 100
            );
        }
    }

    async activateHintMode() {
        if (this._active) return;
        
        this._mode = 'HINT';
        this._updateGeometry();
        this._container.visible = true;
        this._scrollIndicator.visible = false;
        
        try {
            const resp = await this._ipc.send('SCAN');
            if (resp.status === 'success') {
                this.showHints(resp.elements);
            } else {
                console.error("[Llamiv] Scan failed");
                this.hide();
            }
        } catch (e) {
            console.error(`[Llamiv] IPC error: ${e}`);
            this.hide();
        }
    }
    
    activateScrollMode() {
        if (this._active) return;
        
        this._mode = 'SCROLL';
        this._updateGeometry();
        this._container.visible = true;
        this._scrollIndicator.visible = true;
        this.clearHints();
        
        if (!Main.pushModal(this._container)) {
            console.warn("[Llamiv] Failed to push modal for scroll");
            this.hide();
        } else {
            this._active = true;
        }
    }

    showHints(elements) {
        this.clearHints();
        this._elements = elements;
        
        elements.forEach((el, index) => {
            const labelText = this._generateLabel(index);
            const label = new St.Label({
                text: labelText,
                style_class: 'llamiv-hint-label',
            });
            label.set_position(el.x, el.y);
            this._container.add_child(label);
            this._labels.push({ actor: label, text: labelText, elementId: el.id });
        });
        
        if (!Main.pushModal(this._container)) {
            console.warn("[Llamiv] Failed to push modal");
            this.hide();
        } else {
            this._active = true;
            this._inputBuffer = "";
        }
    }

    _generateLabel(index) {
        const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        if (index < 26) return chars[index];
        const first = Math.floor(index / 26) - 1;
        const second = index % 26;
        return chars[first] + chars[second];
    }

    _handleKeyPress(event) {
        const symbol = event.get_key_symbol();
        
        if (symbol === Clutter.KEY_Escape) {
            this.hide();
            return Clutter.EVENT_STOP;
        }
        
        if (this._mode === 'SCROLL') {
            const key = String.fromCharCode(symbol).toLowerCase();
            if (key === 'j') this._ipc.send('SCROLL', { direction: 'down' });
            if (key === 'k') this._ipc.send('SCROLL', { direction: 'up' });
            if (key === 'h') this._ipc.send('SCROLL', { direction: 'left' });
            if (key === 'l') this._ipc.send('SCROLL', { direction: 'right' });
            return Clutter.EVENT_STOP;
        }
        
        if (this._mode === 'HINT') {
            if (symbol === Clutter.KEY_BackSpace) {
                this._inputBuffer = this._inputBuffer.slice(0, -1);
                this._filterHints();
                return Clutter.EVENT_STOP;
            }

            const char = String.fromCharCode(symbol).toUpperCase();
            if (/[A-Z]/.test(char)) {
                this._inputBuffer += char;
                this._filterHints();
                return Clutter.EVENT_STOP;
            }
        }
        
        return Clutter.EVENT_STOP;
    }

    _filterHints() {
        const exactMatch = this._labels.find(l => l.text === this._inputBuffer);
        
        if (exactMatch) {
            this._triggerClick(exactMatch.elementId);
            this.hide();
            return;
        }
        
        this._labels.forEach(l => {
            if (l.text.startsWith(this._inputBuffer)) {
                l.actor.visible = true;
                l.actor.opacity = 255;
            } else {
                l.actor.visible = false;
            }
        });
    }

    async _triggerClick(elementId) {
        try {
            await this._ipc.send('CLICK', { id: elementId });
        } catch (e) {
            console.error(`[Llamiv] Click error: ${e}`);
        }
    }

    hide() {
        if (this._active) {
            Main.popModal(this._container);
            this._container.visible = false;
            this.clearHints();
            this._active = false;
            this._mode = null;
        }
    }
    
    clearHints() {
        this._labels.forEach(l => l.actor.destroy());
        this._labels = [];
        this._elements = [];
        this._inputBuffer = "";
    }

    destroy() {
        this.hide();
        this._container.destroy();
    }
}

// --- Main Extension ---
export default class LlamivExtension extends Extension {
    enable() {
        console.log('[Llamiv] Enabling...');
        
        this._settings = this.getSettings();
        
        this._service = new ServiceManager(this.dir);
        this._service.start();
        
        this._ipc = new IpcClient();
        this._overlay = new OverlayManager(this._ipc);
        
        Main.wm.addKeybinding(
            'activate-mode-key',
            this._settings,
            Meta.KeyBindingFlags.NONE,
            Shell.ActionMode.NORMAL,
            () => {
                this._overlay.activateHintMode();
            }
        );
        
        Main.wm.addKeybinding(
            'scroll-mode-key',
            this._settings,
            Meta.KeyBindingFlags.NONE,
            Shell.ActionMode.NORMAL,
            () => {
                this._overlay.activateScrollMode();
            }
        );
    }

    disable() {
        console.log('[Llamiv] Disabling...');
        
        Main.wm.removeKeybinding('activate-mode-key');
        Main.wm.removeKeybinding('scroll-mode-key');
        
        if (this._service) {
            this._service.stop();
            this._service = null;
        }
        if (this._overlay) {
            this._overlay.destroy();
            this._overlay = null;
        }
        this._ipc = null;
        this._settings = null;
    }
}
