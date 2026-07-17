# Ptolemy SERVER_SPEC.md
*Living document. Do not instantiate server infrastructure until HyperDatabase schema and Flutter client shape are finalized.*

---

## Status
**BLOCKED** on:
1. Flutter client WebSocket contract (client shape in progress)
2. Callimachus / HyperDatabase schema finalization (primary data layer)

Do not allocate hosting space or write server code until both are resolved.

---

## Architecture Overview

```
[Flutter Client] ←──WebSocket──→ [Ptolemy Worker] ←──→ [Callimachus/HyperDatabase]
                                        ↑
                                  [Mouseion/Flask]
                                  thewanderinggod.tech
```

Two server processes, not one:
- **Mouseion** — Flask, web-facing, HTTP/HTTPS, static + templated content
- **Ptolemy Worker** — headless, job queue, C/O streaming, WebSocket only

They do not share a process. Mouseion delegates compute to the Worker via internal socket.

---

## Transport

- **Protocol:** Private WebSocket (wss://)
- **Why not UDP:** Screen dimension negotiation and C/O sequencing require a stateful channel. UDP is connectionless — session metadata (terminal dimensions, mode state) would require a separate handshake layer, netting zero savings over WebSocket.
- **Why WebSocket over ZeroMQ:** Flutter has first-class WebSocket support. ZeroMQ requires native bindings per platform — adds build complexity with no gain at this scale.
- **Auth:** Token-based. Single shared secret for private use. No OAuth overhead.

---

## WebSocket Message Contract (Draft)

All messages are JSON frames. Direction: C = Client, S = Server.

```json
// C → S: Command submission
{ "type": "command", "mode": "ptolemy|python|shell|root", "payload": "...", "session_id": "..." }

// S → C: Output stream chunk
{ "type": "output", "chunk": "...", "stream": "stdout|stderr", "session_id": "..." }

// S → C: Output complete
{ "type": "done", "exit_code": 0, "session_id": "..." }

// C → S: Dimension handshake
{ "type": "dimensions", "cols": 80, "rows": 25 }

// S → C: Dimension acknowledged
{ "type": "dimensions_ack", "cols": 80, "rows": 25 }

// S → C: Error
{ "type": "error", "code": "...", "message": "..." }
```

Session IDs are HyperWebster labels (consistent with Callimachus addressing).

---

## Callimachus Interface

The Worker does not query the database directly. All data I/O routes:

```
Worker → Callimachus API → HyperDatabase (SQLite) → JSON shards
```

Callimachus exposes internal Python API only (not HTTP). The Worker imports Callimachus as a module.

---

## Hosting Constraints

- Hosting space is finite. No superfluous dependencies.
- Dead stack (do not reinstall): Apache2, PHP, phpMyAdmin, MySQL, Dropbox
- Live stack (when ready): Flask, SQLite, rclone (Drive sync), openssh-server, git
- Server build is deferred. When built, it gets one clean install — not iterative debris.

---

## TODO
- [ ] Finalize Flutter WebSocket client shape
- [ ] Finalize HyperDatabase schema (Callimachus)
- [ ] Define Ptolemy Worker job queue (in-memory queue vs. persistent)
- [ ] Write `Mouseion/server.py` skeleton
- [ ] Write `Ptolemy Worker/worker.py` skeleton
- [ ] TLS cert strategy (Let's Encrypt vs. self-signed for private use)
- [ ] LSH_Datatype / Hermitian self-adjoint operator — mathematical rigor review (see LSH TODO)

---

*Last updated: 2026-05-02*
