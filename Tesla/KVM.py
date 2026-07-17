#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Tesla/KVM.py — Fake KVM over punched UDP channel
=================================================
Transmits local mouse movements and keypresses to a remote Ptolemy node.
No VNC overhead — raw input events only.

Packet format (12 bytes, struct '!BBhhHI'):
    type   : uint8   0=mouse_move, 1=mouse_btn, 2=key, 3=ping
    flags  : uint8   button mask / key modifiers / direction (press=0x80)
    x      : int16   dx for move, absolute x for click
    y      : int16   dy for move, absolute y for click
    key    : uint16  Qt key code (type=2), unused otherwise
    seq    : uint32  sequence number — receiver drops stale packets

Server side (Tesla/KVMServer.py, runs on remote):
    Receives packets, applies via python-xlib or uinput.
    Sends ACK pings back to keep NAT hole alive.

Heartbeat: 5s ping to keep NAT table entry open.

VNC fallback:
    If channel fails, call open_vnc_fallback(url).
    Caller (Ptolemy) routes that to TreasureHunt via PtolBus.
"""

import socket
import struct
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal


# ── Packet definition ─────────────────────────────────────────────────────────

KVM_PACKET       = struct.Struct('!BBhhHI')   # 12 bytes, network byte order
KVM_PACKET_SIZE  = KVM_PACKET.size            # 12

# Packet types
TYPE_MOUSE_MOVE = 0
TYPE_MOUSE_BTN  = 1
TYPE_KEY        = 2
TYPE_PING       = 3

# Flag bits
FLAG_PRESSED    = 0x80


# ── KVM receiver thread (server side) ────────────────────────────────────────

class KVMServer(QThread):
    """
    Runs on the remote machine. Receives KVM packets and applies them
    via python-xlib or uinput.
    Standalone: python3 -m Tesla.KVM --server --port 23233
    """

    packet_received = pyqtSignal(int, int, int, int, int, int)  # type,flags,x,y,key,seq

    def __init__(self, host='0.0.0.0', port=23233, parent=None):
        super().__init__(parent)
        self.host     = host
        self.port     = port
        self._running = False
        self._last_seq = 0

    def run(self):
        self._running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind((self.host, self.port))

        while self._running:
            try:
                data, addr = sock.recvfrom(KVM_PACKET_SIZE)
                if len(data) < KVM_PACKET_SIZE:
                    continue
                ptype, flags, x, y, key, seq = KVM_PACKET.unpack(data[:KVM_PACKET_SIZE])

                # Drop out-of-order (allow wrap-around at 2^32)
                if seq != 0 and seq <= self._last_seq:
                    continue
                self._last_seq = seq

                self._apply(ptype, flags, x, y, key)
                self.packet_received.emit(ptype, flags, x, y, key, seq)

                # Send ACK ping back to keep hole open
                ack = KVM_PACKET.pack(TYPE_PING, 0, 0, 0, 0, seq)
                sock.sendto(ack, addr)

            except socket.timeout:
                continue
            except Exception:
                continue

        sock.close()

    def _apply(self, ptype, flags, x, y, key):
        """Apply received event to local X display via python-xlib or uinput."""
        if ptype == TYPE_PING:
            return

        try:
            self._apply_xlib(ptype, flags, x, y, key)
        except Exception:
            try:
                self._apply_uinput(ptype, flags, x, y, key)
            except Exception:
                pass

    def _apply_xlib(self, ptype, flags, x, y, key):
        from Xlib import display as Xdisplay, X
        from Xlib.ext.xtest import fake_input

        d = Xdisplay.Display()
        pressed = bool(flags & FLAG_PRESSED)

        if ptype == TYPE_MOUSE_MOVE:
            # Relative move
            root = d.screen().root
            info = root.query_pointer()
            new_x = max(0, info.root_x + x)
            new_y = max(0, info.root_y + y)
            fake_input(d, X.MotionNotify, x=new_x, y=new_y)

        elif ptype == TYPE_MOUSE_BTN:
            btn = (flags & 0x0F) or 1
            etype = X.ButtonPress if pressed else X.ButtonRelease
            fake_input(d, etype, detail=btn)

        elif ptype == TYPE_KEY:
            from Xlib.keysymdef import miscellany
            etype = X.KeyPress if pressed else X.KeyRelease
            # Qt key → X keysym is approximate; extend as needed
            fake_input(d, etype, detail=key & 0xFF)

        d.sync()

    def _apply_uinput(self, ptype, flags, x, y, key):
        """Fallback: apply via uinput (requires /dev/uinput access)."""
        import uinput
        pressed = bool(flags & FLAG_PRESSED)

        if ptype == TYPE_MOUSE_MOVE:
            with uinput.Device([uinput.REL_X, uinput.REL_Y]) as dev:
                dev.emit(uinput.REL_X, x)
                dev.emit(uinput.REL_Y, y)

        elif ptype == TYPE_MOUSE_BTN:
            btn_map = {1: uinput.BTN_LEFT, 2: uinput.BTN_MIDDLE, 3: uinput.BTN_RIGHT}
            btn = btn_map.get(flags & 0x0F, uinput.BTN_LEFT)
            with uinput.Device([btn]) as dev:
                dev.emit(btn, 1 if pressed else 0)

    def stop(self):
        self._running = False
        self.quit()
        self.wait(2000)


# ── KVM client (sender) ───────────────────────────────────────────────────────

class KVMClient(QObject):
    """
    Runs on the local machine inside Ptolemy.
    Sends input events to remote over punched UDP socket.

    Usage:
        kvm = KVMClient(parent=ptolemy)
        kvm.connect(remote_ip, remote_port, sock=punched_sock)
        kvm.send_mouse_move(dx, dy)
        kvm.send_key(Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, pressed=True)
    """

    connected    = pyqtSignal(str, int)   # ip, port
    disconnected = pyqtSignal()

    HEARTBEAT_MS = 5000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sock     = None
        self.remote   = None
        self.seq      = 0
        self.enabled  = False
        self.vnc_url  = None

        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(self.HEARTBEAT_MS)
        self._heartbeat.timeout.connect(self._ping)

    def connect(self, remote_ip, remote_port, sock=None):
        self.remote  = (remote_ip, remote_port)
        self.sock    = sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.enabled = True
        self._heartbeat.start()
        self.connected.emit(remote_ip, remote_port)

    def disconnect(self):
        self.enabled = False
        self._heartbeat.stop()
        self.remote  = None
        self.disconnected.emit()

    # ── Send helpers ──────────────────────────────────────────────────────────

    def send_mouse_move(self, dx, dy):
        self._send(TYPE_MOUSE_MOVE, 0, dx, dy, 0)

    def send_mouse_button(self, x, y, button, pressed):
        flags = (button & 0x0F) | (FLAG_PRESSED if pressed else 0)
        self._send(TYPE_MOUSE_BTN, flags, x, y, 0)

    def send_key(self, qt_key, modifiers, pressed):
        flags = (int(modifiers) & 0x7F) | (FLAG_PRESSED if pressed else 0)
        self._send(TYPE_KEY, flags, 0, 0, qt_key & 0xFFFF)

    def _ping(self):
        self._send(TYPE_PING, 0, 0, 0, 0)

    def _send(self, ptype, flags, x, y, key):
        if not self.enabled or not self.remote:
            return
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        try:
            pkt = KVM_PACKET.pack(ptype, flags, x, y, key, self.seq)
            self.sock.sendto(pkt, self.remote)
        except Exception:
            pass

    def open_vnc_fallback(self, url=None):
        """
        Signal to Ptolemy that KVM is down — it routes to TreasureHunt.
        Caller should connect kvm.disconnected to a handler that calls this.
        """
        target = url or self.vnc_url
        return target   # caller opens it in TreasureHunt tab


# ── Standalone server entry point ─────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--server' else 23233
    print(f'[KVMServer] Listening on 0.0.0.0:{port}')
    server = KVMServer(port=port)
    server.start()
    sys.exit(app.exec())
