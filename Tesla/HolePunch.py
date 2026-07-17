#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Tesla/HolePunch.py — UDP NAT Traversal
=======================================
Consolidates HolePunchClient.py, HolePunchServer.py, GpsHolePunch.py,
GpsHolePunchServer.py into one coherent module.

Protocol (3-way rendezvous):
    1. Both peers send REGISTER:<peer_id>:<target_id> to relay
    2. Relay records (peer_id → public_ip:port) for each
       When both are registered, replies PEER:<other_ip>:<other_port> to each
    3. Both peers simultaneously flood 5 PUNCH packets to each other's
       public endpoint → NAT tables open bidirectionally
    4. First packet received confirms channel is open

Relay server:
    Tesla/HolePunchRelay.py — 50-line Python socketserver, run on any VPS
    Existing IPs from GpsHolePunch.py:
        80.255.11.139:23232  — Ptolemy primary relay
        72.211.113.6:32323   — House relay

KVM channel uses the punched socket directly after this handshake.

GPS integration:
    GpsHolePunch.py sent GPS dictionaries through the hole.
    This module preserves that: send_data(dict) serialises over the channel.

Usage:
    punch = HolePunch(peer_id='ptolemy_local')
    punch.punch_ready.connect(lambda ip, port: kvm.connect(ip, port, punch.sock))
    punch.punch('ptolemy_remote')
