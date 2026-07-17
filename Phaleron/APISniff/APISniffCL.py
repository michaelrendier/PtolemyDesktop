#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
APISniff.py  –  Python Code / Package Browser
A file-manager-style GUI for exploring installed Python packages and the
current program scope, using dir() and inspect rather than external docs.

Requires: PyQt5, prettytable.py (local copy), Syntax.py, Dialogs.py
"""

__author__ = 'rendier'

import sys
import os
import inspect
import types
import importlib

from PyQt5.QtCore    import QEvent, QUrl, Qt
from PyQt5.QtGui     import (QIcon, QFont, QImage, QImageReader,
                              QTextDocument, QTextImageFormat,
                              QTextCursor, QCursor, QColor)
from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QListWidget,
                              QCheckBox, QWidget, QTextEdit, QAction,
                              qApp, QGridLayout, QInputDialog,
                              QListWidgetItem, QApplication)

from Syntax  import PythonHighlighter
from Dialogs import Dialogs
import prettytable

# ---------------------------------------------------------------------------
# Capture root scope BEFORE anything else is defined
# ---------------------------------------------------------------------------
crumbsRoot = dir()

# ---------------------------------------------------------------------------
# Colour legend  { role : (text_colour, bg_colour) }
# ---------------------------------------------------------------------------
TYPE_COLOURS = {
    'dunder'  : ('black', 'light blue'),
    'wrapper' : ('black', 'light green'),
    'class'   : ('white', 'dark red'),
    'module'  : ('white', 'dark blue'),
    'function': ('white', 'dark green'),
    'builtin' : ('white', 'black'),
    'method'  : ('white', 'purple'),
    'data'    : ('black', 'yellow'),
    'unknown' : ('black', 'white'),
}

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _getattr_path(root, parts):
    """Walk root.a.b.c given ['a', 'b', 'c'].  Raises AttributeError on miss."""
    obj = root
    for p in parts:
        obj = getattr(obj, p)
    return obj


def _safe_source(obj):
    """Return inspect source lines, or a friendly placeholder on failure."""
    try:
        return "".join(inspect.getsourcelines(obj)[0]).replace("\t", "    ")
    except (OSError, TypeError):
        return "# Source code is not available for this object.\n"


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class CodeBrowser(QMainWindow):
    """File-manager-style browser for installed Python packages
    and the current program scope."""

    def __init__(self, crumbs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Package Browser")
        self.Parent = parent

        self.dialogs = Dialogs(parent=self)

        # Paths – degrade gracefully outside the Ptolemy directory tree
        self.homeDir = os.path.expanduser("~") + "/Ptolemy/"
        self.imgDir  = self.homeDir + "images/Phaleron/old/"

        self.styles = (
            "QWidget        { border: 1px solid white;"
            "                 background-color: black; color: white } "
            "QMenuBar::item { background-color: black; color: white } "
            "QStatusBar     { background-color: black; color: white } "
            "QCheckBox      { border: 1px solid black; color: white }"
        )

        # Navigation state
        self.package     = "Current"
        self.crumbs      = ['Explorer', 'Current']
        self.icrumbs     = ''
        self.exploration = None          # the live imported module object

        self.geo      = QDesktopWidget().frameGeometry()
        self.current  = crumbs           # snapshot of the calling scope dir()
        self.reimport = 0
        self.debugger = 0                # off by default
        self.sitems   = []

        # Formatting state (properly initialised in itemSelect)
        self.centering = 80
        self.cent      = "{:^72s}"
        self.spacer    = "{:_^72s}"

        self.initUI()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def initUI(self):
        icon_path = os.path.join(self.imgDir, 'neorendier_small.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.widget = QWidget(self)
        self.widget.setStyleSheet(self.styles)

        # ---- Child widgets ----
        self.list     = QListWidget(self.widget)
        self.tlist    = QListWidget(self.widget)
        self.text     = QTextEdit(self.widget)
        self.bugcheck = QCheckBox(self.widget)

        # ---- Actions (helper to avoid repetition) ----
        def _mkaction(icon_name, label, shortcut, tip, slot):
            p = os.path.join(self.imgDir, icon_name)
            a = QAction(QIcon(p) if os.path.exists(p) else QIcon(), label, self)
            a.setShortcut(shortcut)
            a.setStatusTip(tip)
            a.triggered.connect(slot)
            return a

        exitAction   = _mkaction('exit.png',            'E&xit',
                                 'Ctrl+X', 'Exit Application',      qApp.quit)
        openAction   = _mkaction('folder_red_open.png', '&Open',
                                 'Ctrl+O', 'Open New Package',      self.importPkg)
        searchAction = _mkaction('search-icon.png',     'Search Contains:',
                                 'Ctrl+S', 'Search items in list',  self.searchList)
        debugAction  = _mkaction('debug.png',           'Debugging',
                                 'Ctrl+D', 'Toggle debug output',   self.bugcheck.toggle)

        # ---- Menu bar ----
        self.topMenu = self.menuBar()
        self.topMenu.setStyleSheet(self.styles)

        fileMenu = self.topMenu.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addSeparator()
        fileMenu.addAction(debugAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        searchMenu = self.topMenu.addMenu('&Search')
        searchMenu.addAction(searchAction)

        # ---- Status bar ----
        self.status = self.statusBar()
        self.status.setStyleSheet(self.styles)

        # ---- Name list (left panel) ----
        self.list.setFont(QFont('Monospace', 9))
        self.list.setFixedWidth(300)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.currentItemChanged.connect(self.itemSelect)
        self.list.itemClicked.connect(self.itemSelect)
        self.list.itemDoubleClicked.connect(self.repopList)
        self.list.verticalScrollBar().valueChanged.connect(
            self.tlist.verticalScrollBar().setValue)

        # ---- Type list (middle panel) ----
        self.tlist.setFont(QFont('Monospace', 9))
        self.tlist.setMaximumWidth(300)
        self.tlist.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tlist.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tlist.verticalScrollBar().valueChanged.connect(
            self.list.verticalScrollBar().setValue)

        # ---- Code / text panel (right) ----
        self.text.setFont(QFont('Monospace', 9))
        self.text.setReadOnly(True)
        self.highlight = PythonHighlighter(self.text.document())

        # ---- Debug checkbox ----
        self.bugcheck.setStyleSheet(
            "QCheckBox { border: 1px solid black; color: white }")
        self.bugcheck.setText("Debugging Off")
        self.bugcheck.stateChanged.connect(self.debug)

        # ---- Grid layout ----
        layout = QGridLayout(self.widget)
        layout.addWidget(self.list,     0,  0, 10, 2)
        layout.addWidget(self.tlist,    0,  2, 10, 1)
        layout.addWidget(self.text,     0,  3, 10, 6)
        layout.addWidget(self.bugcheck, 11, 0,  1, 1)

        self.setCentralWidget(self.widget)
        self.addItems()

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def debug(self, state):
        if state == Qt.Checked:
            self.debugger = 1
            self.bugcheck.setText("DEBUGGING ON")
        else:
            self.debugger = 0
            self.bugcheck.setText("Debugging Off")

    def dPrint(self, label, data=None):
        if self.debugger:
            print(label if data is None else f"{label} = {data}")

    # ------------------------------------------------------------------
    # Object resolution  (replaces all the old exec() string-building)
    # ------------------------------------------------------------------

    def _root_is_current(self):
        return len(self.crumbs) > 1 and self.crumbs[1] == 'Current'

    def _resolve_path(self, extra_parts=None):
        """Return the object at crumbs[2:] + extra_parts.

        For 'Current' scope we must eval() the dotted name because the
        objects live in the outer caller scope, not inside self.
        For package scope we use safe getattr chains.
        """
        parts = self.crumbs[2:] + (extra_parts or [])

        if self._root_is_current():
            expr = '.'.join(parts) if parts else ''
            if not expr:
                return None
            try:
                return eval(expr)
            except Exception:
                return None
        else:
            if self.exploration is None:
                return None
            try:
                return _getattr_path(self.exploration, parts)
            except AttributeError:
                return None

    def _resolve_leaf(self):
        """Return the object for self.pkg at the current crumb depth."""
        return self._resolve_path([self.pkg])

    # ------------------------------------------------------------------
    # Import a package
    # ------------------------------------------------------------------

    def importPkg(self):
        self.dPrint("\nIMPORTING PACKAGE")

        prompt = ("Package Does Not Exist\n\nPlease Select a Different Package"
                  if self.reimport else
                  "Please Enter a Package Name\n(blank or __main__ = Current Scope)")
        text, ok = QInputDialog.getText(self, 'Package Chooser', prompt)
        self.reimport = 0

        if not ok:
            return

        text = text.strip()
        if not text or text == '__main__':
            self.setWindowTitle("Browsing Current Scope")
            self.package     = "Current"
            self.exploration = None
            self.addItems()
            return

        self.setWindowTitle(f"Browsing Python '{text}' Module")
        self.package = text

        try:
            self.exploration = importlib.import_module(text)
            self.addItems()
        except ImportError:
            self.dPrint(f"Module '{text}' not found")
            self.reimport = 1
            self.importPkg()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def searchList(self):
        if self.sitems:
            self.sitems = []
            self.repopList('reload')

        term, ok = QInputDialog.getText(self, "List Search",
                                        "Enter Search Term for Current List")
        if not ok or not term:
            return

        self.sitems = self.list.findItems(term, Qt.MatchContains)
        for item in self.sitems:
            item.setForeground(QColor('red'))

        names = [i.text() for i in self.sitems]
        if names:
            table = self._make_table(names)
            self.setText(str(table), 'search-icon.png', 'Search Results')

    # ------------------------------------------------------------------
    # List population
    # ------------------------------------------------------------------

    def addItems(self):
        self.status.setStatusTip('.'.join(self.crumbs))
        self.list.clear()
        self.tlist.clear()
        self.text.clear()

        if self.package == "Current":
            self.dPrint('\nADDING DIR()')
            self.crumbs  = ['Explorer', 'Current']
            self.icrumbs = ''

            for name in self.current:
                try:
                    obj        = eval(name)
                    entry_type = type(obj)
                except Exception:
                    entry_type = type(None)
                self.typeSort(name, entry_type)

        else:
            self.dPrint("\nADDING PACKAGE")
            self.crumbs  = ['Explorer', self.package]
            self.icrumbs = ''

            for name in dir(self.exploration):
                try:
                    obj        = getattr(self.exploration, name)
                    entry_type = type(obj)
                except Exception:
                    entry_type = type(None)
                self.typeSort(name, entry_type)

    def repopList(self, item):
        self.dPrint("\nREPOPULATING LIST")
        try:
            entry = str(item.text())
        except AttributeError:
            entry = str(item)

        self.dPrint("entry", entry)
        self.list.clear()
        self.tlist.clear()

        if entry == "..":
            # ---- navigate up ----
            if len(self.crumbs) > 2:
                self.crumbs.pop()
            if len(self.crumbs) > 2:
                self.listsEntry('..', 'white', 'black', 'Previous')
            self.setStatusTip('.'.join(self.crumbs))
            parent_obj = self._resolve_path()
            direc = dir(parent_obj) if parent_obj is not None else []

        elif entry == 'reload':
            if len(self.crumbs) > 2:
                self.listsEntry('..', 'white', 'black', 'Previous')
            return

        else:
            # ---- navigate down ----
            self.crumbs.append(entry)
            self.setStatusTip('.'.join(self.crumbs))
            child_obj = self._resolve_path()
            direc = dir(child_obj) if child_obj is not None else []
            self.listsEntry('..', 'white', 'black', 'Previous')

        self.icrumbs = '.'.join(self.crumbs[2:])

        for name in direc:
            child      = self._resolve_path([name])
            entry_type = type(child) if child is not None else type(None)
            self.typeSort(name, entry_type)

    # ------------------------------------------------------------------
    # List-item insertion
    # ------------------------------------------------------------------

    def listsEntry(self, text, tcolor, bcolor, entry_type):
        self.dPrint("\nENTERING LIST ITEM")

        item_in = QListWidgetItem(text)
        item_in.setForeground(QColor(tcolor))
        item_in.setBackground(QColor(bcolor))

        # Human-readable type label
        label = (str(entry_type)
                 .replace("<class '", "").replace("'>", "")
                 .replace("builtin_function_or_method", "Builtin Function")
                 .replace("NoneType", "None")
                 .capitalize())

        type_in = QListWidgetItem(label)
        type_in.setForeground(QColor(tcolor))
        type_in.setBackground(QColor(bcolor))
        type_in.setToolTip(str(getattr(entry_type, '__doc__', '') or ''))

        self.list.addItem(item_in)
        self.tlist.addItem(type_in)

    # ------------------------------------------------------------------
    # Colour-coded type sorting
    # ------------------------------------------------------------------

    def typeSort(self, name, entry_type):
        self.dPrint("SORTING", f"{name} -> {entry_type}")

        if name.startswith("__") and name.endswith("__"):
            col = TYPE_COLOURS['dunder']

        elif 'pyqtWrapperType' in str(entry_type):
            col = TYPE_COLOURS['wrapper']

        elif entry_type is types.ModuleType:
            col = TYPE_COLOURS['module']

        elif inspect.isclass(entry_type) and issubclass(entry_type, type):
            col = TYPE_COLOURS['class']

        elif entry_type is types.FunctionType:
            col = TYPE_COLOURS['function']

        elif entry_type in (types.BuiltinFunctionType, types.BuiltinMethodType):
            col = TYPE_COLOURS['builtin']

        elif entry_type is types.MethodType:
            col = TYPE_COLOURS['method']

        elif entry_type in (dict, str, list, tuple, int, float,
                            bool, bytes, set, frozenset, complex):
            col = TYPE_COLOURS['data']

        else:
            col = TYPE_COLOURS['unknown']

        self.listsEntry(name, col[0], col[1], entry_type)

    # ------------------------------------------------------------------
    # Item selection
    # ------------------------------------------------------------------

    def itemSelect(self, item):
        self.dPrint("\nITEM SELECT", item)
        if item is None:
            return

        # Recalculate formatting widths from current widget size
        width_chars    = max(self.text.width() // 7, 40)
        self.centering = width_chars
        fmt_w          = width_chars - 8
        self.cent      = f"{{:^{fmt_w}s}}"
        self.spacer    = f"{{:_^{fmt_w}s}}"

        self.codeS = self.spacer.format("Code")            + "\n\n"
        self.contS = self.spacer.format("Contents")        + "\n\n"
        self.conS  = self.spacer.format("Contents")        + "\n\n"
        self.docS  = self.spacer.format("Document String") + "\n\n"
        self.valS  = self.spacer.format("Value")           + "\n\n"

        try:
            self.pkg     = item.text()
            self.icrumbs = '.'.join(self.crumbs[2:])
            self.dPrint("pkg",    self.pkg)
            self.dPrint("crumbs", self.crumbs)

            leaf          = self._resolve_leaf()
            self.itemType = type(leaf) if leaf is not None else type(None)
            raw_doc       = getattr(leaf, '__doc__', None)
            doc_body      = raw_doc if raw_doc else "No Documentation For Selected Item"
            self.docstr   = f"{self.docS}{doc_body}\n\n"

            self.dPrint("itemType", str(self.itemType))
            self.getText()

        except AttributeError:
            pass

    # ------------------------------------------------------------------
    # Detail routing
    # ------------------------------------------------------------------

    def getText(self):
        self.dPrint("\nGETTING TEXT")
        self.highlight.setDocument(None)

        leaf = self._resolve_leaf()

        if self.pkg == "..":
            self.typePrevious()

        elif self.pkg.startswith("__") and self.pkg.endswith("__"):
            self.typePrivate()

        elif self.itemType is types.ModuleType:
            self.typeModule()

        elif inspect.isclass(leaf):
            self.typeClass()

        elif self.itemType is types.FunctionType:
            self.typeFunction()

        elif self.itemType in (types.BuiltinFunctionType, types.BuiltinMethodType):
            self.typeBuiltin()

        elif self.itemType is types.MethodType:
            self.typeInstanceMethod()

        elif self.itemType in (dict, str, list, tuple, int, float,
                               bool, bytes, set, frozenset, complex,
                               type(None)):
            self.typeCollection()

        elif 'pyqtWrapperType' in str(self.itemType):
            self.typePyqtWrapper()

        else:
            self.dPrint("\n<???UNKNOWN???>")
            self.setText(f"{self.itemType}\n{self.docstr}",
                         'unknown.png', 'UNKNOWN')

    # ------------------------------------------------------------------
    # Type-specific detail renderers
    # ------------------------------------------------------------------

    def typeModule(self):
        self.dPrint("\n<MODULE>")
        obj     = self._resolve_leaf()
        mod_dir = dir(obj) if obj is not None else []
        source  = _safe_source(obj)
        table   = self._make_table(mod_dir)
        self.highlight.setDocument(self.text.document())
        entry = f"{self.docstr}{self.conS}{table}\n\n{self.codeS}{source}"
        self.setText(entry, 'blueberry_folder.png', 'Module Directory')

    def typeClass(self):
        self.dPrint("\n<CLASS>")
        obj       = self._resolve_leaf()
        class_dir = dir(obj) if obj is not None else []
        source    = _safe_source(obj)
        table     = self._make_table(class_dir)
        self.highlight.setDocument(self.text.document())
        entry = f"{self.docstr}{self.conS}{table}\n\n{self.codeS}{source}"
        self.setText(entry, 'ruby_folder.png', 'Class Object')

    def typePyqtWrapper(self):
        self.dPrint("\n<PYQT WRAPPER>")
        obj    = self._resolve_leaf()
        source = _safe_source(obj)
        self.highlight.setDocument(self.text.document())
        entry = (f"{self.cent.format(self.pkg)}\n"
                 f"{self.cent.format(str(self.itemType))}\n\n"
                 f"{self.docstr}{self.codeS}{source}")
        self.setText(entry, 'ruby_folder.png', 'PyQt Class Object')

    def typeFunction(self):
        self.dPrint("\n<FUNCTION>")
        obj    = self._resolve_leaf()
        source = _safe_source(obj)
        self.highlight.setDocument(self.text.document())
        entry  = f"#!/usr/bin/python3\n# -*- coding: utf-8 -*-\n\n{source}"
        self.setText(entry, 'python-bytecode.png', 'Function Code')

    def typeBuiltin(self):
        self.dPrint("\n<BUILTIN>")
        notice = self.cent.format("SOURCE NOT AVAILABLE FOR BUILTIN FUNCTIONS")
        entry  = f"\n\n{notice}\n\n\n{self.docstr}"
        self.setText(entry, 'python-builtins.png', 'Builtin Function')

    def typeInstanceMethod(self):
        self.dPrint("\n<INSTANCE METHOD>")
        obj = self._resolve_leaf()

        # Python 3: __self__.__class__ replaces the Py2 im_class attribute
        try:
            method_of = obj.__self__.__class__
        except AttributeError:
            method_of = getattr(obj, '__objclass__', type(None))

        source       = _safe_source(obj)
        method_title = self.cent.format(f"Instance Method of {method_of}") + "\n\n"
        self.highlight.setDocument(self.text.document())
        entry = f"{method_title}{self.docstr}{self.codeS}{source}"
        self.setText(entry, 'parentheses.png', 'Instance Method')

    def typeCollection(self):
        self.dPrint("\n<COLLECTION / DATA>")
        obj   = self._resolve_leaf()
        entry = f"{self.docstr}{self.valS}{obj!r}"
        self.highlight.setDocument(self.text.document())
        self.setText(entry, 'stickynotes.png', 'Collection / Data Object')

    def typePrivate(self):
        self.dPrint("\n<PRIVATE / DUNDER>")
        obj = self._resolve_leaf()
        val = repr(obj)
        display_val = "" if val in self.docstr else val
        entry = f"{self.docstr}{self.valS}{display_val}"
        self.setText(entry, 'private-folder.png', 'Private / Dunder Data')

    def typePrevious(self):
        self.dPrint("\n<PREVIOUS>")
        parent  = self._resolve_path()
        listing = str(dir(parent)) if parent is not None else "(top of scope)"
        entry   = f"Parent path: {'.'.join(self.crumbs)}\n\nContents:\n{listing}"
        self.setText(entry, 'previous.png', 'Previous Directory')

    def typeUnknown(self):
        self.dPrint("\n<UNKNOWN TYPE>")
        self.setText(self.docstr, 'unknown.png', 'Unknown Type')

    def typeType(self):
        self.dPrint("\n<TYPE>")
        entry = f"{self.docstr}\n\n{self.cent.format('TYPE OBJECT')}\n\n"
        self.setText(entry, 'python-type.png', 'Type Object')

    # ------------------------------------------------------------------
    # Text / image display
    # ------------------------------------------------------------------

    def setText(self, entry, head_img, title):
        self.dPrint("\nSETTING TEXT")
        self.text.clear()
        self.insertImage(head_img, title)
        self.text.append(entry)
        self.text.verticalScrollBar().setValue(0)

    def insertImage(self, file_path, title):
        """Insert a gradient header bar + a type icon into the text pane."""
        self.dPrint("\nINSERTING IMAGE")

        img_full = os.path.join(self.imgDir, file_path)
        hdr_full = os.path.join(self.imgDir, 'rectgradient.jpg')

        image  = QImage(QImageReader(img_full).read()) if os.path.exists(img_full) else QImage()
        header = QImage(QImageReader(hdr_full).read()) if os.path.exists(hdr_full) else QImage()

        img_uri = QUrl(img_full)
        hdr_uri = QUrl(hdr_full)

        self.text.document().addResource(QTextDocument.ImageResource, hdr_uri, header)
        self.text.document().addResource(QTextDocument.ImageResource, img_uri, image)

        hdr_fmt = QTextImageFormat()
        hdr_fmt.setWidth(240); hdr_fmt.setHeight(88)
        hdr_fmt.setName(hdr_uri.toString())

        img_fmt = QTextImageFormat()
        img_fmt.setWidth(88);  img_fmt.setHeight(88)
        img_fmt.setName(img_uri.toString())

        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.insertImage(hdr_fmt)
        cursor.insertImage(img_fmt)

        label_w = max(self.centering - 8, 10)
        self.text.append(f"{{:_^{label_w}s}}".format(title) + "\n\n")
        self.text.setCursor(QCursor(Qt.BlankCursor))

    # ------------------------------------------------------------------
    # PrettyTable helper
    # ------------------------------------------------------------------

    def _make_table(self, name_list):
        """Return a PrettyTable laid out to fill the text pane width.

        Each cell holds one name; the number of columns is calculated so
        the widest name fits comfortably across the available character width.
        """
        if not name_list:
            return "(empty)"

        text_w   = max(self.text.frameGeometry().width() // 7, 20)
        longest  = max(len(n) for n in name_list)
        col_w    = longest + 2                      # +2 for padding
        num_cols = max(1, text_w // col_w)

        # Pad to an even multiple of num_cols
        padded    = list(name_list)
        remainder = len(padded) % num_cols
        if remainder:
            padded += [''] * (num_cols - remainder)

        headers = [str(i) for i in range(num_cols)]
        table   = prettytable.PrettyTable(headers)
        table.header        = False
        table.padding_width = 1
        table.align         = 'l'
        table.border        = True

        rows = [padded[i:i + num_cols] for i in range(0, len(padded), num_cols)]
        for row in rows:
            table.add_row(row)

        return table

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def split(self, arr, size):
        """Chunk a list into sublists of *size*."""
        return [arr[i:i + size] for i in range(0, len(arr), size)]

    def setCurrent(self, cursco):
        self.current = cursco

    def eventFilter(self, obj, event):
        if hasattr(self, 'prev') and obj == self.prev:
            self.prev.setDisabled(len(self.crumbs[2:]) == 0)
        if event.type() == QEvent.Enter:
            obj.setStyleSheet(
                "QPushButton { border: 1px solid white;"
                "              background-color: blue; color: white }")
        if event.type() == QEvent.Leave:
            obj.setStyleSheet(
                "QPushButton { border: 1px solid white;"
                "              background-color: black; color: white }")
        return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Package Browser')

    explorer = CodeBrowser(crumbsRoot)
    explorer.setWindowTitle("Package Browser")
    explorer.setStyleSheet("QMainWindow { background-color: black; color: white }")
    explorer.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
