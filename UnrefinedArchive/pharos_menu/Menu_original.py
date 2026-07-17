#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from collections import OrderedDict

import sys, os, time, inspect, psutil



class Menu(QWidget):

	def __init__(self, parent=None):
		super(Menu, self).__init__(parent)
		QWidget.__init__(self)

		self.Ptolemy = parent
		print("MENU PARENT: ", self.Ptolemy)

		_phila = getattr(self.Ptolemy, 'Philadelphos', None)
		self.output = _phila.setOutput if _phila and hasattr(_phila, 'setOutput') else lambda *a, **kw: None
		self.crumbs = []
		self.FILE_MENU_UP = False
		self.currentDir = dir()
		print("USER DIR : " + str(self.currentDir))

		# Menu Vars
		self.menudict = {}
		self.menulist = []
		self.menucounter = 0
		self.menushift = 0

		# File Menu Vars
		self.filemenu = {}
		self.filemenulist = []
		self.filemenucounter = 0
		self.filemenushift = 0

		self.rect = QRect(0, 0, 254, int(self.Ptolemy.scene.height()) - 50)
		self.setGeometry(self.rect)

		# self.setZValue(0)
		self.initUI()

	def initUI(self):

		self.setStyleSheet("QListWidget {background-color: black }")

		self.menu = QListWidget()
		self.menu.setFont(self.Ptolemy.font(12))
		self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.menu.currentItemChanged.connect(self.itemselect)  # FIX THIS TODO
		self.menu.itemClicked.connect(self.itemselect)
		self.menu.itemDoubleClicked.connect(self.repoplist)

		self.layout = QGridLayout(self)
		self.layout.addWidget(self.menu, 0, 0, 31, 2)
		self.layout.setSpacing(0)

		# Build Menu
		self.buildmenu('Pharos', 'Pharos')
		self.crumbs.append('Pharos')
		self.output(str(('after Pharos build', self.crumbs)))

		pass

	def itemselect(self):

		pass

	def getfiletype(self, filename):

		if len(filename.split('.')) > 1:
			fileend = filename.split('.')[1].lower()  # ADD Console Game Types
		else:
			fileend = None

		if fileend in ['py', 'sh', 'html', 'xml', 'xhtml', 'php', 'css', 'js', 'c', 'h', 'pl', 'pm', 'pyc', 'pyo', 'r',
					   'rb', 'tcl', 'vbs', 'bas', 'asp', 'aspx', 'htm', 'jsp', 'rss']:
			filetype = 'code'
		elif fileend in ['txt', 'rtf', 'log', 'srt', 'cfg', 'ini', 'rc']:
			filetype = 'text'
		elif fileend in ['fnt', 'fon', 'otf', 'ttf']:
			filetype = 'font'
		elif fileend in ['doc', 'docx', 'odt', 'tex', 'wpd', 'wps']:
			filetype = 'doc'
		elif fileend in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico', 'cpt', 'mng', 'tga', 'targa', 'icb', 'vda', 'vst',
						 'pix', 'tif', 'tiff', 'xcf', 'psd', 'ai', 'odg', 'xar']:
			filetype = 'image'
		elif fileend in ['svg', 'cdr', 'ai', 'ps']:
			filetype = 'vector'
		elif fileend in ['xlr', 'xls', 'xlsx', 'ods']:
			filetype = 'spreadsheet'
		elif fileend in ['avi', 'asf', 'asx', 'flv', 'mkv', 'rm', 'mov', 'mpg', 'mpeg', 'mpe', 'mp4', 'ogg', 'swf',
						 'wmv', 'vob']:
			filetype = 'video'
		elif fileend in ['wav', 'cdda', 'mp3', 'wma', 'm4a', 'mp4', 'm4p', 'aac', 'ra', 'mid', 'aif', 'iff', 'm3u',
						 'mpa']:
			filetype = 'audio'
		elif fileend in ['pdf', 'dvi', ]:
			filetype = 'pdf'
		elif fileend in ['zip', '7z', 'bz2', 'gz', 'tar', 'egg', 'rar']:
			filetype = 'archive'
		elif fileend in ['apk', 'jar', 'deb', 'bat', 'com', 'exe', 'cgi', 'vb', 'pif', 'rpm']:
			filetype = 'execute'
		elif fileend in ['iso', 'img', 'bin', 'cue']:
			filetype = 'iso'
		elif fileend in ['db', 'sql', 'csv', 'accdb', 'dbf', 'pdb', 'mdb']:
			filetype = 'database'
		elif fileend in ['nes', 'sfc', 'gb', 'gba', 'gbc', 'z64', 'nds']:
			filetype = 'rom'
		else:
			filetype = None

		return filetype

	def repoplist(self, item):
		self.itemtext = item.text()
		self.output(('\naMenu list', self.menulist), 'cyan')
		# self.output(('\naMenu dict', self.menudict), 'cyan')
		self.output(('\nItem stuff', self.itemtext), 'cyan')

		if self.FILE_MENU_UP == False:
			try:
				citem = self.menulist.index(self.itemtext)
			except ValueError:
				citem = -1
		# print 'menu citem', citem, self.menulist

		else:
			try:
				citem = self.filemenulist.index(self.itemtext)
			except ValueError:
				citem = -1
		# print 'filemenu citem', citem, self.filemenulist

		# print "fml", self.filemenulist
		# fitem = self.filemenulist.index(self.itemtext)
		# if fitem == 0 and self.filemenulist[0] == 'Pharos':
		# 	fitem = 2
		# print 'fitem', fitem, self.filemenulist

		for i in self.menudict:
			if self.menudict[i] == 'title':
				title = i

		if self.FILE_MENU_UP == False:

			# for i in range(citem):
			# 	print '\ni', i

			# Menu Title
			if citem + 1 == 1:  ###INSERT DOCSTRING FOR MENU TITLE##### TODO
				print("Clicked Pharos Title")

			# Back Button
			if citem == -1:

				if len(self.crumbs) == 1:
					pass
				if len(self.crumbs) > 1:
					pm = self.crumbs.pop(-1)
					breadcrumbs = '.'.join(self.crumbs)
					code = 'path = ' + breadcrumbs + '\n' + 'title = ' + "'" + breadcrumbs.split('.')[-1] + "'"
					self.output(("Code", code), 'green')
					exec(code)
					self.buildmenu(str(path), title)

					self.Ptolemy.Pharos.identity = title

			# File Manager Button
			elif citem + 1 == 2:
				# self.menu.clear()
				self.FILE_MENU_UP = True
				self.buildfilemenu()

			# Menu Button Class/Module

			elif self.menudict[self.menulist[citem]] == 'class' or self.menudict[self.menulist[citem]] == 'module':

				self.crumbs.append(self.menulist[citem])
				breadcrumbs = '.'.join(self.crumbs)
				code = 'path = ' + breadcrumbs
				exec(code)
				self.buildmenu(str(path), self.menulist[citem])

				self.Ptolemy.Pharos.identity = self.itemtext
			# self.drawmenu()

			# Menu Button Function
			elif self.menudict[self.menulist[citem]] == 'function' or self.menudict[self.menulist[citem]] == 'method':
				self.crumbs.append(self.menulist[i])
				self.parent.WindowManager.newwindow('function')

			# Menu Button Builtin
			elif self.menudict[self.menulist[citem]] == 'builtin':
				self.crumbs.append(self.menulist[citem])
				self.parent.WindowManager.newwindow('builtin')

			# Menu Button Value
			elif self.menudict[self.menulist[citem]] == 'value':
				self.crumbs.append(self.menulist[citem])
				code = 'value = ' + '.'.join(self.crumbs)
				exec(code)
				self.setoutput('.'.join(self.crumbs) + ' : ' + str(value))
				self.crumbs.pop()

		elif self.FILE_MENU_UP == True:

			# File Manager Title
			if citem + 1 == 1:  ###INSERT DOCSTRING FOR MENU TITLE#####
				print
				'File Manager Title'

			# Pharos Menu Button
			if citem == -1:

				self.FILE_MENU_UP = False
				self.buildmenu('Pharos', 'Pharos')

			# File Manager Current Dir
			elif citem + 1 == 2:
				self.setoutput(str(os.getcwd()))

			# File Manager Dir
			elif self.filemenu[self.filemenulist[citem]] == 'dir' or self.filemenu[self.filemenulist[citem]] == 'prev':
				if len(os.getcwd().split('/')) == 1:
					pass
				if len(os.getcwd().split('/')) > 1:
					os.chdir(self.filemenulist[citem])
					self.buildfilemenu()

			# File Manager File
			elif self.filemenu[self.filemenulist[citem]] == 'file':
				filetype = self.getfiletype(self.filemenulist[citem])

				if filetype == None:
					self.setoutput('File Manager : Unknown File Type', 'light red')
				else:
					self.parent.WindowManager.newwindow(filetype, wincontent=self.filemenulist[citem])
		pass

	def boundingRect(self):
		return self.rect

	def mousePressEvent(self, event):

		print("menu object clicked")
		# if self.FILE_MENU_UP == True:
		# 	mh = self.filemenucounter * 23
		# else:
		# 	mh = self.menucounter * 23
		# tc = (self.windowcounter * 65) - 65  #
		# eym = event.y() / 23
		# eyt = event.y() / 65
		# for i in self.menudict:
		# 	if self.menudict[i] == 'title':
		# 		title = i
		# w = self.screen.width()
		# h = self.screen.height()
		# brush = self.brush('black')
		# pen = self.pen('white')

		# if self.CONTEXT_MENU == True:
		# 	ContextMenu.contextevent(event)
		# else:
		#
		# 	# Left Click Menu
		# 	if event.button() == QtCore.Qt.LeftButton:
		#
		# 		self.Philadelphos.setoutput(str(self.scene.itemAt(event.x(), event.y())))
		#
		# 		if self.FILE_MENU_UP == False:
		# 			citem = eym - self.menushift
		# 			# Menu Title
		# 			if citem + 1 == 1:  ###INSERT DOCSTRING FOR MENU TITLE#####
		# 				print 'Menu Title'
		#
		# 			# Back Button
		# 			elif citem == self.menucounter - 1:
		# 				if len(self.crumbs) == 1:
		# 					pass
		# 				if len(self.crumbs) > 1:
		# 					for i in self.menug.childItems():
		# 						self.menug.removeFromGroup(i)
		# 						self.scene.removeItem(i)
		# 						del i
		# 					pm = self.crumbs.pop(-1)  #
		# 					breadcrumbs = '.'.join(self.crumbs)
		# 					code = 'pth = ' + breadcrumbs + '\n' + 'title = ' + "'" + breadcrumbs + "'"
		# 					exec code
		# 					self.buildmenu(pth, title)
		# 					self.drawmenu()
		#
		# 			# File Manager Button
		# 			elif citem + 1 == 2:
		# 				for i in self.menug.childItems():
		# 					self.menug.removeFromGroup(i)
		# 					self.scene.removeItem(i)
		# 					del i
		# 				self.FILE_MENU_UP = True
		# 				self.buildfilemenu()
		# 				self.drawfilemenu()
		#
		# 			# Menu Button Class/Module
		# 			elif self.menu[self.menulist[citem]] == 'class' or self.menu[self.menulist[citem]] == 'module':
		# 				for i in self.menug.childItems():
		# 					self.menug.removeFromGroup(i)
		# 					self.scene.removeItem(i)
		# 					del i
		# 				self.crumbs.append(self.menulist[citem])
		# 				breadcrumbs = '.'.join(self.crumbs)
		# 				code = 'pth = ' + breadcrumbs
		# 				exec code
		# 				self.buildmenu(pth, self.menulist[citem])
		# 				self.drawmenu()
		#
		# 			# Menu Button Function
		# 			elif self.menu[self.menulist[citem]] == 'function' or self.menu[
		# 				self.menulist[citem]] == 'method':
		# 				self.crumbs.append(self.menulist[citem])
		# 				Win.newwindow(event, 'function')
		#
		# 			# Menu Button Builtin
		# 			elif self.menu[self.menulist[citem]] == 'builtin':
		# 				self.crumbs.append(self.menulist[citem])
		# 				Win.newwindow(event, 'builtin')
		#
		# 			# Menu Button Value
		# 			elif self.menu[self.menulist[citem]] == 'value':
		# 				self.crumbs.append(self.menulist[citem])
		# 				code = 'value = ' + '.'.join(self.crumbs)
		# 				exec code
		# 				self.setoutput('.'.join(self.crumbs) + ' : ' + str(value))
		# 				self.crumbs.pop()
		#
		# 		elif self.FILE_MENU_UP == True:
		# 			citem = eym - self.filemenushift
		#
		# 			# File Manager Title
		# 			if citem + 1 == 1:  ###INSERT DOCSTRING FOR MENU TITLE#####
		# 				print 'Menu Title'
		#
		# 			# File Manager Current Dir
		# 			if citem + 1 == 2:
		# 				self.setoutput(str(os.getcwd()))
		#
		# 			# File Manager Dir
		# 			elif self.filemenu[self.filemenulist[citem]] == 'dir' or self.filemenu[
		# 				self.filemenulist[citem]] == 'prev':
		# 				if len(os.getcwd().split('/')) == 1:
		# 					pass
		# 				if len(os.getcwd().split('/')) > 1:
		# 					for i in self.filemenug.childItems():
		# 						self.filemenug.removeFromGroup(i)
		# 						self.scene.removeItem(i)
		# 						del i
		# 					os.chdir(self.filemenulist[citem])
		# 					self.buildfilemenu()
		# 					self.drawfilemenu()
		#
		# 			# Pharos Button
		# 			elif citem + 1 == 3:
		# 				for i in self.filemenug.childItems():
		# 					self.filemenug.removeFromGroup(i)
		# 					self.scene.removeItem(i)
		# 					del i
		# 				self.FILE_MENU_UP = False
		# 				self.buildmenu(Pharos, 'Pharos')
		# 				self.drawmenu()
		#
		# 			# File Manager File
		# 			elif self.filemenu[self.filemenulist[citem]] == 'file':
		# 				filetype = self.getfiletype(self.filemenulist[citem])
		#
		# 				if filetype == None:
		# 					self.setoutput('File Manager : Unknown File Type', 'red')
		# 				else:
		# 					self.WindowManager.newwindow(event, filetype, wincontent=self.filemenulist[citem])
		#
		#
		# 	# Right click
		# 	elif event.button() == QtCore.Qt.RightButton:
		#
		# 		# Right Click Menu
		# 		if 0 < event.x() < 254 and 0 < event.y() < h - 50:
		# 			if self.FILE_MENU_UP == False:
		# 				if self.CONTEXT_MENU == False:
		# 					self.CONTEXT_MENU = True
		# 					ContextMenu.buildcontextmenu('menu', event)
		# 			else:
		# 				if self.CONTEXT_MENU == False:
		# 					self.CONTEXT_MENU = True
		# 					ContextMenu.buildcontextmenu('fileman', event)
		#
		#
		# 	# Middle Click
		# 	elif event.button() == QtCore.Qt.MiddleButton:  #####
		# 		print 'Mouse Middle Button'
		#
		pass

	def clearmenu(self):

		for item in self.menug.childItems():
			self.menug.removeItem(item)

	def listentry(self, text, tcolor='white', bcolor='black'):

		itemIn = QListWidgetItem(text)
		itemIn.setForeground(QColor(tcolor))
		itemIn.setBackground(QColor(bcolor))

		self.menu.addItem(itemIn)

	# Ptolemy Menu
	def buildmenu(self, module, title):
		# self.crumbs.append('Pharos')

		self.menu.clear()

		self.menudict = {}
		self.menulist = []
		self.menucounter = 0
		self.menushift = 0

		self.menudict[title] = 'title'
		self.menudict['back'] = 'back'
		self.menudict['File Manager'] = 'File Manager'

		# print(inspect.getmembers(Pharos))

		for name, obj in inspect.getmembers(module):

			if inspect.isbuiltin(obj):
				self.menudict[name] = 'builtin'

			elif inspect.isfunction(obj):
				self.menudict[name] = 'function'

			elif inspect.ismodule(obj):
				self.menudict[name] = 'module'

			elif inspect.ismethod(obj):
				self.menudict[name] = 'method'

			elif type(obj) == str or type(obj) == int or type(obj) == float or type(obj) == list or type(
					obj) == tuple or type(obj) == dict or type(obj) == list:
				self.menudict[name] = 'value'

			elif type(obj):
				self.menudict[name] = 'class'

		self.menuDict = {}
		###Clean Dict (no __*__ entries)#
		for i in self.menudict.keys():  #
			if i.startswith("__"):
				pass
			else:
				self.menuDict[i] = self.menudict[i]  #



		self.drawmenu()

	def drawmenu(self):

		# self.menu.clear()

		for name, obj in self.menuDict.items():
			if obj == 'title':
				modulename = name
				self.listentry(modulename, 'orange', 'darkred')
				self.menulist.append(modulename)
				self.menucounter += 1

		self.listentry('File Manager', 'cyan', 'darkblue')
		self.menulist.append('File Manager')
		self.menucounter += 1

		for i in OrderedDict(sorted(self.menuDict.items(), key=lambda key: key[0].lower())):
			if self.menuDict[i] == 'class':
				self.listentry(i, 'red')
				self.menulist.append(i)
				self.menucounter += 1

			elif self.menuDict[i] == 'function':
				self.listentry(i, 'white')
				self.menulist.append(i)
				self.menucounter += 1

			elif self.menuDict[i] == 'module':
				self.listentry(i, 'green')
				self.menulist.append(i)
				self.menucounter += 1

			elif self.menuDict[i] == 'builtin':
				self.listentry(i, 'cyan')
				self.menulist.append(i)
				self.menucounter += 1

			elif self.menuDict[i] == 'method':
				self.listentry(i, 'magenta')
				self.menulist.append(i)
				self.menucounter += 1

			elif self.menuDict[i] == 'value':
				self.listentry(i, 'orange')
				self.menulist.append(i)
				self.menucounter += 1

		if len(self.crumbs) <= 1:
			self.listentry("TOP MENU", 'red')
			self.menulist.append(i)
			self.menucounter += 1

		elif len(self.crumbs) > 1:
			self.listentry(self.menuDict['back'], 'red')
			self.menulist.append(i)
			self.menucounter += 1

	# File Menu
	def buildfilemenu(self):

		self.menu.clear()

		self.filemenu = {}
		self.filemenulist = []
		self.filemenucounter = 0
		self.filemenushift = 0

		self.filemenu['File Manager'] = 'title'
		self.filemenu[str(os.getcwd().split('/')[-1])] = 'current'
		self.filemenu['..'] = 'prev'
		self.filemenu['Pharos'] = 'Pharos'

		for i in os.listdir(os.getcwd()):
			if os.path.isfile(i):
				self.filemenu[i] = 'file'
			# self.filemenulist.append(i)
			else:
				self.filemenu[i] = 'dir'
			self.filemenulist.append(i)

		self.drawfilemenu()

	def drawfilemenu(self):

		# self.menu.clear()

		self.filemenushift = 0

		for name, obj in self.filemenu.items():
			if obj == 'title':
				modulename = name
				self.listentry(modulename, 'white', 'darkblue')
				# self.drawfilebutton(modulename, 'red', 'blue', 'white')
				self.filemenucounter += 1
				self.filemenulist.append(modulename)

		for name, obj in self.filemenu.items():
			if obj == 'current':
				modulename = name
				self.listentry("~/" + modulename, 'white', 'darkblue')
				self.filemenucounter += 1
				self.filemenulist.append(modulename)

		self.listentry(self.filemenu['Pharos'], 'orange', 'darkred')
		self.filemenucounter += 1
		self.filemenulist.append('Pharos')

		for name, obj in self.filemenu.items():
			if obj == 'prev':
				modulename = name
				self.listentry(modulename, 'red', 'black')
				self.filemenucounter += 1
				self.filemenulist.append(modulename)

		# for i in OrderedDict(sorted(self.filemenu.items(), key=lambda key: key[0].lower)):
		for i in sorted(self.filemenu.keys()):
			# for i in self.filemenu.keys().sort(key=lambda v: v.lower()):#FIX ORDER ALPHABETICALLY HERE TODO
			if self.filemenu[i] == 'dir':
				self.listentry(i, 'red')
				self.filemenucounter += 1
				self.filemenulist.append(i)

		# for i in OrderedDict(sorted(self.filemenu.items(), key=lambda key: key[0].lower)):
		for i in sorted(self.filemenu.keys()):
			# for i in self.filemenu.keys().sort(key=lambda v: v.lower()):
			if self.filemenu[i] == 'file':
				self.listentry(i, 'cyan')
				self.filemenucounter += 1
				self.filemenulist.append(i)