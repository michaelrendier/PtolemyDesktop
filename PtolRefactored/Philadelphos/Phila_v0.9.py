#!/usr/bin/env python3
"""
Philadelphos/phila.py — Neural Architecture Slot
=================================================
The Philadelphos face manages all AI and language model interfaces.
This module defines the open slot for a pluggable neural architecture.

NEURAL_ARCHITECTURE is None until the user provides an implementation.
The SMNNIP reference implementation (ptolemy_core.py + LLM_Datatype_Cl.py)
is the canonical conforming implementation — protected by .gitignore.SSF
until Second Age publication.

Any community-supplied architecture must expose the PtolemyArchitectureInterface
contract defined below.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


# ─────────────────────────────────────────────────────────────────────────────
# INTERFACE CONTRACT
# Any plugged-in neural architecture must implement this.
# ─────────────────────────────────────────────────────────────────────────────

class PtolemyArchitectureInterface(ABC):
    """
    Minimum interface any neural architecture must satisfy to plug into Philadelphos.

    The SMNNIP reference implementation (ptolemy_core.py) is the canonical example.
    Community implementations should subclass this and implement all abstract methods.
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this architecture. e.g. 'JuliusCaesar'"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string. e.g. '0.1.0'"""
        ...

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @abstractmethod
    def load(self, checkpoint_path: Optional[str] = None) -> None:
        """
        Initialize the architecture. Load weights from checkpoint_path if provided.
        Must be called before any inference.
        """
        ...

    @abstractmethod
    def unload(self) -> None:
        """Release model weights and free memory."""
        ...

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """True if load() has been called and the model is ready for inference."""
        ...

    # ── Inference ─────────────────────────────────────────────────────────────

    @abstractmethod
    def encode(self, text: str, language: str = "en") -> Any:
        """
        Encode text into the model's internal semantic representation.
        Returns a representation that can be passed to decode() or compared.
        """
        ...

    @abstractmethod
    def decode(self, representation: Any, language: str = "en",
               max_tokens: int = 512) -> str:
        """
        Decode a semantic representation into output text.
        """
        ...

    @abstractmethod
    def respond(self, prompt: str, language: str = "en",
                max_tokens: int = 512) -> str:
        """
        Full encode → process → decode cycle. The primary chat interface.
        """
        ...

    # ── HyperWebster integration ──────────────────────────────────────────────

    @abstractmethod
    def lookup(self, word: str, language: str = "en") -> Optional[Dict]:
        """
        Look up a word in the architecture's knowledge store.
        Returns a SemanticWord-compatible dict or None if not found.
        """
        ...

    @abstractmethod
    def train_on_word(self, semantic_word: Dict) -> None:
        """
        Incorporate a SemanticWord JSON record into the model's knowledge.
        Must respect the Rabies Principle: first_encountered is read-only.
        """
        ...

    # ── Introspection ─────────────────────────────────────────────────────────

    def info(self) -> Dict[str, Any]:
        """Return a summary dict for display / logging."""
        return {
            "name": self.name,
            "version": self.version,
            "loaded": self.is_loaded,
        }


# ─────────────────────────────────────────────────────────────────────────────
# THE SLOT
# ─────────────────────────────────────────────────────────────────────────────

# This is the user-defined variable. Community contributors set this to their
# own PtolemyArchitectureInterface subclass instance.
#
# The SMNNIP reference implementation is protected by .gitignore.SSF and will
# be released publicly when Second Age conditions are met.
#
# Example (community use):
#
#   from my_architecture import MyArchitecture
#   from Philadelphos.phila import NEURAL_ARCHITECTURE
#   NEURAL_ARCHITECTURE = MyArchitecture()
#   NEURAL_ARCHITECTURE.load("path/to/checkpoint.pt")
#
# Example (SMNNIP reference — internal):
#
#   from Philadelphos.ptolemy_core import JuliusCaesarFace
#   NEURAL_ARCHITECTURE = JuliusCaesarFace()
#   NEURAL_ARCHITECTURE.load()

NEURAL_ARCHITECTURE: Optional[PtolemyArchitectureInterface] = None


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE — safe call helpers
# ─────────────────────────────────────────────────────────────────────────────

def _require_architecture(op: str) -> PtolemyArchitectureInterface:
    if NEURAL_ARCHITECTURE is None:
        raise RuntimeError(
            f"Philadelphos.NEURAL_ARCHITECTURE is None — cannot {op}.\n"
            f"Set NEURAL_ARCHITECTURE to a PtolemyArchitectureInterface instance first."
        )
    if not NEURAL_ARCHITECTURE.is_loaded:
        raise RuntimeError(
            f"NEURAL_ARCHITECTURE '{NEURAL_ARCHITECTURE.name}' is not loaded.\n"
            f"Call NEURAL_ARCHITECTURE.load() first."
        )
    return NEURAL_ARCHITECTURE


def respond(prompt: str, language: str = "en", max_tokens: int = 512) -> str:
    """Module-level convenience. Routes to active NEURAL_ARCHITECTURE.respond()."""
    arch = _require_architecture("respond")
    return arch.respond(prompt, language=language, max_tokens=max_tokens)


