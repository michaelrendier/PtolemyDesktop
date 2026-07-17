#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import QUrl, QEvent, Qt
from PyQt6.QtGui import QAction, QIcon, QFont, QImage, QImageReader, QTextDocument, QTextImageFormat, QCursor, QTextCursor, QColor
from PyQt6.QtWidgets import QApplication, QListWidgetItem, QInputDialog, QGridLayout, QWidget, QListWidget, QTextEdit, QCheckBox, QMainWindow, QMessageBox

from Phaleron.Syntax import PythonHighlighter
from Pharos.Dialogs import Dialogs

import sys, os, time, inspect, psutil, types, urllib, prettytable


# current = dir()

# Fix these TODO
# object, instance, enumeration

class StdErrHandler():
	"""
	http://stackoverflow.com/questions/28505462/display-stderr-in-a-pyqt-qmessagebox
	http://stackoverflow.com/users/3453633/carpecimex
	"""
	def __init__(self):
		# pass
		# To instantiate only one message box
		self.err_box = None

	def write(self, std_msg):
		# All that stderr or stdout require is a class with a 'write' method.
		if self.err_box is None:
			self.err_box = QMessageBox()
			# Both OK and window delete fire the 'finished' signal
			self.err_box.finished.connect(self.clear)
		# A single error is sent as a string of separate stderr .write() messages,
		# so concatenate them.
		self.err_box.setText(self.err_box.text() + std_msg)
		# .show() is used here because .exec() or .exec_() create multiple
		# MessageBoxes.
		self.err_box.show()

	def clear(self):
		# QMessageBox doesn't seem to be actually destroyed when closed, just hidden.
		# This is true even if destroy() is called or if the Qt.WA_DeleteOnClose
		# attribute is set.  Clear text for next time.
		self.err_box.setText('')

thatone = StdErrHandler()
# print("TYPE", type(thatone.write))

current = dir()

