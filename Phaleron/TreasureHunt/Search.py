#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWidgets import *


from Phaleron.Syntax import PythonHighlighter

from bs4 import BeautifulSoup
from html2text import html2text
from PIL import Image
from ast import literal_eval
from urllib.request import build_opener
from urllib.error import HTTPError, URLError
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)

import os, urllib, string, bleach






class Search(QWidget):
	
	def __init__(self, parent=None):
		super(Search, self).__init__(parent)
		QWidget.__init__(self)
		
		self.parent = parent.parentWidget()
		
		# self.setFixedSize(150, 150)
		self.setStyleSheet(self.parent.styles)
		self.setAutoFillBackground(True)
		
		self.initUI()
	
	# Clean Up Objects TODO
	def __del__(self):
		
		pass
	
	def initUI(self):
		
		# Combo Box
		self.searchType = QComboBox(self)
		self.searchType.addItems(
			['Search Type?', 'wikiArticle', 'wikiFormula', 'wikiGroup', 'wikiInfobox', 'wikiPeriodicUpdate',
			 'wikiToWandering'])
		
		# Search Box
		self.searchIn = QLineEdit(self)
		self.searchIn.returnPressed.connect(self.searchClicked)
		
		# Search Button
		self.searchGo = QPushButton('Search', self)
		self.searchGo.setToolTip('Perform Search')
		self.searchGo.clicked.connect(self.searchClicked)
		
		# Wiki Group Button
		self.groupView = QPushButton("Wikipedia Groups", self)
		self.groupView.setToolTip("View Wikipedia Group Books")
		self.groupView.clicked.connect(self.wikiGroupView)
		
		# Wiki Periodic Button
		self.wikiPeriodicView = QPushButton('Periodic Table', self)
		self.wikiPeriodicView.setToolTip('View the Wikipedia Periodic Table')
		self.wikiPeriodicView.clicked.connect(self.wikiPeriodicTable)
		
		# Layout
		self.layout = QGridLayout(self)
		self.layout.addWidget(self.searchType, 0, 0, 1, 1)
		self.layout.addWidget(self.searchIn, 1, 0, 1, 1)
		self.layout.addWidget(self.searchGo, 2, 0, 1, 1)
		self.layout.addWidget(self.groupView, 3, 0, 1, 1)
		self.layout.addWidget(self.wikiPeriodicView, 4, 0, 1, 1)
		self.setLayout(self.layout)
	
	# Enable Button ONLY with not default selected and search term entered #fix code and table names thing TODO
	# Fix code.compile thing todo
	def searchClicked(self):
		# print self.searchType.currentText()
		code = "self.{0}('{1}')".format(self.searchType.currentText(), self.searchIn.text())
		# print 'searching code =', code
		try:
			exec(code)
		except SyntaxError:
			self.infoBox('No Selection', "Pleace choose a Search Type first.")
	
	def wikiGroupView(self):
		self.gView = WikiGroup(parent=self)
		self.parent.addTab(self.gView, "Wiki Group")
	
	# TODO
	def wikiPeriodicTable(self):
		
		sql = "SELECT * FROM `TESTdb`.`JARVIS_searchDicts` WHERE `searchName` = 'periodicTable'"
		args = []
		row = self.parent.database.dbReturnF1(sql, args)
		self.periodicDict = literal_eval(row[2])
		
		self.converter = WebkitRenderer()
		self.converter.format = "png"
		self.converter.width = 500
		# self.converter.height = 275
		
		# print "main geo", Jarvis.geo
		self.periodicWidget = QWidget(self)
		self.periodicWidget.setStyleSheet("QWidget { background-color: black; }")
		self.periodicWidget.setAutoFillBackground(True)
		
		self.periodicList = QComboBox(self.periodicWidget)
		self.periodicList.setFixedWidth(125)
		self.periodicList.setStyleSheet(self.parent.styles)
		self.periodicList.addItems(
			['Hydrogen', 'Helium', 'Lithium', 'Beryllium', 'Boron', 'Carbon', 'Nitrogen', 'Oxygen', 'Fluorine', 'Neon',
			 'Sodium', 'Magnesium', 'Aluminium', 'Silicon', 'Phosphorus', 'Sulfur', 'Chlorine', 'Argon', 'Potassium',
			 'Calcium', 'Scandium', 'Titanium', 'Vanadium', 'Chromium', 'Manganese', 'Iron', 'Cobalt', 'Nickel',
			 'Copper', 'Zinc', 'Gallium', 'Germanium', 'Arsenic', 'Selenium', 'Bromine', 'Krypton', 'Rubidium',
			 'Strontium', 'Yttrium', 'Zirconium', 'Niobium', 'Molybdenum', 'Technetium', 'Ruthenium', 'Rhodium',
			 'Palladium', 'Silver', 'Cadmium', 'Indium', 'Tin', 'Antimony', 'Tellurium', 'Iodine', 'Xenon', 'Caesium',
			 'Barium', 'Lanthanum', 'Cerium', 'Praseodymium', 'Neodymium', 'Promethium', 'Samarium', 'Europium',
			 'Gadolinium', 'Terbium', 'Dysprosium', 'Holmium', 'Erbium', 'Thulium', 'Ytterbium', 'Lutetium', 'Hafnium',
			 'Tantalum', 'Tungsten', 'Rhenium', 'Osmium', 'Iridium', 'Platinum', 'Gold', 'Mercury_(element)',
			 'Thallium', 'Lead', 'Bismuth', 'Polonium', 'Astatine', 'Radon', 'Francium', 'Radium', 'Actinium',
			 'Thorium', 'Protactinium', 'Uranium', 'Neptunium', 'Plutonium', 'Americium', 'Curium', 'Berkelium',
			 'Californium', 'Einsteinium', 'Fermium', 'Mendelevium', 'Nobelium', 'Lawrencium', 'Rutherfordium',
			 'Dubnium', 'Seaborgium', 'Bohrium', 'Hassium', 'Meitnerium', 'Darmstadtium', 'Roentgenium', 'Copernicium',
			 'Ununtrium', 'Flerovium', 'Ununpentium', 'Livermorium', 'Ununseptium', 'Ununoctium'])
		self.periodicList.activated[str].connect(self.wikiPeriodicTableChange)
		
		self.periodicTable = QTableWidget(self.periodicWidget)
		# self.periodicTable.setStyleSheet("QTableWidget { background-color: white; color: black }")
		
		# print "Loading Hydrogen"
		self.wikiPeriodicTableChange('Hydrogen')
		
		self.periodicLayout = QGridLayout(self.periodicWidget)
		self.periodicLayout.addWidget(self.periodicList)
		self.periodicLayout.addWidget(self.periodicTable)
		self.setLayout(self.periodicLayout)
		self.parent.addTab(self.periodicWidget, 'Periodic Table')
		pass
	
	def wikiPeriodicTableChange(self, value):
		
		# print "value =", value
		try:
			self.periodicTable.clear()
		except AttributeError:
			pass
		
		self.element = self.periodicDict[str(value)]
		self.headList = self.element[0]
		self.valueDict = self.element[1]
		self.valueList = []
		
		for i in self.headList:
			self.valueList.append(self.valueDict[i])
		
		self.headList.append('Vapor Pressure')
		self.headList.append("Stable Isotopes")
		
		self.periodicTable.setStyleSheet(self.parent.styles)
		self.periodicTable.setRowCount(len(self.headList))
		self.periodicTable.setFont(QFont('Monospace', 9))
		self.periodicTable.setColumnCount(1)
		self.periodicTable.setColumnWidth(0, self.parent.win.width() - 350)
		self.periodicTable.horizontalHeader().setStretchLastSection(True)
		self.periodicTable.horizontalHeader().hide()
		self.periodicTable.setVerticalHeaderLabels(self.headList)
		# self.periodicTable.setVerticalHeaderItem().setTextAlignment(QtCore.Qt.AlignRight)
		
		# print "Loading {0}".format(value)
		cell = 0
		for i in self.valueList:
			newitem = QTableWidgetItem(i)
			self.periodicTable.setItem(cell, 0, newitem)
			cell += 1
		
		soup = BeautifulSoup(self.element[2])
		rows = len(soup.findAll('tr'))
		
		vapeHtml = self.element[2]
		vapeHtml = vapeHtml.replace('<table',
									"<table width=\"100%\" text-decoration=\"none\" cellspacing=\"0\" border=\"1\"")
		
		self.cellVape = QTextBrowser()
		self.cellVape.setStyleSheet("QTextBrowser { background-color: white; color: black; text-decoration: none }")
		self.cellVape.setMaximumWidth(self.parent.win.width() - 350)
		self.cellVape.setHtml(vapeHtml)
		
		self.periodicTable.setCellWidget(cell, 0, self.cellVape)
		self.periodicTable.resizeRowToContents(cell)
		self.periodicTable.setRowHeight(cell, ((rows * 26)))
		cell += 1
		
		soup = BeautifulSoup(self.element[3])
		self.rows = len(soup.findAll('tr'))
		
		these = ['span', 'tr', 'html', 'th', 'sup', 'table', 'td', 'body']
		isosHtml = bleach.clean(self.element[3], tags=these, strip=True)
		isosHtml = isosHtml.replace('<table', "<table width=\"100%\" cellspacing=\"0\" border=\"1\"")
		isosHtml = isosHtml.replace('<title>',
         # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
									"<link rel=\"stylesheet\" type=\"text/css\" href=\PTOL_ROOT + "/stylesheet.css\"><title>")
		# isosHtml = isosHtml.replace('')
		
		self.isosWeb = QTextBrowser()
		self.isosWeb.setStyleSheet("QTextBrowser { background-color: white; color: black; text-decoration: none }")
		self.isosWeb.setMaximumWidth(self.parent.win.width() - 350)
		self.isosWeb.setHtml(isosHtml)
		
		self.periodicTable.setCellWidget(cell, 0, self.isosWeb)
		self.periodicTable.resizeRowToContents(cell)
		self.periodicTable.setRowHeight(cell, (((self.rows) * 23)))
		self.headList.remove('Vapor Pressure')
		self.headList.remove('Stable Isotopes')
		pass
	
	def wikiFormula(self, searchterm):
		
		self.formulaGet = SearchThread(self.parent, 2, searchterm)
		self.formulaGet.formulaFinished.connect(self.searchResults)
		self.formulaGet.searchHTTPError.connect(self.parent.dialogs.infoBox)
		self.formulaGet.start()
	
	def wikiInfobox(self, searchterm):
		
		self.infoboxGet = SearchThread(self.parent, 4, searchterm)
		self.infoboxGet.infoboxFinished.connect(self.htmlView)
		self.infoboxGet.infoboxNotExist.connect(self.parent.dialogs.infoBox)
		self.infoboxGet.searchHTTPError.connect(self.parent.dialogs.infoBox)
		self.infoboxGet.searchURLError.connect(self.parent.dialogs.infoBox)
		self.infoboxGet.start()
	
	def wikiPeriodicUpdate(self, misc):
		
		self.periodicUpdate = SearchThread(self.parent, 5, misc)
		self.periodicUpdate.periodicFinished.connect(self.wikiPeriodicTable)
		self.periodicUpdate.searchHTTPError.connect(self.parent.dialogs.infoBox)
		self.periodicUpdate.searchURLError.connect(self.parent.dialogs.infoBox)
		self.periodicUpdate.start()
	
	def wikiGroup(self, topPage):
		
		self.groupGet = SearchThread(self.parent, 3, topPage)
		self.groupGet.groupFinished.connect(self.wikiGroupView)
		self.groupGet.searchHTTPError.connect(self.parent.dialogs.infoBox)
		self.groupGet.start()
	
	def wikiArticle(self, searchterm):
		
		# self.emit(QtCore.SIGNAL('indicatorChange(QString)'), 'red')
		self.articleGet = SearchThread(self.parent, 1, searchterm)
		self.articleGet.articleFinished.connect(self.htmlView)
		self.articleGet.searchHTTPError.connect(self.parent.dialogs.infoBox)
		self.articleGet.searchURLError.connect(self.parent.dialogs.infoBox)
		self.articleGet.start()
	
	def htmlView(self, content):
		
		# QSett = QWebSettings.globalSettings()
		# QSett.setAttribute(QWebSettings.PluginsEnabled, True)
		# QSett.setAttribute(QWebSettings.JavaEnabled, True)
		# QSett.setAttribute(QWebSettings.JavascriptEnabled, True)
		# QSett.setAttribute(QWebSettings.SiteSpecificQuirksEnabled, True)
		# QSett.setAttribute(QWebSettings.Accelerated2dCanvasEnabled, True)
		# QSett.setAttribute(QWebSettings.AcceleratedCompositingEnabled, True)
		# QSett.setAttribute(QWebSettings.AutoLoadImages, True)
		# QSett.setAttribute(QWebSettings.CSSGridLayoutEnabled, True)
		# QSett.setAttribute(QWebSettings.AutoLoadImages, True)
		# QSett.setAttribute(QWebSettings.CSSRegionsEnabled, True)
		# QSett.setAttribute(QWebSettings.HyperlinkAuditingEnabled, True)
		# QSett.setAttribute(QWebSettings.JavascriptCanAccessClipboard, True)
		# QSett.setAttribute(QWebSettings.JavascriptCanOpenWindows, True)
		# QSett.setAttribute(QWebSettings.JavascriptCanCloseWindows, True)
		# QSett.setAttribute(QWebSettings.JavascriptEnabled, True)
		# QSett.setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True)
		# QSett.setAttribute(QWebSettings.LocalContentCanAccessFileUrls, True)
		# QSett.setAttribute(QWebSettings.WebGLEnabled, True)
		# QSett.setAttribute(QWebSettings.ZoomTextOnly, True)
		
		QSett = QWebEngineSettings.globalSettings()
		QSett.setAttribute(QWebEngineSettings.PluginsEnabled, True)
		QSett.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
		QSett.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
		QSett.setAttribute(QWebEngineSettings.AutoLoadImages, True)
		QSett.setAttribute(QWebEngineSettings.AutoLoadImages, True)
		QSett.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, True)
		QSett.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
		QSett.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
		QSett.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
		QSett.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
		QSett.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
		QSett.setAttribute(QWebEngineSettings.WebGLEnabled, True)
		
		# print content
		# self.webView = QWebView(parent=self)
		self.webView = QWebEngineView(parent=self)
		# self.webView.setStyleSheet(self.parent.styles)
		self.webView.setHtml(content)
		self.parent.addTab(self.webView, self.searchIn.text())
	
	# FIX HARVESTTEXTIMAGES TODO
	def textView(self, content):
		
		self.txtView = QTextBrowser(parent=self)
		self.txtView.setStyleSheet(self.parent.styles)
		
		self.highlighter = PythonHighlighter(self.searchText.document())
		self.highlighter.setDocument(None)
		
		if cType == 'text':
			self.txtView.append(content)
		elif cType == 'html':
			soup = self.harvestSoupImages(content, "{0}/temp/harvest/".format(self.parent.homeDir))
			self.txtView.setHtml(soup)
		self.parent.addTab(self.txtView, self.searchIn.text())
		
		pass
	
	# CLEAN THIS UP TODO
	def searchResults(self, content):
		
		# print "search results ", content
		self.searchWidget = QWidget(self)
		self.searchWidget.setStyleSheet(self.parent.styles)
		self.searchLayout = QGridLayout(self.searchWidget)
		self.searchText = QTextBrowser(self.searchWidget)
		self.searchText.setStyleSheet(self.parent.styles)
		self.searchText.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.highlighter = PythonHighlighter(self.searchText.document())
		self.highlighter.setDocument(None)
		
		# print "\nSIZING APPENDING"
		# self.searchText.append("{0}\n\n".format(url))
		imageWidths = {}
		for i in content:
			i = literal_eval(i)
			# print 'i =', i
			name = i[1].split("/")[-1] + ".png"
			# print 'mangled =', name
			img = Image.open(name)
			# print 'image size =', img.size[0]
			imageWidths[name] = img.size[0]
			
			self.searchText.append(i[0] + "\n")
			self.searchText.insertHtml(
				"<img src='./temp/latex/{0}' style='background-color: white'>\n".format(i[1].split("/")[-1]))
			self.searchText.append("\n\n")
		
		os.chdir("../..")
		self.searchLayout.addWidget(self.searchText)
		self.searchText.moveCursor(QTextCursor.Start)
		self.parent.addTab(self.searchWidget, 'Formula')