def lookup(word: str, language: str = "en") -> Optional[Dict]:
    """Module-level convenience. Routes to active NEURAL_ARCHITECTURE.lookup()."""
    arch = _require_architecture("lookup")
    return arch.lookup(word, language=language)


# ─────────────────────────────────────────────────────────────────────────────
# PHILA — kernel-visible stub (v0.9)
# Ptolemy3.py does: from Philadelphos.Phila import Phila; self.Philadelphos = Phila(self)
# In v0.9 Philadelphos is a thin log-bridge.  Full SMIP integration in Plan 2.
# ─────────────────────────────────────────────────────────────────────────────

class Phila:
    """
    Ptolemy kernel's handle to the Philadelphos layer.
    v0.9: bridges setOutput → msg_bus.post(CH_LOG).
    """

    def __init__(self, ptolemy):
        self.Ptolemy = ptolemy

    def setOutput(self, text, color=None, speak=False):
        """Route legacy setOutput calls to the message bus log channel."""
        try:
            from Pharos.PtolBus import BusMessage, Priority, CH_LOG
            meta = {'color': color} if color else {}
            self.Ptolemy.msg_bus.publish(
                BusMessage(CH_LOG, str(text), Priority.T2,
                           sender='Philadelphos', meta=meta))
        except Exception:
            print(f'[Phila] {text}')


def architecture_info() -> Dict[str, Any]:
    """Return info dict about the active architecture, or status message if None."""
    if NEURAL_ARCHITECTURE is None:
        return {"status": "no architecture loaded", "NEURAL_ARCHITECTURE": None}
    return NEURAL_ARCHITECTURE.info()


# ─────────────────────────────────────────────────────────────────────────────
# FACES REGISTRY — known named faces (populated at import by face modules)
# ─────────────────────────────────────────────────────────────────────────────

_FACE_REGISTRY: Dict[str, PtolemyArchitectureInterface] = {}


def register_face(face: PtolemyArchitectureInterface) -> None:
    """Called by face modules at import to self-register."""
    _FACE_REGISTRY[face.name] = face


def get_face(name: str) -> Optional[PtolemyArchitectureInterface]:
    return _FACE_REGISTRY.get(name)


def list_faces() -> List[str]:
    return list(_FACE_REGISTRY.keys())


def activate_face(name: str) -> None:
    """Set NEURAL_ARCHITECTURE to a registered face by name."""
    global NEURAL_ARCHITECTURE
    face = _FACE_REGISTRY.get(name)
    if face is None:
        raise KeyError(f"No face registered under name '{name}'. "
                       f"Known faces: {list_faces()}")
    NEURAL_ARCHITECTURE = face


if __name__ == "__main__":
    print("Philadelphos neural architecture slot — status:")
    print(architecture_info())
    print(f"Registered faces: {list_faces()}")


# ─────────────────────────────────────────────────────────────────────────────
# PHILA — Qt face widget
# Ptolemy3.py imports: from Philadelphos.Phila import Phila
# ─────────────────────────────────────────────────────────────────────────────

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                                  QTextEdit, QSizePolicy)
    from PyQt6.QtCore    import Qt
    from PyQt6.QtGui     import QFont, QColor

    class Phila(QWidget):
        """
        Philadelphos face widget — AI/command layer for the Ptolemy desktop.

        Embeds PtolemyEars (input) and a response display area.
        Wires ptolemy_tongue as the last output filter.

        Layout:
            ┌─────────────────────────────────────┐
            │  response_display (QTextEdit, r/o)  │
            ├─────────────────────────────────────┤
            │  PtolemyEars  [input ──────────] [→]│
            └─────────────────────────────────────┘
        """

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumSize(480, 200)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._build_ui()

        def _build_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(4)

            # Response display
            self.response_display = QTextEdit(self)
            self.response_display.setReadOnly(True)
            self.response_display.setFont(QFont('Ubuntu Mono', 10))
            self.response_display.setStyleSheet(
                'background:#050d0d; color:#00dddd; border:1px solid #005555;')
            layout.addWidget(self.response_display, stretch=1)

            # Ears (input + gate indicator)
            try:
                from Philadelphos.ptolemy_ears import PtolemyEars
                self.ears = PtolemyEars(self)
                self.ears.set_response_handler(self._on_response)
                layout.addWidget(self.ears)
            except Exception as e:
                fallback = QLabel(f"[ears unavailable: {e}]", self)
                fallback.setFont(QFont('Ubuntu Mono', 9))
                layout.addWidget(fallback)
                self.ears = None

        def _on_response(self, text: str):
            """Append response to display widget."""
            self.response_display.append(text)
            # Scroll to bottom
            sb = self.response_display.verticalScrollBar()
            sb.setValue(sb.maximum())

        def setOutput(self, text: str, speak: bool = False):
            """
            Ptolemy3.py calls this on scene item click.
            Displays item information in the response pane.
            """
            self.response_display.append(f"[item] {text}")

except ImportError:
    # Headless / non-Qt environment — stub
    class Phila:  # type: ignore[no-redef]
        def __init__(self, parent=None):
            pass
        def setOutput(self, text, speak=False):
            pass