class CodeBrowser(QMainWindow):
	"""File manager like browser for installed python packages as well as current program scope.
	"""

	def __init__(self, current, parent=None):
		super(CodeBrowser, self).__init__(parent)
		QMainWindow.__init__(self)
		self.setWindowTitle("Package Browser")

		self.debugger = 1
		self.dPrint("INIT")

		self.parent = parent
		# self.dPrint(str(self.parent))

		if self.parent:
			self.dialogs = self.parent.dialogs
			self.homeDir = self.parent.homeDir
			self.styles = self.parent.styles


		else:
			self.dialogs = Dialogs(parent=self)
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			self.homeDir = PTOL_ROOT + "/"
			self.styles = "QWidget { border: 1px solid white; background-color: black; color: white } " \
						  "QMenuBar::item { background-color: black; color: white } " \
						  "QStatusBar { background-color: black; color: white } " \
						  "QCheckBox {border: 1px solid black; color: white }"

		self.imgDir = self.homeDir + "images/Phaleron/old/"

		# AttributeError: type object 'WebkitRenderer' has no attribute 'im_class' line 804 repoplist TODO
		self.package = "Current"
		self.crumbs = ['Explorer', 'Current']
		self.exploration = ""
		self.geo = QApplication.primaryScreen().availableGeometry()

		self.current = current
		# if curScope:
		# 	self.current = curScope
		# else:
		# 	self.current = current
		# self.dPrint "self.current =", self.
		self.reimport = 0
		# self.debugger = 1
		self.sitems = []
		self.typelist = ['ellipsis', 'long', 'NoneType', 'bool', 'NotImplementedType', 'complex', 'getset_descriptor', 'classobj', 'unicode', 'code', 'object', 'file', 'member_descriptor', 'generator', 'str', 'traceback', 'slice', 'list', 'set', 'instance', 'buffer', 'frame', 'type', 'dictproxy', 'float', 'function', 'tuple', 'instancemethod', 'class', 'xrange', 'module', 'int', 'dict', 'builtin_function_or_method']
		self.varlist = ['bool', 'complex', 'dict', 'dictproxy', 'float', 'generator', 'int', 'list', 'long', 'slice', 'str', 'set', 'tuple', 'namedtuple']
		self.dirlist = ['class', 'module', 'builtin_method_or_function', 'function', 'method']


		self.initUI()

	# TODO
	def __del__(self):
		pass

	def initUI(self):
		self.dPrint('initUI')
		self.setWindowIcon(QIcon(self.imgDir + 'neorendier_small.png'))

		# Main Widget
		self.widget = QWidget(self)
		self.widget.setStyleSheet(self.styles)


		# Widget Instances
		self.list = QListWidget(self.widget)
		self.tlist = QListWidget(self.widget)
		self.text = QTextEdit(self.widget)
		self.bugcheck = QCheckBox(self.widget)

		# Actions
		exitAction = QAction(QIcon(self.imgDir + 'exit.png'), 'E&xit', self)
		exitAction.setShortcut('Ctrl+X')
		exitAction.setStatusTip('Exit Application')
		exitAction.triggered.connect(QApplication.instance().quit)

		openAction = QAction(QIcon(self.imgDir + 'folder_red_open.png'), '&Open', self)
		openAction.setShortcut('Ctrl+O')
		openAction.setStatusTip('Open New Package')
		openAction.triggered.connect(self.importPkg)

		searchAction = QAction(QIcon(self.imgDir + 'search-icon.png'), 'Search Contains:', self)
		searchAction.setShortcut('Ctrl+S')
		searchAction.setStatusTip('Search for items that contain the search term')
		searchAction.triggered.connect(self.searchList)

		debugAction = QAction(QIcon(self.imgDir + 'debug.png'), 'Debugging', self)
		debugAction.setShortcut('Ctrl+D')
		debugAction.triggered.connect(self.bugcheck.setChecked)

		# Menu Bar
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

		# Status Bar
		self.status = self.statusBar()
		self.status.setStyleSheet(self.styles)

		# Directory List Setup
		self.list.setFont(QFont('Monospace', 9))
		self.list.setFixedWidth(300)
		self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.list.currentItemChanged.connect(self.itemSelect)
		self.list.itemClicked.connect(self.itemSelect)
		self.list.itemDoubleClicked.connect(self.repopList)
		self.list.verticalScrollBar().valueChanged.connect(self.tlist.verticalScrollBar().setValue)

		# Type List Setup
		self.tlist.setFont(QFont('Monospace', 9))
		self.tlist.setFixedWidth(300)
		self.tlist.setMaximumWidth(300)
		self.tlist.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.tlist.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.tlist.verticalScrollBar().valueChanged.connect(self.list.verticalScrollBar().setValue)
		# self.list.currentItemChanged.connect(self.setText)#FOR WHEN TYPE LIST HAS setText TODO

		# Textbox Setup
		self.text.setFont(QFont('Monospace', 9))
		self.text.setReadOnly(True)
		self.highlight = PythonHighlighter(self.text.document())

		# Debug Setup
		self.bugcheck.setStyleSheet("QCheckBox {border: 1px solid black; color: white }")
		self.bugcheck.setText("Debugging Off")
		self.bugcheck.stateChanged.connect(self.debug)

		# Layout Setup
		self.layout = QGridLayout(self.widget)
		self.layout.addWidget(self.list, 0, 0, 10, 2)
		self.layout.addWidget(self.tlist, 0, 2, 10, 1)
		self.layout.addWidget(self.text, 0, 3, 10, 6)
		self.layout.addWidget(self.bugcheck, 11, 0, 1, 1)

		self.setCentralWidget(self.widget)

		self.addItems()

	def addItems(self):  # MAKE TO USE ONLY REPOP LIST TODO
		self.dPrint("\nADDING ITEMS")

		self.status.setStatusTip(str(".".join(self.crumbs)))
		self.list.clear()
		self.tlist.clear()
		self.text.clear()
		self.crumbs = [['Explorer', 'Current'] if self.package == 'Current' else ['Explorer', self.package]][0]
		self.icrumbs = []
		# if self.package == "Current":
		if 'Current' in self.crumbs:
			self.dirIter = self.current
		else:
			self.dirIter = dir(self.exploration)

		for i in self.dirIter:
			dEntry = i
			code = f"self.entryType = type({dEntry}).__name__"
			code2 = f"self.entryType = type(self.exploration.{dEntry}).__name__"

			exec(code if 'Current' in self.crumbs else code2)

			if self.entryType not in self.varlist or self.entryType not in self.dirlist:
				self.entryType = self.wrapper_type(dEntry, self.entryType)

			self.typeSort(dEntry, self.entryType)

	def eventFilter(self, object, event):
		if object == self.prev and len(self.crumbs[2:]) == 0:
			self.prev.setDisabled(True)
		else:
			self.prev.setDisabled(False)
		if event.type() == QEvent.Enter:
			self.dPrint("Enter Event: Setting Blue")
			object.setStyleSheet("QPushButton { border: 1px solid white; background-color: blue; color: white }")

		if event.type() == QEvent.Leave:
			self.dPrint("Leave Event: Setting Blue")
			object.setStyleSheet("QPushButton { border: 1px solid white; background-color: black; color: white }")

		return False

	def split(self, arr, size):
		arrs = []
		while len(arr) > size:
			pice = arr[:size]
			arrs.append(pice)
			arr = arr[size:]
		arrs.append(arr)
		return arrs

	def insertImage(self, filePath, title):
		self.dPrint("\nINSERTING IMAGE")
		"""http://stackoverflow.com/questions/15539075/inserting-qimage-after-string-in-qtextedit
		user1006989
		"""
		# FIND ICON PACK TO MAKE IMAGES WITH FOR EACH BUILT IN TYPE TODO
		# FIX ENTERING GRAPHIC TITLE TODO

		# imageUri = QUrl(QString("./progImages/{0}".format(filePath)))
		imageUri = QUrl(self.imgDir + filePath)
		image = QImage(QImageReader(filePath).read())
		# headerUri = QtCore.QUrl(QtCore.QString("file://home/rendier/JARVIS/working/rectgradient.jpg"))
		headerUri = QUrl(self.imgDir + 'rectgradient.jpg')
		header = QImage(QImageReader(self.imgDir + 'rectgradient.jpg').read())

		self.text.document().addResource(QTextDocument.ResourceType.ImageResource, headerUri, header)

		imageHeader = QTextImageFormat()
		imageHeader.setWidth(240)
		imageHeader.setHeight(88)
		imageHeader.setName(headerUri.toString())

		self.text.document().addResource(QTextDocument.ResourceType.ImageResource, imageUri, image)

		imageFormat = QTextImageFormat()
		imageFormat.setWidth(88)
		imageFormat.setHeight(88)
		imageFormat.setName(imageUri.toString())

		textCursor = self.text.textCursor()
		textCursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.MoveAnchor)

		textCursor.insertImage(imageHeader)
		textCursor.insertImage(imageFormat)
		headerCentered = ((self.centering - len(title)) / 2) - 4
		self.text.append(self.spacer.format(title) + "\n\n")

		# This will hide the cursor
		blankCursor = QCursor(Qt.CursorShape.BlankCursor)
		self.text.setCursor(blankCursor)

	def importPkg(self):  # FIX INPUT DIALOG COLORS and from and multi import TODO
		self.dPrint("\nIMPORTING PACKAGE")
		# self.dPrint("importPkg", dir())

		if self.reimport == 0:
			text, ok = QInputDialog.getText(self, 'Package Chooser',
											"Please Select Package\n__main__ for Current Program Scope")

		else:
			text, ok = QInputDialog.getText(self, 'Package Chooser',
											"Package Does Not Exist\n\nPlease Select Differenet Package")
			self.reimport = 0

		if ok:
			if text == "":
				self.setWindowTitle("Browsing Current Scope")
			else:
				self.setWindowTitle(f"Browsing Python {text} Module")
			self.package = str(text)
			# self.dPrint("package", self.package)
			if self.package == "":
				self.package = "Current"
				self.exploration = current
				self.addItems()

			elif self.package.count(".") == 1:
				try:
					self.dPrint("SINGLE DOT")
					parts = self.package.split(".")
					self.package = str(parts[1])
					code = f"self.exploration = getattr(__import__('{parts[1]}', globals(), locals(), ['{parts[0]}',]), '{parts[1]}')"
					code2 = f"from {parts[0]} import {parts[1]}"
					self.dPrint("from import", code2)
					eval(str(self.package))
					self.addItems()

				except ImportError:
					self.dPrint(f"Module {'.'.join(parts)} does not exist")
					self.reimport = 1
					self.importPkg()

			elif self.package.count(".") > 1:  # FIX MULTI IMPORT (OR LEARN WHY NOT) TODO

				parts = list(self.package.split("."))
				self.package = str(parts[-1])
				try:
					code = f"self.exploration = getattr(__import__('{'.'.join(parts[:-1])}', globals(), locals(), ['{parts[-1]}',], -1), '{parts[-1]}')"
					# self.dPrint("multi import code", code)
					exec(code)
					self.addItems()

				except ImportError:
					try:
						# self.dPrint(f"Checking if {parts[-1]} is builtin...")
						code = f"self.exploration = __import__('{parts[-1]}')"
						# self.dPrint("import error builtin check code", code)
						exec(code)
						self.addItems()

					except ImportError:
						self.dPrint(f"Module {'.'.join(parts)} does not exist")
						self.reimport = 1
						self.importPkg()


			else:
				try:
					code = f"self.exploration = __import__('{self.package}')"
					# self.dPrint("import code", code)
					exec(code)
					self.addItems()

				except ImportError:
					# self.dPrint(f"Module {self.package} does not exist")
					self.reimport = 1
					self.importPkg()

	def searchList(self):
		if self.sitems:
			self.sitems = []
			self.repopList('reload')

		term, ok = QInputDialog.getText(self, "List Search", "Enter Search Term for Current List")

		if ok:
			self.sitems = self.list.findItems(term, Qt.MatchFlag.MatchContains)
			for i in self.sitems:
				i.setForeground(QColor('red'))

			dlist = self.modDir
			longest = len(max(self.modDir, key=len))
			# self.dPrint("longest item", longest)
			tdir = self.makeTable(dlist, longest)

			entry = [str(i.text()) for i in self.sitems]
			longest = len(max(entry, key=len))
			# self.dPrint("longest item", longest)
			table = self.split(entry, 3)
			result = self.makeTable(table)
			self.setText(str(result), 'search-icon.png', 'Search Results')

	def wrapper_type(self, dEntry, entryType):
		self.dPrint("\nWRAPPER TYPE")
		self.dPrint(f"ENTRY TYPE: {entryType}, dEntry: {dEntry}")

		if eval(f'inspect.isclass({dEntry})' if 'Current' in self.crumbs else f"inspect.isclass(self.exploration.{dEntry})"):
			entryType = 'class'
		elif eval(f'inspect.isbuiltin({dEntry})' if 'Current' in self.crumbs else f"inspect.isbuiltin(self.exploration.{dEntry})"):
			entryType = 'builtin_function_or_method'
		elif eval(f'inspect.isfunction({dEntry})' if 'Current' in self.crumbs else f"inspect.isfunction(self.exploration.{dEntry})"):
			entryType = 'function'
		elif eval(f'inspect.ismethod({dEntry})' if 'Current' in self.crumbs else f"inspect.ismethod(self.exploration.{dEntry})"):
			entryType = 'method'
		elif eval(f'inspect.ismodule({dEntry})' if 'Current' in self.crumbs else f"inspect.ismodule(self.exploration.{dEntry})"):
			entryType = 'module'

		elif "." in entryType:
			self.dPrint("INSTANCE")
			if eval(f"isinstance({dEntry}, type({dEntry}))"):
				entryType = 'instance'

		else:
			try:
				entryType = eval(f"{dEntry}.__module__" if 'Current' in self.crumbs else f"self.exploration.{dEntry}.__module__")# + str(entryType)
			except AttributeError:
				pass


		return entryType

	def typeSort(self, dEntry, entryType):
		# self.dPrint("\nSORTING")
		# self.dPrint(f"{'*' * 50}\nARGS: {dEntry}, {entryType}, {type(entryType)}")

		if 'wrapper' in entryType:  # MAKE SO CAN ALTER FOR SDK WRAPPERS TODO
			self.listsEntry(dEntry, 'black', 'light green', entryType)

		elif entryType not in self.typelist:
			self.listsEntry(dEntry, "black", 'light blue', entryType)

		elif entryType in self.varlist:
			self.listsEntry(dEntry, 'black', 'yellow', entryType)

		elif entryType == 'NoneType':
			self.listsEntry(dEntry, 'black', 'light grey', entryType)

		elif entryType == 'type':
			self.listsEntry(dEntry, 'black', 'orange', entryType)

		elif eval(f'inspect.isbuiltin({dEntry if "Current" in self.crumbs else f"self.exploration.{dEntry}"})'):
			self.listsEntry(dEntry, 'white', 'black', entryType)

		elif eval(f'inspect.isfunction({dEntry if "Current" in self.crumbs else f"self.exploration.{dEntry}"})'):
			self.listsEntry(dEntry, 'white', 'dark green', entryType)

		elif eval(f'inspect.isclass({dEntry if "Current" in self.crumbs else f"self.exploration.{dEntry}"})'):
			self.listsEntry(dEntry, 'white', 'dark red', entryType)

		elif eval(f'inspect.ismodule({dEntry if "Current" in self.crumbs else f"self.exploration.{dEntry}"})'):
			self.listsEntry(dEntry, 'white', 'dark blue', entryType)

		elif eval(f'inspect.ismethod({dEntry if "Current" in self.crumbs else f"self.exploration.{dEntry}"})'):
			self.listsEntry(dEntry, 'black', 'magenta', entryType)

		else:
			entryType = self.wrapper_type(dEntry, entryType)
			self.listsEntry(dEntry, 'black', 'white', entryType)

	def debug(self, state):
		if state == Qt.CheckState.Checked:
			self.debugger = 1
			self.bugcheck.setText("DEBUGGING ON")
		else:
			self.debugger = 0
			self.bugcheck.setText("Debuging Off")

	def dPrint(self, label, data=None):
		if self.debugger == 1:
			if not data:
				print(f"{label}")

			else:
				print(f"{label} = {str(data)}")

	def makeTable(self, dlist, longest):
		self.dPrint("\nMAKING TABLE")
		# self.dPrint("dlist", dlist)
		textwidth = self.text.frameGeometry().width() / 7
		# self.dPrint("textwidth", textwidth)
		cols = int(textwidth / longest)
		# self.dPrint("columns", cols)
		code = f"self.pTable = prettytable.PrettyTable({[i for i in range(cols)]})"
		# self.dPrint("PrettyTable code", code)
		exec(code)
		# self.pTable = PrettyTable(["0", "1", "2"])
		# self.dPrint("self.pTable\n", self.pTable)
		self.pTable.padding_width = 0
		self.pTable.align = "l"
		self.pTable.header = False

		table = self.split(dlist, cols)
		# self.dPrint("table", table)

		for i in table:
			# self.dPrint("list item", i)
			try:
				# self.dPrint("try", i)
				self.pTable.add_row(i)

			except Exception:
				# self.dPrint("except", len(i))
				fix = (cols - len(i))
				# self.dPrint("fix", fix)
				for j in range(fix):
					# self.dPrint("fixing", i)
					i.append("#")
				# self.dPrint("fixed eye", i)
				self.pTable.add_row(i)
		# self.dPrint(str(self.pTable))
		return self.pTable

	def itemSelect(self, item):
		self.dPrint("\nITEM SELECT")
		# self.dPrint("clicked item", item)
		# self.dPrint("THISONE", type(item))
		# self.dPrint("THATONE", item.text())
		self.centering = self.text.width() / 7
		self.cent = r"{: ^" + str(self.centering - 8) + r"s}"
		# self.dPrint('num string', self.cent)
		self.spacer = r"{:_^" + str(self.centering - 8) + r"s}"
		# self.dPrint(item.text())
		self.codeS = self.spacer.format("Code") + "\n\n"
		self.contS = self.spacer.format("Contents") + "\n\n"
		self.docS = self.spacer.format("Document String") + "\n\n"
		self.valS = self.spacer.format("Value") + "\n\n"
		if item != None:
			self.pkg = f"{item.text()}"
		self.pkg2 = self.pkg if not "." in self.pkg else self.pkg.split(".")[-1]
		self.icrumbs = str(".".join(self.crumbs[2:]))
		# self.dPrint("self.pkg", self.pkg)
		# self.dPrint("crumbs", self.crumbs)
		# self.dPrint("icrumbs", self.icrumbs)
		# self.dPrint("Exploration", self.exploration)

		try:
			if len(self.crumbs) >= 2:
				if len(self.crumbs[2:]) == 0:
					# self.dPrint("len(self.crumbs[2:]) == 0:")
					code = f"self.itemType = type({self.pkg}).__name__; self.docstr = {self.pkg}.__doc__"
					code2 = f"self.itemType = type(self.exploration.{self.pkg2}).__name__; self.docstr = self.exploration.{self.pkg2}.__doc__"

					exec(code if 'Current' in self.crumbs else code2)

				else:
					if self.pkg == "..":
						code = f"self.itemType = type({self.icrumbs}); self.docstr = {self.icrumbs}.__doc__"
						code2 = f"self.itemType = type(self.exploration.{self.icrumbs}).__name__; self.docstr = self.exploration.{self.icrumbs}.__doc__"
						exec(code if 'Current' in self.crumbs else code2)

					else:
						code = f"self.itemType = type({self.icrumbs}.{self.pkg2}).__name__; self.docstr = {self.icrumbs}.{self.pkg2}.__doc__"
						code2 = f"self.itemType = type(self.exploration.{self.icrumbs}.{self.pkg2}).__name__; self.docstr = self.exploration.{self.icrumbs}.{self.pkg2}"
						exec(code if 'Current' in self.crumbs else code2)

			else:
				code = f"self.itemType = type(self.exploration.{self.icrumbs}); self.docstr = self.exploration.{self.icrumbs}"
				code2 = f"self.itemType = type(self.exploration.{self.icrumbs}.{self.pkg}).__name__; self.docstr = self.exploration.{self.icrumbs}.{self.pkg}"
				exec(code if self.pkg == '..' else code2)

			if self.docstr == None:
				self.docstr = "No Documentation For Selected Item"

			self.docstr = f"{self.docS}\n\n{self.docstr}\n\n"
			# self.dPrint("self.itemType", str(self.itemType))
			# self.dPrint("self.docstr", str(self.docstr))
			self.getText()

		except AttributeError:
			raise AttributeError
			pass

	def getcode(self, obj):
		self.dPrint("\nGETCODE")
		try:
			sourceLines = "".join(inspect.getsourcelines(self.obj)[0]).replace("\t", "    ")

		except (IOError, TypeError):
			sourceLines = "NO CODE AVAILABLE FIX THIS TODO"  # FIX THIS WITH MATH2 TODO

		return sourceLines

	def parse_crumbs(self):
		self.dPrint("\nPARSE CRUMBS")
		self.pkg2 = self.pkg if not "." in self.pkg else self.pkg.split(".")[-1]
		if len(self.crumbs[2:]) == 0:
			code = f"self.table = dir({self.pkg}); self.obj = {self.pkg}"
			code2 = f"self.table = dir(self.exploration.{self.pkg}); self.obj = self.exploration.{self.pkg}"
			exec(code if 'Current' in self.crumbs else code2)

			# if len(self.crumbs[2:]) == 0:
			# 	code = f"self.table = dir({self.pkg}); self.obj = {self.pkg}"
			# 	self.dPrint("current short self.modDir code", code)
			# 	exec(code)
			# else:
			# 	code = f"self.table = dir({self.icrumbs}.{self.pkg2}); self.obj = {self.icrumbs}.{self.pkg2}"
			# 	self.dPrint("current long self.modDir code", code)
			# 	exec(code)
		# elif len(self.crumbs[2:]) == 0:
		# 	code = f"self.table = dir(self.exploration.{self.pkg}); self.obj = self.exploration.{self.pkg}"
		# 	# self.dPrint("short self.modDir code", code)
		# 	exec(code)
		else:
			code = f"self.table = dir({self.icrumbs}.{self.pkg2}); self.obj = {self.icrumbs}.{self.pkg2}"
			code2 = f"self.table = dir(self.exploration.{self.icrumbs}.{self.pkg2}); self.obj = self.exploration.{self.icrumbs}.{self.pkg2}"
			# self.dPrint("long self.modDir code", code)
			exec(code if 'Current' in self.crumbs else code2)

		return self.table, self.obj

	def typeModule(self):
		self.dPrint("\n<MODULE>")

		self.modDir, self.obj = self.parse_crumbs()

		sourceLines = self.getcode(self.obj)

		longest = len(max(self.modDir, key=len))
		# self.dPrint("longest item", longest)
		tdir = self.makeTable(self.modDir, longest)

		self.highlight.setDocument(self.text.document())

		entry = f"{self.docstr}{self.contS}{str(tdir)}\n\n{self.codeS}{sourceLines}"
		self.setText(entry, 'blueberry_folder.png', 'Module Object')

	def typeClass(self):
		self.dPrint("\n<CLASSOBJ>")

		self.classDir, self.obj = self.parse_crumbs()
		sourceLines = self.getcode(self.obj)
		# self.dPrint("sourceLines", sourceLines)

		longest = len(max(self.classDir, key=len))
		# self.dPrint("longest item", longest)
		tdir = self.makeTable(self.classDir, longest)

		self.highlight.setDocument(self.text.document())

		entry = "{0}{1}{2}\n\n{3}{4}".format(self.docstr, self.contS, str(tdir), self.codeS, sourceLines)

		self.setText(entry, "ruby_folder.png", "Class Object")

	def typeMethod(self):# Fix instance method of code TODO
		self.dPrint("\n<INSTANCE METHOD>")

		self.methodOf, self.obj = self.parse_crumbs()

		methodTitle = self.cent.format(f"Instance Method of {'.'.join(self.crumbs[2:])}.{self.obj.__name__}\n\n")

		sourceLines = self.getcode(self.obj)
		# self.dPrint("sourceLines", sourceLines)

		self.highlight.setDocument(self.text.document())

		# self.dPrint("methodOf", self.methodOf)
		# self.dPrint("sourceLines", sourceLines)

		entry = f"{methodTitle}{self.docstr}{self.codeS}{sourceLines}"
		self.setText(entry, 'parentheses.png', "Instance Method")

	def typeFunction(self): # Fix function of code TODO
		self.dPrint("\n<FUNCTION>")

		self.functionOf, self.obj = self.parse_crumbs()
		# self.dPrint("obj", self.obj)

		functionTitle = self.cent.format(f"Function of {self.functionOf}\n\n")

		sourceLines = self.getcode(self.obj)
		# self.dPrint("sourceLines", sourceLines)

		# self.highlight.setDocument(self.text.document())

		entry = f"{functionTitle}{self.docstr}{self.codeS}#!/usr/bin/python\n# -*- coding: utf-8 -*-\n\n{sourceLines}"
		self.highlight.setDocument(self.text.document())

		self.setText(entry, 'python-bytecode.png', "Function Code")

	def typeWrapper(self):
		self.dPrint("\n<WRAPPERTYPE>")
		# self.dPrint('package:', self.pkg)

		self.classDir, self.obj = self.parse_crumbs()

		# self.dPrint("OBJ:", self.obj)
		sourceLines = self.getcode(self.obj)
		# self.dPrint("sourceLines", sourceLines)

		self.highlight.setDocument(self.text.document())
		#self.highlight.highlightBlock(sourceLines)

		entry = f"{self.cent.format(self.pkg)}\n\n{self.cent.format(self.itemType)}\n\n{self.docstr}{self.codeS}{sourceLines}"
		# self.dPrint('entry', entry)
		self.setText(entry, "ruby_folder.png", "Wrapper Object")

	def typeBuiltin(self):
		self.dPrint("\n<BUILTIN>")
		entry = f"\n\n{self.cent.format('CODE CANNOT BE RETRIEVED FOR BUILTIN FUNCTIONS')}\n\n\nYET\n\n{self.docstr}"
		# self.dPrint("entry", entry)
		self.setText(entry, 'python-builtins.png', "Builtin Functions")

	def typeType(self):
		self.dPrint("\n<TYPE>")
		entry = f"{self.docstr}\n\n{self.cent.format('NO DATA FOR TYPE <TYPE>')}\n\n\nYET"
		# self.dPrint("entry", entry)
		self.setText(entry, 'python-type.png', 'Type Type')

	def typeVariables(self):
		self.dPrint("\n<COLLECTION>")

		_, self.dataObj = self.parse_crumbs()

		entry = f"{self.docstr}{self.valS}{self.dataObj}"
		# self.dPrint('entry', entry)
		self.highlight.setDocument(self.text.document())

		self.setText(entry, 'stickynotes.png', "Collection Object")

	def typePrevious(self):  # ADD PREVIOUS self.direcTORY STRUCTURE TO DOCSTR TODO
		self.dPrint("\n<PREVIOUS>")
		entry = "Put Previous self.directory name and listing here"
		self.setText(entry, "previous.png", "Previous self.directory")

	def typeUnknown(self):  # DOCUMENT SOMETHING HERE SUCH AS DOCSTRING & self.direcTORY TODO
		self.dPrint("\n<UNKNOWN TYPE>")
		entry = f"{self.docstr}"
		# self.dPrint("entry", entry)
		self.setText(entry, 'unknown.png', "Unknown Types")

	def getText(self):
		self.dPrint("\nGETTING TEXT")
		# print("itemType:", self.itemType)
		self.highlight.setDocument(None)
		# self.itemType = self.entryType

		if str(self.pkg) == "..":
			self.typePrevious()

		elif str(self.itemType) == 'wrappertype':
			self.typeWrapper()

		elif self.itemType == 'class':
			self.typeClass()

		elif self.itemType == 'function':
			self.typeFunction()

		elif self.itemType == 'builtin_function_or_method':
			self.typeBuiltin()

		elif self.itemType == 'type':
			self.typeType()

		elif self.itemType == 'module':
			self.typeModule()

		elif self.itemType == 'method':
			self.typeMethod()

		elif self.itemType in self.varlist:
			self.typeVariables()

		else:
			self.dPrint("\n<???UNKNOWN???>")

			self.setText(f"{self.itemType}\n{self.docstr}", 'unknown.png', 'UNKNOWN')

	def setText(self, entry, headImg, title):
		self.dPrint("\nSETTING TEXT")
		self.text.clear()
		self.insertImage(headImg, title)
		self.text.append(entry)
		self.text.verticalScrollBar().setValue(0)

	def repopList(self, item):
		self.dPrint("\nREPOPULATING LIST")
		# self.dPrint("clicked item", item)
		try:
			entry = str(item.text())
			# self.dPrint('item text', entry)
		except AttributeError:
			entry = str(item)

		# self.dPrint("entry", entry)
		self.list.clear()
		self.tlist.clear()

		if entry == "..":
			self.dPrint("\nREPOP PREVIOUS")
			# self.dPrint(self.crumbs)
			self.crumbs.pop()
			# self.dPrint(self.crumbs)

			if len(self.crumbs) > 2:
				self.listsEntry('..', 'white', 'black', 'Previous')

			self.setStatusTip(str(".".join(self.crumbs)))

			if len(self.crumbs[2:]) == 0:

				code = "self.direc = current"
				code2 = "self.direc = dir(self.exploration)"
				exec(code if 'Current' in self.crumbs else code2)

			else:

				code = f"self.direc = dir({'.'.join(self.crumbs[2:])})"
				code2 = f"self.direc = dir(self.exploration.{'.'.join(self.crumbs[2:])})"
				exec(code if 'Current' in self.crumbs else code2)

			self.dPrint("prev self.direc", self.direc)

		elif entry == 'reload':
			self.dPrint("\nRELOADING")
			if len(self.crumbs) > 2:
				self.listsEntry('..', 'white', 'black', 'Previous')

		else:
			self.dPrint("\nREPOP FORWARD")
			self.crumbs.append(entry if not "." in entry else entry.split('.')[-1])
			# self.dPrint("crumbs", self.crumbs)
			self.setStatusTip(str(".".join(self.crumbs)))

			code = "self.direc = dir({0})".format(".".join(self.crumbs[2:]))
			code2 = "self.direc = dir(self.exploration.{0})".format(".".join(self.crumbs[2:]))
			exec(code  if 'Current' in self.crumbs else code2)

			self.listsEntry("..", "white", 'black', 'Previous')

		for i in self.direc:
			dEntry = str(i)
			# self.dPrint("dEntry", dEntry)
			self.crumbs.append(dEntry)
			# self.dPrint("dEntry in crumbs", self.crumbs)
			if "Current" in self.crumbs:

				code = f"self.entryType = type({self.pkg})"
				code2 = f"self.entryType = type({'.'.join(self.crumbs[2:])}).__name__"
				exec(code if len(self.crumbs[2:]) == 0 else code2)

			else:
				code = f"self.entryType = type(self.exploration.{'.'.join(self.crumbs[2:])}).__name__"
				self.dPrint("second self.entryType code", code)
				exec(code)

			# self.dPrint("self.entryType", self.entryType)
			self.typeSort(f'{".".join(self.crumbs[2:])}', self.entryType)
			self.crumbs.remove(dEntry)
			# self.dPrint("dEntry out crumbs", self.crumbs)
			# self.dPrint("THISONEHERE")

	def listsEntry(self, text, tcolor, bcolor, entryType):
		# self.dPrint("\nENTERING LIST ITEM")
		# self.dPrint(f"ARGS: {text}, {tcolor}, {bcolor}, {entryType}")
		itemIn = QListWidgetItem(text)
		itemIn.setForeground(QColor(tcolor))
		itemIn.setBackground(QColor(bcolor))
		entry = str(entryType)
		typeIn = QListWidgetItem(entry)
		typeIn.setForeground(QColor(tcolor))

		typeIn.setToolTip(str(entryType.__doc__))
		typeIn.setBackground(QColor(bcolor))
		self.list.addItem(itemIn)
		self.tlist.addItem(typeIn)

	def setCurrent(self, cursco):
		self.dPrint("\nSET CURRENT")
		self.current = cursco


def main(current):

	app = QApplication(sys.argv)
	app.setApplicationName('Package Browser')
	# app.setStyleSheet("QMainWindow { background-color: black; color: white }")
	Explorer = CodeBrowser(current)
	# Explorer.resize((Explorer.geo.width()/6)*4, (Explorer.geo.height()/4)*3)
	Explorer.setWindowTitle("Package Browser")
	# Explorer.setWindowFlags(Explorer.windowFlags() | QtCore.Qt.FramelessWindowHint)
	Explorer.setStyleSheet("QMainWindow { background-color: black; color: white }")
	# Explorer.resizeEvent.connect()
	# Explorer.showMaximized()
	Explorer.show()

	# stdErrHandler = StdErrHandler() TODO
	# sys.stderr = stdErrHandler
	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec())



# self.dPrint "after import", current

if __name__ == "__main__":
	main(current)