# work on thread indicator TODO
class SearchThread(QThread):
	# Signals
	indicatorChange = pyqtSignal(str)
	searchHTTPError = pyqtSignal(list)
	searchURLError = pyqtSignal(list)
	articleFinished = pyqtSignal(str)
	groupFinished = pyqtSignal()
	infoboxNotExist = pyqtSignal(list)
	infoboxFinished = pyqtSignal(str)
	formulaFinished = pyqtSignal(str)
	periodicFinished = pyqtSignal()
	
	def __init__(self, parent, stype, *args):
		
		super(SearchThread, self).__init__(parent)
		QThread.__init__(self)
		
		self.parent = parent
		print('SearchThread Parent')
		print(self.parent)
		
		self.stype = stype
		self.args = []
		for arg in args:
			self.args.append(arg)
	
	# self.indicatorWORK = ThreadIndicator("WORK")
	# self.status.addPermanentWidget(self.indicatorWORK)
	# self.indicatorWORK.show()
	
	def run(self):
		# self.emit(QtCore.SIGNAL("indicatorChange(QString)"), "red")
		if self.stype == 1:
			self.wikiArticleGet(self.args[0])
		
		elif self.stype == 2:
			self.wikiFormulaGet(self.args[0])
		
		elif self.stype == 3:
			self.wikiGroupGet(self.args[0])
		
		elif self.stype == 4:
			self.wikiInfoboxGet(self.args[0])
		
		elif self.stype == 5:
			self.wikiPeriodicUpdateGet()
	
	def getHtmlSoup(self, url, text):
		
		try:
			infile = self.parent.opener.open(url)
			page = infile.read()
			soup = BeautifulSoup(page, 'lxml')
			return soup
		
		except HTTPError:
			
			self.searchHTTPError.emit([text + ' HTTP Error', '404 Error\nPage Not Found.'])
		
		except URLError:
			
			self.searchURLError.emit([text + ' URL Error', 'Can not find the internet.'])
	
	def harvestSoupImages(self, content, tmpPath):
		
		soup = BeautifulSoup(str(content), 'lxml')
		print(tmpPath)
		imgs = []
		for i in soup.findAll('img'):
			imgs.append(i.get('src'))
		# print 'imgs =', imgs
		imgList = ["http:{0}".format(i.get('src')) for i in soup.findAll('img')]
		# print "imglist", imgList
		os.chdir(tmpPath)
		# print 'cwd =', os.getcwd()
		# os.system('rm *')
		dbprint("\nDOWNLOADING SOUP IMAGES")
		for i in imgList:
			self.fileName = urllib.request.unquote(i.split("/")[-1]).replace("(", "").replace(")", "")
			# print "self.filename --> ", self.fileName
			
			if os.path.isfile(self.fileName):
				pass
			else:
				os.system("wget -q -O {0} {1}".format(self.fileName, i))
		
		dbprint("\nREPLACING SOUP IMAGES")
		
		for i in soup.findAll('img'):
			# print "i.attrs.src =", i.attrs['src']
			fileName = urllib.request.unquote(i.get('src').split("/")[-1]).replace('(', '').replace(')', '')
			# print "fileName =", fileName
			print("{0}{1}".format(tmpPath, fileName))
			i.attrs['src'] = "{0}{1}".format(tmpPath, fileName)
		# print 'i.attrs.src after', i.attrs['src']
		# print "TRYING THIS SOUP", unicode(soup)
		print(os.getcwd())
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		os.chdir(PTOL_ROOT + '/')
		# print "cwd =", os.getcwd()
		return soup
	
	def wikiArticleGet(self, searchterm):  # Search for Entry in Database First and load TODO
		
		url = "http://en.wikipedia.org/w/index.php?title={0}".format(urllib.request.quote(searchterm))
		
		soup = self.getHtmlSoup(url, 'article')
		if soup == None:
			pass
		else:
			content = soup.find('div', attrs={'id': 'mw-content-text'})
			
			for i in content.findAll('table'):  # soup.findAll('table', attrs={'class': 'infobox'}):
				i.attrs['width'] = "352"
				i.attrs['border'] = '1'
				i.attrs['bordercolor'] = 'black'
				try:
					i.attrs['style'] = str(i.attrs['style'] + ';float:right;')
				except KeyError:
					i.attrs['style'] = 'float:right;'
			
			soup = self.harvestSoupImages(content,
										  'temp/harvest/article/')  # "{0}/temp/harvest/article/".format(self.parent.homeDir))
			# print soup
			self.articleFinished.emit(str(soup))
	
	def wikiGroupGet(self, topPage):
		
		refDir = "media/reference/wikipedia"
		url = "https://en.wikipedia.org/w/index.php?title={0}&printable=yes".format(urllib.request.quote(topPage))
		soup = self.getHtmlSoup(url, 'group')
		html = soup
		content = soup.find('table', attrs={'class': 'vertical-navbox nowraplinks'})
		# print 'content\n', str(content)
		saniTopPage = ""
		for letter in topPage:
			if letter.lower() in string.ascii_lowercase:
				saniTopPage = saniTopPage + letter.lower()
		# print "saniTopPage", saniTopPage
		
		groupList = [topPage]
		for i in content.findAll('a'):
			if i.attrs['href'].startswith('/wiki/') and not i.attrs['href'].startswith('/wiki/Template'):
				groupList.append(urllib.request.unquote(i.get('href').split("/")[-1]))
		# print "groupList", groupList
		
		newDir = "{0}/{1}/{2}".format(self.parent.homeDir, refDir, saniTopPage)
		
		if not os.path.isdir(newDir):
			os.makedirs(newDir)
		os.chdir(newDir)
		
		dictHtml = {}
		for i in groupList:
			# print "i", i
			url = "https://en.wikipedia.org/w/index.php?title={0}".format(urllib.request.quote(i))
			# print 'url', url
			
			partSoup = self.getHtmlSoup(url, 'group')
			# print 'soup', str(soup)
			# print "Downloading Images"
			for img in partSoup.findAll('img'):
				fName = img.attrs['src'].split('/')[-1]
				dlName = "http:{0}".format(img.attrs['src'])
				if not os.path.isfile(fName):
					os.system("wget -q {0}".format(dlName))
				img.attrs['src'] = "{0}/{1}".format(saniTopPage, fName)
			# print "img.src", img.attrs['src']
			# print "soup.img", partSoup.img
			# print "partSoup", partSoup
			dictHtml[i] = partSoup
		# print "dictEntry", dictHtml['Classical mechanics']
		
		os.chdir(self.parent.homeDir)
		# print 'dictHtml', dictHtml
		
		sql = "SELECT * FROM `TESTdb`.`data_groups` WHERE `groupName` = '{0}'".format(topPage)
		row = self.parent.database.dbReturnF1(sql)
		if not row:
			sql = "INSERT INTO `TESTdb`.`data_groups` (`groupName`, `groupContents`, `groupHtml`) VALUES (%s, %s, %s)"
			args = [topPage, groupList, dictHtml]
			self.parent.database.dbExecute(sql, args)
		else:
			result = fedit([('Overwrite Entry?', False)], 'Entry Exists',
						   'I have found an entry already...would you like to')
			if result[0] == True:
				sql = "UPDATE `TESTdb`.`data_groups` SET `groupName`=%s, `groupContents`=%s, `groupHtml`=%s"
				args = [topPage, groupList, dictHtml]
				# print 'last part', dictHtml['Classical mechanics']
				self.parent.database.dbExecute(sql, args)
		
		self.groupFinished.emit()
		
		pass
	
	def wikiInfoboxGet(self, searchterm):
		
		url = "http://en.wikipedia.org/w/index.php?title={0}".format(urllib.request.quote(searchterm))
		soup = self.getHtmlSoup(url, 'infobox')
		for i in soup.findAll('table'):
			i.attrs['border'] = '1'
			i.attrs['align'] = 'center'
		if soup.find("table", attrs={'class': 'infobox'}):
			content = soup.find("table", attrs={"class": "infobox"})
			
			# print 'content =', unicode(content)
			self.infoboxFinished.emit(str(content))
		
		else:
			self.infoboxNotExist.emit(['Infobox Not Exist Error', 'There was no infobox found on this page.'])
	
	def wikiFormulaGet(self, searchterm):
		
		flist = []
		ilist = []
		content = []
		check = " ,.\\"
		fronta = "\\ ,-+^'(_=>"
		frontb = ["cr", "{B", "(b", "ds", "|x", "(e", "({", ]
		
		try:
			# opener = urllib2.build_opener()
			# opener.addheaders = [("User-agent", "Mozilla/5.0")]
			url = "http://en.wikipedia.org/w/index.php?title={0}".format(urllib.request.quote(searchterm))
			# print "url = " + url
			page = self.parent.opener.open(url).read()
			soup = BeautifulSoup(page, 'lxml')
			alt = soup.findAll("img", {"class": "mwe-math-fallback-image-inline"})
			for i in alt: flist.append(str(i["alt"]))
			src = soup.findAll("img", {"class": "mwe-math-fallback-image-inline"})
			for i in src: ilist.append(str(i["src"]))
			# for i in flist: print "flist = " + i
			# for i in ilist: print "ilist = " + i
			
			data = [list(i) for i in zip(flist, ilist)]
			# print data
			
			for i in data:
				stuff = i
				# print "*" + stuff[0]#.replace(" ", "_").replace("\n", "#")
				stuff[0] = stuff[0].replace("\n", "")
				stuff[1] = str(stuff[1].replace("svg", "png"))
				
				while stuff[0][0] in check: stuff[0] = stuff[0][1:]
				
				while stuff[0][-1] in check: stuff[0] = stuff[0][:-1]
				
				# print "stuff[0][0:2] = " + stuff[0][0:2].replace(" ", "#")
				
				if len(stuff[0]) <= 1:
					pass
				
				elif stuff[0][1] not in fronta and stuff[0][0:2] not in frontb:
					stuff[0] = "\\" + stuff[0]
				
				# print "\033[91m {}\033[00m".format(str(i[0])) + "\n"
				content.append(str(i))
			
			dbprint("\nDOWNLOADING")
			# print "list text =", content
			os.chdir(self.parent.homeDir + "/temp/latex")
			# print "cwd =", os.getcwd()
			os.system("rm *.png")
			
			for i in content:
				i = literal_eval(i)
				os.system("wget -q '{0}' -O '{1}.png'".format(i[1], i[1].split("/")[-1]))
			
			self.formulaFinished.emit(content)
		
		
		except HTTPError:
			
			self.searchHTTPError.emit(['HTTP Error', '404 Page not found.'])
		
		except URLError:
			
			self.searchURLError.emit(['URL Error', 'Could not find the internet.'])
	
	# Make this work with webkit2png todo
	def wikiPeriodicUpdateGet(self):
		
		periodicTable = {}
		pList = ['Hydrogen', 'Helium', 'Lithium', 'Beryllium', 'Boron', 'Carbon', 'Nitrogen', 'Oxygen', 'Fluorine',
				 'Neon', 'Sodium', 'Magnesium', 'Aluminium', 'Silicon', 'Phosphorus', 'Sulfur', 'Chlorine', 'Argon',
				 'Potassium', 'Calcium', 'Scandium', 'Titanium', 'Vanadium', 'Chromium', 'Manganese', 'Iron', 'Cobalt',
				 'Nickel', 'Copper', 'Zinc', 'Gallium', 'Germanium', 'Arsenic', 'Selenium', 'Bromine', 'Krypton',
				 'Rubidium', 'Strontium', 'Yttrium', 'Zirconium', 'Niobium', 'Molybdenum', 'Technetium', 'Ruthenium',
				 'Rhodium', 'Palladium', 'Silver', 'Cadmium', 'Indium', 'Tin', 'Antimony', 'Tellurium', 'Iodine',
				 'Xenon', 'Caesium', 'Barium', 'Lanthanum', 'Cerium', 'Praseodymium', 'Neodymium', 'Promethium',
				 'Samarium', 'Europium', 'Gadolinium', 'Terbium', 'Dysprosium', 'Holmium', 'Erbium', 'Thulium',
				 'Ytterbium', 'Lutetium', 'Hafnium', 'Tantalum', 'Tungsten', 'Rhenium', 'Osmium', 'Iridium', 'Platinum',
				 'Gold', 'Mercury_(element)', 'Thallium', 'Lead', 'Bismuth', 'Polonium', 'Astatine', 'Radon',
				 'Francium', 'Radium', 'Actinium', 'Thorium', 'Protactinium', 'Uranium', 'Neptunium', 'Plutonium',
				 'Americium', 'Curium', 'Berkelium', 'Californium', 'Einsteinium', 'Fermium', 'Mendelevium', 'Nobelium',
				 'Lawrencium', 'Rutherfordium', 'Dubnium', 'Seaborgium', 'Bohrium', 'Hassium', 'Meitnerium',
				 'Darmstadtium', 'Roentgenium', 'Copernicium', 'Ununtrium', 'Flerovium', 'Ununpentium', 'Livermorium',
				 'Ununseptium', 'Ununoctium']
		
		for term in pList:
			# print "Mining {0}".format(term)
			url = "http://en.wikipedia.org/w/index.php?title={0}".format(term)
			
			try:
				page = self.parent.opener.open(url).read()
				# html = clean_html(page)
				soup = BeautifulSoup(page)
				info = soup.findAll('table', attrs={'class': 'infobox'})
				soup = BeautifulSoup(str(info))
				
				vape = "No Vapor Pressure Table"
				isos = "No Stable Isotopes Table"
				for i in soup.findAll('table', attrs={'class': 'wikitable'}):
					if "(K)" in i:
						vape = i.extract()
					
					elif 'half-life' in i:
						isos = i.extract()
					# print 'isos'
					else:
						i.extract()
				
				rows = []
				edict = {}
				cs = 1
				for row in soup.findAll('tr'):
					try:
						if row.th.text:
							if row.td.text:
								header = (row.th.text.replace(u'\u000A', u' '))
								data = (row.td.text.replace(u'\u000A', u' '))
								
								if header == u"Element category":
									data = data[2:]
								if header == " per shell ":
									header = 'Per shell'
								if header == "Crystal structure":
									if cs == 1:
										header = "Crystal structure I"
										cs = 2
										pass
									elif cs == 2:
										header = "Crystal structure II"
										cs = 1
								# print "these =", header, data
								rows.append(header)
								edict[header] = data
					except AttributeError:
						pass
				
				periodicTable[term] = [rows, edict, vape, isos]
				
				self.periodicFinished.emit()
			
			except HTTPError:
				
				self.searchHTTPError.emit(['HTTP Error', '404 Error\nPage Not Found.'])
			
			except URLError:
				
				self.searchURLError.emit(['URL Error', 'Can not find the internet.'])
		
		# output = open('periodicDict.txt', 'wb')
		# output.write(str(periodicTable))
		# output.close()
		
		sql = "UPDATE `TESTdb`.`JARVIS_searchDicts` SET `searchDict` = %s WHERE `searchName` LIKE 'periodicTable'"
		args = [periodicTable]
		self.parent.database.dbExecute(sql, args)
		pass