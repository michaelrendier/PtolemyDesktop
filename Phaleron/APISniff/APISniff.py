#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import QEvent, QUrl, Qt
from PyQt6.QtGui import QAction, QIcon, QFont, QImage, QImageReader, QTextDocument, QTextImageFormat, QTextCursor, QCursor, QColor
from PyQt6.QtWidgets import QMainWindow, QListWidget, QCheckBox, QWidget, QTextEdit, QGridLayout, QInputDialog, QListWidgetItem, QApplication

from Syntax import PythonHighlighter
from Dialogs import Dialogs

import sys, os, time, inspect, psutil, types, urllib

crumbsRoot = dir()

class CodeBrowser(QMainWindow):
	"""File manager like browser for installed python packages as well as current program scope.
	"""
	
	def __init__(self, crumbs, parent=None):
		super(CodeBrowser, self).__init__(parent)
		self.setWindowTitle("Package Browser")
		
		self.Parent= parent
		print("CODEBROWSER PARENT:", self.Parent)
		

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
		
		self.current = crumbs
		# if curScope:
		# 	self.current = curScope
		# else:
		# 	self.current = current
		# print "self.current =", self.
		self.reimport = 0
		self.debugger = 1
		self.sitems = []
		self.typelist = ['bool', 'buffer', 'builtin_function_or_method',
						 "<type 'builtin_function_or_method'>", "<type 'classobj'>", "<type 'code'>",
						 "<type 'complex'>", "<type 'dictproxy'>", "<type 'dict'>", "<type 'dict'>",
						 "<type 'ellipsis'>", "<type 'file'>", "<type 'float'>", "<type 'frame'>", "<type 'function'>",
						 "<type 'generator'>", "<type  'getset_descriptor'>", "<type 'instance'>", "<type 'int'>",
						 "<type 'function'>", "<type 'list'>", "<type 'long'>", "<type 'member_descriptor'>",
						 "<type 'instancemethod'>", "<type 'module'>", "<type 'NoneType'>",
						 "<type 'NotImplementedType'>", "<type 'object'>", "<type 'slice'>", "<type 'str'>",
						 "<type 'traceback'>", "<type 'tuple'>", "<type 'type'>", "<type 'instancemethod'>",
						 "<type 'unicode'>", "<type 'xrange'>"]
		# self.entryType = ""
		
		self.initUI()
	
	# TODO
	def __del__(self):
		pass
	
	def initUI(self):
		
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
		exitAction.triggered.connect(qApp.quit)
		
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
		self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.list.currentItemChanged.connect(self.itemSelect)
		self.list.itemClicked.connect(self.itemSelect)
		self.list.itemDoubleClicked.connect(self.repopList)
		self.list.verticalScrollBar().valueChanged.connect(self.tlist.verticalScrollBar().setValue)
		
		# Type List Setup
		self.tlist.setFont(QFont('Monospace', 9))
		self.list.setFixedWidth(300)
		self.tlist.setMaximumWidth(300)
		self.tlist.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.tlist.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
	
	# self.raise_()
	# self.activateWindow()
	# self.setFocus()
	# self.show()
	
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
		"""http://stackoverflow.com/questions/15539075/inserting-qimage-after-string-in-qtextedit
		user1006989
		"""
		# FIND ICON PACK TO MAKE IMAGES WITH FOR EACH BUILT IN TYPE TODO
		# FIX ENTERING GRAPHIC TITLE TODO
		self.dPrint("\nINSERTING IMAGE")
		# imageUri = QUrl(QString("./progImages/{0}".format(filePath)))
		imageUri = QUrl(self.imgDir + filePath)
		image = QImage(QImageReader(filePath).read())
		# headerUri = QtCore.QUrl(QtCore.QString("file://home/rendier/JARVIS/working/rectgradient.jpg"))
		headerUri = QUrl(self.imgDir + 'rectgradient.jpg')
		header = QImage(QImageReader(self.imgDir + 'rectgradient.jpg').read())
		
		self.text.document().addResource(QTextDocument.ImageResource, headerUri, QVariant(header))
		
		imageHeader = QTextImageFormat()
		imageHeader.setWidth(240)
		imageHeader.setHeight(88)
		imageHeader.setName(headerUri.toString())
		
		self.text.document().addResource(QTextDocument.ImageResource, imageUri, QVariant(image))
		
		imageFormat = QTextImageFormat()
		imageFormat.setWidth(88)
		imageFormat.setHeight(88)
		imageFormat.setName(imageUri.toString())
		
		textCursor = self.text.textCursor()
		textCursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
		
		textCursor.insertImage(imageHeader)
		textCursor.insertImage(imageFormat)
		headerCentered = ((self.centering - len(title)) / 2) - 4
		self.text.append(self.spacer.format(title) + "\n\n")
		
		# This will hide the cursor
		blankCursor = QCursor(Qt.BlankCursor)
		self.text.setCursor(blankCursor)
	
	def importPkg(self):  # FIX INPUT DIALOG COLORS TODO
		self.dPrint("\nIMPORTING PACKAGE")
		self.dPrint("importPkg", dir())
		
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
				self.setWindowTitle("Browsing Python {0} Module".format(text))
			self.package = str(text)
			self.dPrint("package", self.package)
			if self.package == "":
				self.package = "Current"
				self.exploration = current
				self.addItems()
			
			elif self.package.count(".") == 1:
				try:
					parts = self.package.split(".")
					self.package = str(parts[1])
					code = "self.exploration = getattr(__import__('{0}', globals(), locals(), ['{1}',]), '{0}')".format(
						parts[1], parts[0])
					self.dPrint("from import", code)
					exec(code)
					self.addItems()
				
				except ImportError:
					self.dPrint("Module {0} does not exist".format(".".join(parts)))
					self.reimport = 1
					self.importPkg()
			
			elif self.package.count(".") > 1:  # FIX MULTI IMPORT (OR LEARN WHY NOT) TODO
				
				parts = list(self.package.split("."))
				self.package = str(parts[-1])
				try:
					code = "self.exploration = getattr(__import__('{1}', globals(), locals(), ['{0}',], -1), '{0}')".format(
						parts[-1], ".".join(parts[:-1]))
					self.dPrint("multi import code", code)
					exec(code)
					self.addItems()
				
				except ImportError:
					try:
						self.dPrint("Checking if {0} is builtin...".format(parts[-1]))
						code = "self.exploration = __import__('{0}')".format(parts[-1])
						self.dPrint("import error builtin check code", code)
						exec(code)
						self.addItems()
					
					except ImportError:
						self.dPrint("Module {0} does not exist".format(".".join(parts)))
						self.reimport = 1
						self.importPkg()
			
			else:
				try:
					code = "self.exploration = __import__('{0}')".format(self.package)
					self.dPrint("import code", code)
					exec(code)
					self.addItems()
				
				except ImportError:
					self.dPrint("Module {0} does not exist".format(self.package))
					self.reimport = 1
					self.importPkg()
	
	def searchList(self):
		if self.sitems:
			self.sitems = []
			self.repopList('reload')
		
		term, ok = QInputDialog.getText(self, "List Search", "Enter Search Term for Current List")
		
		if ok:
			self.sitems = self.list.findItems(term, Qt.MatchContains)
			for i in self.sitems:
				i.setForeground(QColor('red'))
			
			dlist = self.modDir
			longest = len(max(self.modDir, key=len))
			self.dPrint("longest item", longest)
			tdir = self.makeTable(dlist, longest)
			
			entry = [str(i.text()) for i in self.sitems]
			longest = len(max(entry, key=len))
			self.dPrint("longest item", longest)
			table = self.split(entry, 3)
			result = self.makeTable(table)
			self.setText(str(result), 'search-icon.png', 'Search Results')
	
	def addItems(self):  # MAKE TO USE ONLY REPOP LIST TODO
		
		self.status.setStatusTip(str(".".join(self.crumbs)))
		self.list.clear()
		self.tlist.clear()
		self.text.clear()
		
		if self.package == "Current":
			self.dPrint('\nADDING DIR()')
			# Breadcrumbs
			self.crumbs = ['Explorer', 'Current']
			self.icrumbs = []
			
			for i in self.current:
				dEntry = i
				self.dPrint("dEntry is:", dEntry)
				# print("I : ", i)
				# print("TYPE : ", type(i))
				# print("DIR : ", dir(i))
				# print("INSPECT : ", inspect.isclass(i))
				code = f"self.entryType = type({dEntry})"
				self.dPrint("entry code", code)
				exec(code)
				print("I : ", dEntry)
				print("TYPE : ", eval('type({0})'.format(dEntry)))
				# print("DIR : ", dir(dEntry))
				print("INSPECT : ", eval('inspect.isclass({0})'.format(dEntry)))
				print("ENTRYTYPE : ", self.entryType.__name__)
				self.typeSort(dEntry, self.entryType)
		
		else:
			# Breadcrumbs
			self.dPrint("\nADDING PACKAGE")
			self.crumbs = ['Explorer', self.package]
			self.icrumbs = []
			
			for i in dir(self.exploration):
				dEntry = i
				self.dPrint("dEntry", dEntry)
				print("INSPECT : ", inspect.isbuiltin(i))
				code = "self.entryType = type(self.exploration.{0})".format(dEntry)
				self.dPrint("entry code", code)
				exec(code)
				self.typeSort(dEntry, self.entryType)
	
	def typeSort(self, dEntry, entryType):
		self.dPrint("\nSORTING")
		print("ARGS : ", dEntry, entryType)
		
		if dEntry.startswith("__") and dEntry.endswith("__"):
			self.listsEntry(dEntry, 'black', 'light blue', entryType)
		
		elif str(entryType.__name__) == 'PyQt5.QtCore.pyqtWrapperType':  # MAKE SO CAN ALTER FOR SDK WRAPPERS TODO
			self.listsEntry(dEntry, 'black', 'light green', entryType)
		
		elif str(entryType) not in self.typelist:
			self.listsEntry(dEntry, "black", 'white', entryType)
		
		elif entryType == types.TypeVar:
			self.listsEntry(dEntry, 'white', 'grey', entryType)
		
		elif eval('inspect.isclass({0})'.format(dEntry)):
			self.listsEntry(dEntry, 'white', 'dark red', entryType)
		
		elif entryType.__name__ == 'module':
			self.listsEntry(dEntry, 'white', 'dark blue', entryType.__name__)
		
		elif entryType == types.FunctionType:
			self.listsEntry(dEntry, 'white', 'dark green', entryType)
		
		elif entryType == types.BuiltinFunctionType:
			self.listsEntry(dEntry, 'white', 'black', entryType)
		
		elif entryType == types.MethodType:
			self.listsEntry(dEntry, 'white', 'purple', entryType)
		
		elif entryType in (dict, str, list, tuple):
			self.listsEntry(dEntry, 'black', 'yellow', entryType)
		
		else:
			self.listsEntry(dEntry, 'black', 'white', entryType)
	
	def debug(self, state):
		if state == Qt.Checked:
			self.debugger = 1
			self.bugcheck.setText("DEBUGGING ON")
		else:
			self.debugger = 0
			self.bugcheck.setText("Debuging Off")
	
	def dPrint(self, label, data=None):
		if self.debugger == 1:
			if not data:
				print("{0}".format(label))
			
			else:
				print("{0} = {1}".format(label, str(data)))
	
	def makeTable(self, dlist, longest):
		self.dPrint("\nMAKING TABLE")
		self.dPrint("dlist", dlist)
		textwidth = self.text.frameGeometry().width() / 7
		self.dPrint("textwidth", textwidth)
		cols = (textwidth / longest)
		self.dPrint("columns", cols)
		code = "self.pTable = prettytable.PrettyTable({0})".format([i for i in range(cols)])
		self.dPrint("PrettyTable code", code)
		exec(code)
		# self.pTable = PrettyTable(["0", "1", "2"])
		self.dPrint("self.pTable\n", self.pTable)
		self.pTable.padding_width = 0
		self.pTable.align = "l"
		self.pTable.header = False
		
		table = self.split(dlist, cols)
		self.dPrint("table", table)
		
		for i in table:
			self.dPrint("list item", i)
			try:
				# self.dPrint("try", i)
				self.pTable.add_row(i)
			
			except Exception:
				self.dPrint("except", len(i))
				fix = (cols - len(i))
				self.dPrint("fix", fix)
				for j in range(fix):
					self.dPrint("fixing", i)
					i.append("#")
				self.dPrint("fixed eye", i)
				self.pTable.add_row(i)
		self.dPrint(str(self.pTable))
		return self.pTable
	
	def itemSelect(self, item):
		self.dPrint("\nITEM SELECT")
		self.dPrint("clicked item", item)
		self.centering = self.text.width() / 7
		self.cent = r"{: ^" + str(self.centering - 8) + r"s}"
		print('num string', self.cent)
		self.spacer = r"{:_^" + str(self.centering - 8) + r"s}"
		# self.dPrint(item.text())
		self.codeS = self.spacer.format("Code") + "\n\n"
		self.contS = self.spacer.format("Contents") + "\n\n"
		self.docS = self.spacer.format("Document String") + "\n\n"
		self.valS = self.spacer.format("Value") + "\n\n"
		
		try:
			self.pkg = "{0}".format(item.text())
			self.icrumbs = str(".".join(self.crumbs[2:]))
			self.dPrint("self.pkg", self.pkg)
			self.dPrint("crumbs", self.crumbs)
			self.dPrint("icrumbs", self.icrumbs)
			
			if len(self.crumbs) >= 2:
				if len(self.crumbs[2:]) == 0:
					if 'Current' in self.crumbs:
						code = "self.itemType = type({0}); self.docstr = {0}.__doc__".format(self.pkg)
						self.dPrint("current short self.itemType code", code)
						exec(code)
					else:
						code = "self.itemType = type(self.exploration.{0}); self.docstr = self.exploration.{0}.__doc__".format(
							self.pkg)
						self.dPrint("short self.itemType code", code)
						exec(code)
				
				else:
					if self.pkg == "..":
						if 'Current' in self.crumbs:
							code = "self.itemType = type({0}); self.docstr = {0}.__doc__".format(current)
							self.dPrint("long Current prev self.itemType code", code)
							exec(code)
						else:
							code = "self.itemType = type(self.exploration); self.docstr = self.exploration.__doc__"
							self.dPrint("long prev self.itemType", code)
							exec(code)
					
					else:
						if 'Current' in self.crumbs:
							code = "self.itemType = type({0}.{1}); self.docstr = {0}.{1}.__doc__".format(self.icrumbs,
																										 self.pkg)
							self.dPrint("current long self.itemType code", code)
							exec(code)
						else:
							code = "self.itemType = type(self.exploration.{0}.{1}); self.docstr = self.exploration.{0}.{1}".format(
								self.icrumbs, self.pkg)
							self.dPrint("long self.itemType", code)
							exec(code)
				
				if self.docstr == None:
					self.docstr = "No Documentation For Selected Item"
			
			else:
				if self.pkg == "..":
					code = "self.itemType = type(self.exploration.{0}); self.docstr = self.exploration.{0}".format(
						self.icrumbs)
					self.dPrint("prev code", code)
					exec(code)
				
				else:
					code = "self.itemType = type(self.exploration.{0}.{1}); self.docstr = self.exploration.{0}.{1}".format(
						self.icrumbs, self.pkg)
					self.dPrint("pkg code", code)
					exec(code)
				
				if self.docstr == None:
					self.docstr = "No Documentation For Selected Item"
			
			self.docstr = "{0}\n\n{1}\n\n".format(self.docS, self.docstr)
			self.dPrint("self.itemType", str(self.itemType))
			self.dPrint("self.docstr", str(self.docstr))
			self.getText()
		
		except AttributeError:
			pass
	
	def typeModule(self):
		self.dPrint("\n<MODULE>")
		if 'Current' in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "self.modDir = dir({0}); obj = {0}".format(self.pkg)
				self.dPrint("current short self.modDir code", code)
				exec(code)
			else:
				code = "self.modDir = dir({0}.{1}); obj = {0}.{1}".format(self.icrumbs, self.pkg)
				self.dPrint("current long self.modDir code", code)
				exec(code)
		elif len(self.crumbs[2:]) == 0:
			code = "self.modDir = dir(self.exploration.{0}); obj = self.exploration.{0}".format(self.pkg)
			self.dPrint("short self.modDir code", code)
			exec(code)
		else:
			code = "self.modDir = dir(self.exploration.{0}.{1}); obj = self.exploration.{0}.{1}".format(self.icrumbs,
																										self.pkg)
			self.dPrint("long self.modDir code", code)
			exec(code)
		try:
			sourceLines = "".join(inspect.getsourcelines(obj)[0]).replace("\t", "    ")
			self.highlight.highlightBlock(sourceLines)
		
		except (IOError, TypeError):
			sourceLines = "NO CODE AVAILABLE FIX THIS TODO"  # FIX THIS WITH MATH2 TODO
		self.dPrint("sourceLines", sourceLines)
		
		dlist = self.modDir
		longest = len(max(self.modDir, key=len))
		self.dPrint("longest item", longest)
		tdir = self.makeTable(dlist, longest)
		
		self.highlight.setDocument(self.text.document())
		
		entry = "{0}{1}{2}\n\n{3}{4}".format(self.docstr, self.conS, str(tdir), self.codeS, sourceLines)
		
		self.setText(entry, 'blueberry_folder.png', 'Module Directory')
	
	def typePrivate(self):
		self.dPrint("\n<PYPRIVATE>")
		if 'Current' in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "pyPrivate = {0}".format(self.pkg)
				self.dPrint("current short pyPrivate code", code)
				exec(code)
			else:
				code = "pyPrivate = {0}.{1}".format(self.icrumbs, self.pkg)
				self.dPrint("current long pyPrivate code", code)
				exec(code)
		elif len(self.crumbs[2:]) == 0:
			code = "pyPrivate = self.exploration.{0}".format(self.pkg)
			self.dPrint("short PyPrivate code", code)
			exec(code)
		else:
			code = "pyPrivate = self.exploration.{0}.{1}".format(self.icrumbs, self.pkg)
			self.dPrint("long PyPrivate code", code)
			exec(code)
		
		self.dPrint("PyPrivate", pyPrivate)
		entry = "{0}{1}{2}".format(self.docstr, self.valS,
								   [str(pyPrivate) if str(pyPrivate) not in self.docstr else "See Doc String"][0])
		
		if self.itemType in (dict, int, str, list, float, complex):
			self.highlight.setDocument(self.text.document())
		
		self.setText(entry, "private-folder.png", "Private Python Data")
	
	def typePyqtWrapper(self):
		self.dPrint("\n<CLASSOBJ>")
		if 'Current' in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "classDir = dir({0}); obj = {0}".format(self.pkg)
				self.dPrint("current short classDir code", code)
				exec(code)
			else:
				code = "classDir = dir({0}.{1}); obj = {0}.{1}".format(self.icrumbs, self.pkg)
				self.dPrint("current long classDir code", code)
				exec(code)
		else:
			code = "classDir = dir(self.exploration.{0}); obj = self.exploration.{0}".format(self.pkg)
			self.dPrint("classDir", code)
			exec(code)
		
		try:
			sourceLines = "".join(inspect.getsourcelines(obj)[0]).replace("\t", "    ")
		
		except IOError:
			sourceLines = "NO CODE AVAILABLE FIX THIS TODO"  # FIX THIS WITH MATH2 TODO
		self.dPrint("sourceLines", sourceLines)
		
		self.highlight.setDocument(self.text.document())
		
		entry = "{0}\n\n{1}\n\n{2}{3}{4}".format(self.cent.format(self.pkg), self.cent.format(self.itemType),
												 self.docstr, self.codeS, sourceLines)
		self.dPrint('entry', entry)
		self.setText(entry, "ruby_folder.png", "PyQt Class Object")
	
	def typeClass(self):
		self.dPrint("\n<CLASSOBJ>")
		if 'Current' in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "classDir = dir({0}); obj = {0}".format(self.pkg)
				self.dPrint("current short classDir code", code)
				exec(code)
			else:
				code = "classDir = dir({0}.{1}); obj = {0}.{1}".format(self.icrumbs, self.pkg)
				self.dPrint("current long classDir code", code)
				exec(code)
		else:
			code = "classDir = dir(self.exploration.{0}); obj = self.exploration.{0}".format(self.pkg)
			self.dPrint("classDir", code)
			exec(code)
		
		try:
			sourceLines = "".join(inspect.getsourcelines(obj)[0]).replace("\t", "    ")
		
		except IOError:
			sourceLines = "NO CODE AVAILABLE FIX THIS TODO"  # FIX THIS WITH MATH2 TODO
		self.dPrint("sourceLines", sourceLines)
		
		dlist = classDir
		longest = len(max(classDir, key=len))
		self.dPrint("longest item", longest)
		tdir = self.makeTable(dlist, longest)
		
		self.highlight.setDocument(self.text.document())
		
		entry = "{0}{1}{2}\n\n{3}{4}".format(self.docstr, self.conS, str(tdir), self.codeS, sourceLines)
		
		self.setText(entry, "ruby_folder.png", "Class Object")
	
	def typeFunction(self):
		self.dPrint("\n<FUNCTION>")
		if 'Current' in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "obj = {0}".format(self.pkg)
				self.dPrint("current short obj code", code)
				exec(code)
			else:
				code = "obj = {0}.{1}".format(self.icrumbs, self.pkg)
				self.dPrint("current long obj code", code)
				exec(code)
		elif len(self.crumbs[2:]) == 0:
			code = "obj = self.exploration.{0}".format(self.pkg)
			self.dPrint("not icrumbs code", code)
			exec(code)
		else:
			code = "obj = self.exploration.{0}.{1}".format(self.icrumbs, self.pkg)
			self.dPrint("icrumbs code", code)
			exec(code)
		self.dPrint("obj", obj)
		
		try:
			sourceLines = "".join(inspect.getsourcelines(obj)[0]).replace("\t", "    ")
		
		except IOError:
			sourceLines = "NO CODE AVAILABLE FIX THIS TODO"  # FIX THIS WITH MATH2 TODO
		self.dPrint("sourceLines", sourceLines)
		
		self.highlight.setDocument(self.text.document())
		
		entry = "#!/usr/bin/python\n# -*- coding: utf-8 -*-\n\n{0}".format(sourceLines)
		self.highlight.setDocument(self.text.document())
		
		self.setText(entry, 'python-bytecode.png', "Function Code")
	
	def typeBuiltin(self):
		self.dPrint("\n<BUILTIN>")
		entry = "\n\n{0}\n\n\nYET\n\n{1}".format(self.cent.format("CODE CANNOT BE RETRIEVED FOR BUILTIN FUNCTIONS"),
												 self.docstr)
		self.dPrint("entry", entry)
		self.setText(entry, 'python-builtins.png', "Builtin Functions")
	
	def typeType(self):
		self.dPrint("\n<TYPE>")
		entry = "{0}\n\n{1}\n\n\nYET".format(self.docstr, self.cent.format("NO DATA FOR TYPE 'TYPE'"))
		self.dPrint("entry", entry)
		self.setText(entry, 'python-type.png', 'Type Type')
	
	def typeCollection(self):
		self.dPrint("\n<COLLECTION>")
		if 'Current' in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "dataObj = {0}".format(self.pkg)
				self.dPrint("current short dataObj code", code)
				exec(code)
			else:
				code = "dataObj = {0}.{1}".format(self.icrumbs, self.pkg)
				self.dPrint("current long dataObj code", code)
				exec(code)
		elif len(self.crumbs[2:]) == 0:
			code = "dataObj = (self.exploration.{0})".format(self.pkg)
			self.dPrint('short dataObj code', code)
			exec(code)
		else:
			code = "dataObj = (self.exploration.{0}.{1})".format(self.icrumbs, self.pkg)
			self.dPrint("long dataObj code", code)
			exec(code)
		
		entry = "{0}{1}{2}".format(self.docstr, self.valS, dataObj)
		self.dPrint('entry', entry)
		self.highlight.setDocument(self.text.document())
		
		self.setText(entry, 'stickynotes.png', "Collection Object")
	
	def typePrevious(self):  # ADD PREVIOUS self.direcTORY STRUCTURE TO DOCSTR TODO
		self.dPrint("\n<PREVIOUS>")
		entry = "Put Previous self.directory name and listing here"
		self.setText(entry, "previous.png", "Previous self.directory")
	
	def typeUnknown(self):  # DOCUMENT SOMETHING HERE SUCH AS DOCSTRING & self.direcTORY TODO
		self.dPrint("\n<UNKNOWN TYPE>")
		entry = "{0}".format(self.docstr)
		self.dPrint("entry", entry)
		self.setText(entry, 'unknown.png', "Unknown Types")
	
	def typeInstanceMethod(self):
		self.dPrint("\n<INSTANCE METHOD>")
		if "Current" in self.crumbs:
			if len(self.crumbs[2:]) == 0:
				code = "obj = {0}; methodOf = getattr({0}, '__self__', {0}).__class__".format(self.pkg)
				self.dPrint("current short methodOf code", code)
				exec(code)
			else:
				code = "obj = {0}.{1}; methodOf = getattr({0}.{1}, '__self__', {0}.{1}).__class__".format(self.icrumbs, self.pkg)
				self.dPrint("current long methodOf code", code)
				exec(code)

		elif len(self.crumbs[2:]) == 0:
			code = "obj = self.exploration.{0}; methodOf = getattr(self.exploration.{0}, '__self__', self.exploration.{0}).__class__".format(self.pkg)
			self.dPrint("short methodOf code", code)
			exec(code)

		else:
			code = "obj = self.exploration.{0}.{1}; methodOf = getattr(self.exploration.{0}.{1}, '__self__', self.exploration.{0}.{1}).__class__".format(self.icrumbs, self.pkg)
			self.dPrint("long methodOf code", code)
			exec(code)
		
		methodTitle = self.cent.format("Instance Method of {0}".format(methodOf)) + "\n\n"
		
		try:
			sourceLines = "".join(inspect.getsourcelines(obj)[0]).replace("\t", "    ")
		
		except IOError:
			sourceLines = "NO CODE AVAILABLE FIX THIS TODO"  # FIX THIS WITH MATH2 TODO
		self.dPrint("sourceLines", sourceLines)
		
		self.highlight.setDocument(self.text.document())
		
		self.dPrint("methodOf", methodOf)
		self.dPrint("sourceLines", sourceLines)
		
		entry = "{0}{1}{2}{3}".format(methodTitle, self.docstr, self.codeS, sourceLines)
		self.setText(entry, 'parentheses.png', "Instance Method")
		pass
	
	def getText(self):
		self.dPrint("\nGETTING TEXT")
		self.highlight.setDocument(None)
		
		if str(self.pkg) == "..":
			self.typePrevious()
		elif str(self.itemType) == "<type 'PyQt4.QtCore.pyqtWrapperType'>":
			self.typePyqtWrapper()
		
		
		elif str(self.itemType) not in self.typelist:
			self.typeUnknown()
		
		elif str(self.pkg).startswith("__") and str(self.pkg).endswith("__") == True:
			self.typePrivate()
		
		elif self.itemType == types.ClassType:
			self.typeClass()
		
		elif self.itemType == types.FunctionType:
			self.typeFunction()
		
		elif self.itemType == types.BuiltinFunctionType:
			self.typeBuiltin()
		
		elif self.itemType == types.TypeType:
			self.typeType()
		
		elif self.itemType == types.ModuleType:
			self.typeModule()
		
		elif self.itemType == types.MethodType:
			self.typeInstanceMethod()
		
		elif self.itemType not in (types.BuiltinFunctionType, types.MethodType) and self.itemType in (float, str, list, tuple, int, dict):
			self.typeCollection()
		
		else:
			self.dPrint("\n<???UNKNOWN???>")
			
			self.setText("{0}\n{1}".format(self.itemType, self.docstr), 'unknown.png', 'UNKNOWN')
	
	def setText(self, entry, headImg, title):
		self.dPrint("\nSETTING TEXT")
		self.text.clear()
		self.insertImage(headImg, title)
		self.text.append(entry)
		self.text.verticalScrollBar().setValue(0)
	
	def repopList(self, item):
		self.dPrint("\nREPOPULATING LIST")
		self.dPrint("clicked item", item)
		try:
			entry = str(item.text())
			self.dPrint('item text', entry)
		except AttributeError:
			entry = str(item)
		
		self.dPrint("entry", entry)
		self.list.clear()
		self.tlist.clear()
		
		if entry == "..":
			self.dPrint("\nREPOP PREVIOUS")
			self.dPrint(self.crumbs)
			self.crumbs.pop()
			self.dPrint(self.crumbs)
			
			if len(self.crumbs) > 2:
				self.listsEntry('..', 'white', 'black', 'Previous')
			
			self.setStatusTip(str(".".join(self.crumbs)))
			
			if 'Current' in self.crumbs:
				if len(self.crumbs[2:]) == 0:
					code = "self.direc = dir()".format(self.pkg)
					self.dPrint("current short self.direc code", code)
					exec(code)
				else:
					code = "self.direc = dir({0})".format(self.icrumbs, self.pkg)
					self.dPrint("current long self.direc code", code)
					exec(code)
			
			if len(self.crumbs[2:]) == 0:
				if "Current" in self.crumbs:
					code = "self.direc = current"
					self.dPrint("current prev top self.direc code")
					exec(code)
				else:
					code = "self.direc = dir(self.exploration)"
					self.dPrint("prev top self.direc code", code)
					exec(code)
			else:
				if "Current" in self.crumbs:
					code = "self.direc = dir({0})".format(".".join(self.crumbs[2:]))
					self.dPrint("current previous deep code", code)
					exec(code)
				else:
					code = "self.direc = dir(self.exploration.{0})".format(".".join(self.crumbs[2:]))
					self.dPrint("prev deep code", code)
					exec(code)
			
			self.dPrint("prev self.direc", self.direc)
		
		elif entry == 'reload':
			self.dPrint("\nRELOADING")
			if len(self.crumbs) > 2:
				self.listsEntry('..', 'white', 'black', 'Previous')
		
		else:
			self.dPrint("\nREPOP FORWARD")
			self.crumbs.append(entry)
			self.dPrint("crumbs", self.crumbs)
			self.setStatusTip(str(".".join(self.crumbs)))
			if "Current" in self.crumbs:
				code = "self.direc = dir({0})".format(".".join(self.crumbs[2:]))
				self.dPrint("Current self.direc code", code)
				exec(code)
			else:
				code = "self.direc = dir(self.exploration.{0})".format(".".join(self.crumbs[2:]))
				self.dPrint("self.direc code", code)
				exec(code)
			self.dPrint("forward self.direc", self.direc)
			self.listsEntry("..", "white", 'black', 'Previous')
		
		for i in self.direc:
			dEntry = str(i)
			self.dPrint("dEntry", dEntry)
			self.crumbs.append(dEntry)
			self.dPrint("dEntry in crumbs", self.crumbs)
			if "Current" in self.crumbs:
				if len(self.crumbs[2:]) == 0:
					code = "self.entryType = type({0})".format(self.pkg)
					self.dPrint("current short self.entryType code", code)
					exec(code)
				
				else:
					code = "self.entryType = type({0})".format(".".join(self.crumbs[2:]))
					self.dPrint("current long self.entryType code", code)
					exec(code)
			
			else:
				code = "self.entryType = type(self.exploration.{0})".format(".".join(self.crumbs[2:]))
				self.dPrint("self.entryType code", code)
				exec(code)
			
			self.dPrint("self.entryType", self.entryType)
			self.typeSort(dEntry, self.entryType)
			self.crumbs.remove(dEntry)
			self.dPrint("dEntry out crumbs", self.crumbs)
	
	def listsEntry(self, text, tcolor, bcolor, entryType):
		self.dPrint("\nENTERING LIST ITEM")
		itemIn = QListWidgetItem(text)
		itemIn.setForeground(QColor(tcolor))
		itemIn.setBackground(QColor(bcolor))
		entry = str(entryType).replace("<type '", "").replace("'>", "").capitalize().replace("Classobj", "Class Object") \
			.replace("Builtin_function_or_method", "Builtin Functions").replace("Str", "String").replace("Dict",
																										 "Dictionary").replace(
			"Pyqt4.qtcore.pyqtwrappertype", "PyQt4 Wrapper **")  # .replace("")
		typeIn = QListWidgetItem(entry)
		typeIn.setForeground(QColor(tcolor))
		
		typeIn.setToolTip(str(entryType.__doc__))
		typeIn.setBackground(QColor(bcolor))
		self.list.addItem(itemIn)
		self.tlist.addItem(typeIn)
	
	def setCurrent(self, cursco):
		self.current = cursco


def main(object):
	
	# def __init__(self, crumbsRoot, parent=None):
	# 	super(main, self).__init__(parent)
		
	app = QApplication(sys.argv)
	app.setApplicationName('Package Browser')
	# app.setStyleSheet("QMainWindow { background-color: black; color: white }")
	Explorer = CodeBrowser(crumbsRoot)
	# Explorer.resize((Explorer.geo.width()/6)*4, (Explorer.geo.height()/4)*3)
	Explorer.setWindowTitle("Package Browser")
	# Explorer.setWindowFlags(Explorer.windowFlags() | QtCore.Qt.FramelessWindowHint)
	Explorer.setStyleSheet("QMainWindow { background-color: black; color: white }")
	# Explorer.resizeEvent.connect()
	# Explorer.showMaximized()
	Explorer.show()
	
	# stdErrHandler = StdErrHandler()
	# sys.stderr = stdErrHandler
	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec_())


# print "after import", current

if __name__ == "__main__":
	print("THIS FIRST", crumbsRoot)
	print("THIS SECOND", dir())
	# main(crumbsRoot)