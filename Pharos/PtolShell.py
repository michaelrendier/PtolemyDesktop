#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
PtolShell — QTermWidget container for the Ptolemy shell pty.

Embeds a QTermWidget that runs :mod:`Pharos.ptolemy_shell` inside a
pseudo-terminal.  All prompt logic, input routing, and Monad dispatch live
in ``ptolemy_shell.py``; this module is purely the Qt wrapper.

Launch mechanism
----------------
``QTermWidget.setArgs`` has unreliable Python binding behaviour across
versions.  Instead a temporary executable shell script is written::

    #!/bin/sh
    exec python3 /path/to/ptolemy_shell.py

``setShellProgram(wrapper)`` is called with no args, which is universally
reliable.  The wrapper is deleted on :meth:`PtolShell.closeEvent`.
"""
__author__ = 'rendier@thewanderinggod.tech'

import sys
import os
import stat
import shlex
import tempfile

from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

try:
    import QTermWidget
    _HAS_QTERM = True
except ImportError:
    _HAS_QTERM = False

_SHELL_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'ptolemy_shell.py'
)


class PtolShell(QWidget):
    """Qt widget that hosts the Ptolemy shell inside a QTermWidget pty.

    If ``QTermWidget`` is not installed a plain error label is shown instead.
    The shell process is ``ptolemy_shell.py``, launched via a temp wrapper
    script so the pty starts cleanly on all QTermWidget Python binding versions.
    """

    def __init__(self, parent=None):
        """Initialise the widget and start the shell pty.

        :param parent: Optional Qt parent widget.
        :type parent: QWidget or None
        """
        super().__init__(parent)
        self.setMinimumSize(660, 415)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet('background: #050510;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._wrapper = None

        if _HAS_QTERM:
            self._term = QTermWidget.QTermWidget()
            self._term.setColorScheme('Linux')
            self._term.setTerminalFont(QFont('Monospace', 10))

            _scroll = getattr(QTermWidget.QTermWidget, 'ScrollBarRight', None)
            if _scroll is None:
                _pos = getattr(QTermWidget.QTermWidget, 'ScrollBarPosition', None)
                if _pos is not None:
                    _scroll = getattr(_pos, 'ScrollBarRight', None)
            if _scroll is not None:
                self._term.setScrollBarPosition(_scroll)

            self._term.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Write a tiny wrapper script so QTermWidget execs python3 directly.
            # Using setShellProgram(executable) + no args is more reliable than
            # setArgs across different QTermWidget Python binding versions.
            tf = tempfile.NamedTemporaryFile(
                mode='w', suffix='.sh', delete=False, prefix='ptol_shell_')
            tf.write(f'#!/bin/sh\nexec {sys.executable} {shlex.quote(_SHELL_SCRIPT)}\n')
            tf.close()
            os.chmod(tf.name, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            self._wrapper = tf.name

            self._term.setShellProgram(self._wrapper)
            self._term.startShellProgram()
            layout.addWidget(self._term)
        else:
            lbl = QLabel(
                'QTermWidget not installed.\n'
                'pip install qtermwidget  or  build from source.')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet('color: #ff8800; background: #050510;')
            layout.addWidget(lbl)
            self._term = None

    def showEvent(self, event):
        """Give keyboard focus to the terminal on show."""
        super().showEvent(event)
        if self._term is not None:
            self._term.setFocus()

    def mousePressEvent(self, event):
        """Return keyboard focus to the terminal after a click."""
        super().mousePressEvent(event)
        if self._term is not None:
            self._term.setFocus()

    def closeEvent(self, event):
        """Remove the temporary wrapper script before closing.

        :param event: Qt close event.
        """
        if self._wrapper and os.path.exists(self._wrapper):
            try:
                os.unlink(self._wrapper)
            except Exception:
                pass
        super().closeEvent(event)