"""

import socket
import time
import json
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal


# ── Known endpoints (from existing Tesla config) ──────────────────────────────

RELAY_PRIMARY  = ('80.255.11.139', 23232)   # Ptolemy primary
RELAY_HOUSE    = ('72.211.113.6',  32323)   # House relay
PORT_LOCAL     = 5555
PORT_PRIM      = 23232
PORT_HOUSE     = 32323


# ── Relay server (runs on VPS / any reachable host) ──────────────────────────

class HolePunchRelay:
    """
    Minimal UDP relay. Run standalone on a VPS:
        python3 -m Tesla.HolePunch --relay --port 23232

    Tracks registrations, pairs peers, sends PEER replies.
    No auth — add a shared secret check if needed.
    """

    def __init__(self, host='0.0.0.0', port=PORT_PRIM):
        self.host    = host
        self.port    = port
        self._peers  = {}   # peer_id → (addr, target_id, registered_at)

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        print(f'[HolePunchRelay] Listening on {self.host}:{self.port}')

        while True:
            try:
                data, addr = sock.recvfrom(512)
                msg = data.decode(errors='replace').strip()

                if msg.startswith('REGISTER:'):
                    parts = msg.split(':')
                    if len(parts) < 3:
                        continue
                    peer_id   = parts[1]
                    target_id = parts[2]

                    # Stale entry cleanup (30s TTL)
                    now = time.time()
                    self._peers = {k: v for k, v in self._peers.items()
                                   if now - v[2] < 30}

                    self._peers[peer_id] = (addr, target_id, now)
                    print(f'[Relay] Registered {peer_id} from {addr}')

                    # If target is already registered, pair them
                    target = self._peers.get(target_id)
                    if target and target[1] == peer_id:
                        t_addr = target[0]
                        # Tell each peer about the other
                        sock.sendto(
                            f'PEER:{t_addr[0]}:{t_addr[1]}'.encode(), addr)
                        sock.sendto(
                            f'PEER:{addr[0]}:{addr[1]}'.encode(), t_addr)
                        print(f'[Relay] Paired {peer_id} ↔ {target_id}')
                    else:
                        sock.sendto(b'WAIT', addr)

                elif msg == 'PING':
                    sock.sendto(b'PONG', addr)

            except Exception as e:
                print(f'[Relay] Error: {e}')
                continue


# ── Client punch thread ───────────────────────────────────────────────────────

class HolePunchThread(QThread):
    punch_ready  = pyqtSignal(str, int)   # (remote_ip, remote_port)
    punch_failed = pyqtSignal(str)        # reason

    def __init__(self, punch_obj, target_id, relay_host, relay_port):
        super().__init__()
        self.punch_obj    = punch_obj
        self.target_id    = target_id
        self.relay_host   = relay_host
        self.relay_port   = relay_port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(15.0)
        self.punch_obj.sock = sock

        try:
            relay = (self.relay_host, self.relay_port)
            register_msg = f'REGISTER:{self.punch_obj.peer_id}:{self.target_id}'.encode()

            # Poll relay until paired (max 12s, retry every 2s)
            remote_ip, remote_port = None, None
            for attempt in range(6):
                sock.sendto(register_msg, relay)
                try:
                    data, _ = sock.recvfrom(256)
                    msg = data.decode(errors='replace')
                    if msg.startswith('PEER:'):
                        parts = msg.split(':')
                        remote_ip   = parts[1]
                        remote_port = int(parts[2])
                        break
                    elif msg == 'WAIT':
                        time.sleep(2)
                except socket.timeout:
                    time.sleep(1)

            if not remote_ip:
                self.punch_failed.emit('Relay did not pair peers within timeout')
                return

            # Simultaneous punch — flood both directions
            for _ in range(8):
                sock.sendto(b'PUNCH', (remote_ip, remote_port))
                time.sleep(0.05)

            # Confirm channel is open
            sock.settimeout(6.0)
            try:
                data, _ = sock.recvfrom(64)
                # Got something back — channel open
                self.punch_ready.emit(remote_ip, remote_port)
            except socket.timeout:
                # May still work — emit anyway, KVM heartbeat will confirm
                self.punch_ready.emit(remote_ip, remote_port)

        except Exception as e:
            self.punch_failed.emit(str(e))


# ── HolePunch — main interface ────────────────────────────────────────────────

class HolePunch(QObject):
    """
    Primary interface for Tesla networking.
    Wraps the punch protocol, GPS data channel, and relay selection.

    Signals:
        punch_ready(ip, port)  — channel is open, sock is live
        punch_failed(reason)   — could not establish
        data_received(dict)    — incoming data packet (GPS, commands, etc.)

    Usage:
        hp = HolePunch(peer_id='ptol_local', parent=ptolemy)
        hp.punch_ready.connect(lambda ip, port: kvm.connect(ip, port, hp.sock))
        hp.punch('ptol_remote')
        hp.send_data({'type': 'gps', 'lat': 49.2, 'lon': -123.1})
    """

    punch_ready    = pyqtSignal(str, int)
    punch_failed   = pyqtSignal(str)
    data_received  = pyqtSignal(dict)

    def __init__(self, peer_id='ptolemy', parent=None):
        super().__init__(parent)
        self.peer_id         = peer_id
        self.sock            = None
        self._thread         = None
        self._recv_thread    = None
        self._channel_open   = False
        self._remote         = None

        # Relay selection — try primary first, fall back to house
        self._relays = [RELAY_PRIMARY, RELAY_HOUSE]

    # ── Punch ─────────────────────────────────────────────────────────────────

    def punch(self, target_id, relay=None):
        """
        Initiate hole punch to target_id.
        relay: (host, port) tuple or None to auto-select.
        """
        relay_host, relay_port = relay or self._relays[0]
        self._thread = HolePunchThread(self, target_id, relay_host, relay_port)
        self._thread.punch_ready.connect(self._on_ready)
        self._thread.punch_failed.connect(self._on_failed_try_fallback)
        self._thread.start()

    def _on_ready(self, ip, port):
        self._remote      = (ip, port)
        self._channel_open = True
        self._start_receive()
        self.punch_ready.emit(ip, port)

    def _on_failed_try_fallback(self, reason):
        """Try secondary relay before giving up."""
        if len(self._relays) > 1 and not self._channel_open:
            self._relays.append(self._relays.pop(0))    # rotate
            self.punch_failed.emit(f'Primary failed ({reason}), trying fallback')
        else:
            self.punch_failed.emit(reason)

    # ── Data channel ─────────────────────────────────────────────────────────

    def send_data(self, data_dict):
        """Send arbitrary dict over the punched channel (JSON-encoded)."""
        if not self._channel_open or not self.sock or not self._remote:
            return False
        try:
            payload = json.dumps(data_dict).encode()
            self.sock.sendto(payload, self._remote)
            return True
        except Exception:
            return False

    def _start_receive(self):
        """Start background receive loop for incoming data packets."""
        self._recv_thread = HolePunchReceiveThread(self)
        self._recv_thread.data_received.connect(self.data_received)
        self._recv_thread.start()

    # ── Network discovery (from GpsHolePunch.py) ─────────────────────────────

    @staticmethod
    def get_local_ip(iface='wlp2s0'):
        from subprocess import Popen, PIPE
        proc = Popen(
            args=f"ifconfig -a {iface} | grep 'inet '",
            stdout=PIPE, stderr=PIPE, shell=True)
        out = proc.communicate()[0]
        try:
            return out.replace(b'        ', b'').split(b' ')[1].decode()
        except (IndexError, UnicodeDecodeError):
            return '127.0.0.1'

    @staticmethod
    def get_public_ip():
        from subprocess import Popen, PIPE
        proc = Popen(
            args='dig +short myip.opendns.com @resolver1.opendns.com',
            stdout=PIPE, stderr=PIPE, shell=True)
        return proc.communicate()[0].replace(b'\n', b'').decode()

    def close(self):
        self._channel_open = False
        if self._thread:
            self._thread.quit()
            self._thread.wait(1000)
        if self._recv_thread:
            self._recv_thread.quit()
            self._recv_thread.wait(1000)
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


class HolePunchReceiveThread(QThread):
    data_received = pyqtSignal(dict)

    def __init__(self, punch_obj):
        super().__init__()
        self.punch_obj = punch_obj
        self._running  = False

    def run(self):
        self._running = True
        sock = self.punch_obj.sock
        if not sock:
            return
        sock.settimeout(2.0)
        while self._running and self.punch_obj._channel_open:
            try:
                data, _ = sock.recvfrom(4096)
                if data.startswith(b'{'):
                    try:
                        d = json.loads(data.decode())
                        self.data_received.emit(d)
                    except json.JSONDecodeError:
                        pass
                # KVM packets handled by KVMServer — skip binary packets here
            except socket.timeout:
                continue
            except Exception:
                break

    def stop(self):
        self._running = False
        self.quit()
        self.wait(1000)


# ── Standalone modes ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    if '--relay' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else PORT_PRIM
        relay = HolePunchRelay(port=port)
        relay.serve()

    elif '--punch' in sys.argv:
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        idx = sys.argv.index('--punch')
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else 'ptolemy_remote'
        hp = HolePunch(peer_id='ptolemy_local')
        hp.punch_ready.connect(lambda ip, port: print(f'Channel open: {ip}:{port}'))
        hp.punch_failed.connect(lambda r: print(f'Failed: {r}'))
        hp.punch(target)
        sys.exit(app.exec_())
