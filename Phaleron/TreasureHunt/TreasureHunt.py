#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
# from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtSvg import *
from PyQt6.QtSvgWidgets import *
from PyQt6.QtWidgets import *

from Callimachus.Database import Database
from Callimachus.imageProcessing import processImage
from Pharos.Dialogs import Dialogs

from bs4 import BeautifulSoup
from lxml import html as HTML
from ast import literal_eval
from urllib.request import build_opener
from urllib.error import HTTPError, URLError
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)
import pdfkit
import articleDateExtractor as ADE
# from webkit2png import WebkitRenderer

######################
# FIX DATABASE NAMES TODO
######################


# import PIL.ExifTags
# exif = {
#     PIL.ExifTags.TAGS[k]: v
#     for k, v in img._getexif().items()
#     if k in PIL.ExifTags.TAGS
# }

import sys, os, urllib, re
from Pharos.PtolFace import PtolFace
from Pharos.PGui import PMainWindow



class Research(QWidget):

	def __init__(self, parent=None):
		super(Research, self).__init__(parent)
		QWidget.__init__(self)

		
		self.Phaleron = parent.parentWidget()
		self.Ptolemy = self.Phaleron.Ptolemy
		print("RESEARCH: ", self.Phaleron, self.Ptolemy)

		self.sectionsCategories = {}
		sql = "SELECT * FROM `PTOLdb`.`data_sectionsCategories`"
		rows = self.Phaleron.database.dbReturnFA(sql)
		for row in rows:
			self.sectionsCategories[row[1]] = literal_eval(row[2])

		print(self.sectionsCategories)

		self.LIBRARYOPEN = 0
		self.WIKIVIEWOPEN = 0

		self.setStyleSheet(self.Phaleron.styles)
		self.setAutoFillBackground(True)

		from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
		QSett = QWebEngineProfile.defaultProfile().settings()
		QSett.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

		self.initUI()

	# Clean Up Objects TODO
	def __del__(self):

		pass

	def initUI(self):
		
		self.side = 23
		self.styles = "QPushButton { border: 1px solid cyan; background-color: cyan; color: black } " \
					  "QFrame {border: 1px solid cyan; background-color: cyan; color: cyan; } " \
					  "QRadioButton { background-color: black; color: white;} " \
					  "QRadioButton::label {align: right} " \
					  "QRadioButton::indicator{ border: 1px solid cyan; border-radius: 6px; color: cyan; background-color: black;} " \
					  "QRadioButton::indicator::checked{ border: 1px solid cyan; border-radius: 6px; color: black; background-color: cyan;} "

		# Tab Widget
		self.tabs = QTabWidget(parent=self)
		self.tabs.setDocumentMode(True)
		self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
		self.tabs.currentChanged.connect(self.current_tab_changed)
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_current_tab)

		self.Phaleron.setCentralWidget(self.tabs)

		# SSL Icon
		self.httpsicon = QSvgWidget(self.Phaleron.imgDir + 'lock-nossl.svg')
		self.httpsicon.setStyleSheet(self.styles)
		self.httpsicon.setFixedSize(self.side, self.side)

		# Navigation Buttons
		self.backBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'back.svg'), "", parent=self)
		self.backBtn.setStyleSheet(self.styles)
		self.backBtn.setToolTip('Back Page')
		self.backBtn.setFixedSize(self.side, self.side)
		self.backBtn.clicked.connect(lambda: self.tabs.currentWidget().back())

		self.forwardBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'forward.svg'), '', parent=self)
		self.forwardBtn.setStyleSheet(self.styles)
		self.forwardBtn.setToolTip('Forward Page')
		self.forwardBtn.setFixedSize(self.side, self.side)
		self.forwardBtn.clicked.connect(lambda: self.tabs.currentWidget().forward())

		self.reloadBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'reload.svg'), '', parent=self)
		self.reloadBtn.setStyleSheet(self.styles)
		self.reloadBtn.setToolTip('Reload Page')
		self.reloadBtn.setFixedSize(self.side, self.side)
		self.reloadBtn.clicked.connect(lambda: self.tabs.currentWidget().reload())

		self.stopBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'stop.svg'), '', parent=self)
		self.stopBtn.setStyleSheet(self.styles)
		self.stopBtn.setToolTip('Stop Page Loading')
		self.stopBtn.setFixedSize(self.side, self.side)
		self.stopBtn.clicked.connect(lambda: self.tabs.currentWidget().stop())

		self.newTabBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'newtab.svg'), '', parent=self)
		self.newTabBtn.setStyleSheet(self.styles)
		self.newTabBtn.setToolTip('New Tab')
		self.newTabBtn.setFixedSize(self.side, self.side)
		self.newTabBtn.clicked.connect(lambda _: self.add_new_tab())

		self.urlEdit = QLineEdit(parent=self)
		self.urlEdit.setFixedHeight(self.side)
		self.urlEdit.returnPressed.connect(self.navigate_to_url)

		# Apps

		self.notepadBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'notepad.svg'), '', parent=self)
		self.notepadBtn.setStyleSheet(self.styles)
		self.notepadBtn.setToolTip('Open Notepad App')
		self.notepadBtn.setFixedSize(self.side, self.side)
		if self.Ptolemy:
			self.notepadBtn.clicked.connect(self.Ptolemy.openNotepad)
		else:
			self.notepadBtn.clicked.connect(self.Phaleron.dialogs.addNoteBox)

		self.archiveSeparator = QFrame(parent=self)
		self.archiveSeparator.setStyleSheet(self.styles)
		self.archiveSeparator.setFrameShape(QFrame.VLine)
		self.archiveSeparator.setFrameShadow(QFrame.Sunken)

		self.archiveRadio = QRadioButton('As Text', parent=self)
		self.archiveRadio.setStyleSheet(self.styles)
		self.archiveRadio.setToolTip('Archive as Text instead of HTML')
		self.archiveRadio.setFixedSize(85, self.side)


		self.newSectionBtn = QPushButton(QIcon(self.Phaleron.imgDir + "newtab.svg"), '', parent=self)
		self.newSectionBtn.setStyleSheet(self.styles)
		self.newSectionBtn.setFixedSize(self.side, self.side)
		self.newSectionBtn.setToolTip('Add New Section with Categories')
		self.newSectionBtn.clicked.connect(self.Phaleron.dialogs.addSectionBox)

		self.sectionBox = QComboBox(parent=self)
		self.sectionBox.setStyleSheet(self.Phaleron.styles)
		self.sectionBox.addItem('SECTION')
		for i in self.sectionsCategories:
			self.sectionBox.addItem(i)
		self.sectionBox.currentTextChanged.connect(lambda text: self.sectionChanged(self.sectionBox.currentText()))

		self.newCategoryBtn = QPushButton(QIcon(self.Phaleron.imgDir + "newtab.svg"), '', parent=self)
		self.newCategoryBtn.setStyleSheet(self.styles)
		self.newCategoryBtn.setFixedSize(self.side, self.side)
		self.newCategoryBtn.setToolTip('Add new Category to existing Section')
		self.newCategoryBtn.clicked.connect(self.Phaleron.dialogs.addCategoryBox)

		self.categoryBox = QComboBox(parent=self)
		self.categoryBox.setStyleSheet(self.Phaleron.styles)
		self.categoryBox.addItem('CATEGORY')

		self.archiveBtn = QPushButton(QIcon(self.Phaleron.imgDir + 'archive.svg'), '', parent=self)
		self.archiveBtn.setStyleSheet(self.styles)
		self.archiveBtn.setToolTip('Archive to Database')
		self.archiveBtn.setFixedSize(self.side, self.side)
		self.archiveBtn.clicked.connect(lambda _: self.archive(self.urlEdit.text()))


		# Layout
		self.layout = QGridLayout(self)
		self.layout.addWidget(self.backBtn, 0, 1, 1, 1)
		self.layout.addWidget(self.forwardBtn, 0, 2, 1, 1)
		self.layout.addWidget(self.reloadBtn, 0, 3, 1, 1)
		self.layout.addWidget(self.stopBtn, 0, 4, 1, 1)
		self.layout.addWidget(self.httpsicon, 0, 5, 1, 1)
		self.layout.addWidget(self.urlEdit, 0, 6, 1, 7)
		self.layout.addWidget(self.newTabBtn, 0, 13, 1, 1)
		self.layout.addWidget(self.notepadBtn, 1, 1, 1, 1)
		self.layout.addWidget(self.archiveSeparator, 1, 7, 1, 1)
		self.layout.addWidget(self.archiveRadio, 1, 8, 1, 1)
		self.layout.addWidget(self.newSectionBtn, 1, 9, 1, 1)
		self.layout.addWidget(self.sectionBox, 1, 10, 1, 1)
		self.layout.addWidget(self.newCategoryBtn, 1, 11, 1, 1)
		self.layout.addWidget(self.categoryBox, 1, 12, 1, 1)
		self.layout.addWidget(self.archiveBtn, 1, 13, 1, 1)
		self.setLayout(self.layout)

		self.add_new_tab('http://www.google.com', 'Start Page')

	def add_new_tab(self, url=None, label="Blank"):

		if url is None:
			url = QUrl('')

		browser = QWebEngineView(parent=self)
		browser.setUrl(QUrl(url))
		i = self.tabs.addTab(browser, label)

		self.tabs.setCurrentIndex(i)

		browser.urlChanged.connect(lambda url, browser=browser:
								   self.update_urlbar(url, browser))

		browser.loadFinished.connect(lambda _, i=i, browser=browser:
									 self.tabs.setTabText(i, browser.page().title()))

		# Every page that loads feeds the Monad — no queue, no archive step.
		# toPlainText is async; the callback fires when Qt has the text ready.
		browser.loadFinished.connect(lambda ok, browser=browser:
									 browser.page().toPlainText(self._enqueue_page_text)
									 if ok else None)

	def _enqueue_page_text(self, text: str):
		"""Feed page plain-text to the Monad. Called async by toPlainText()."""
		if not text or len(text.strip()) < 20:
			return
		learner = getattr(self.Ptolemy, 'monad_learner', None)
		if learner is not None:
			learner.enqueue(text)

	def tab_open_doubleclick(self, i):
		if i == -1:  # No tab under the click
			self.add_new_tab()

	def current_tab_changed(self, i):
		try:
			qurl = self.tabs.currentWidget().url()
			self.update_urlbar(qurl, self.tabs.currentWidget())
			# self.update_title(self.tabs.currentWidget())

		except AttributeError:
			pass

	def close_current_tab(self, i):
		if self.tabs.count() < 2:
			return

		self.tabs.removeTab(i)

	def update_title(self, browser):
		if browser != self.tabs.currentWidget():
			# If this signal is not from the current tab, ignore
			return

		title = self.tabs.currentWidget().page().title()
		print('title : ' + title)
		self.Phaleron.setWindowTitle("Phaleron - {0}".format(title))

	def navigate_to_url(self):  # Does not receive the Url
		q = QUrl(self.urlEdit.text())
		if q.scheme() == "":
			q.setScheme("http")

		self.tabs.currentWidget().setUrl(q)

	def update_urlbar(self, q, browser=None):

		if browser != self.tabs.currentWidget():
			# If this signal is not from the current tab, ignore
			return

		if q.scheme() == 'https':
			# Secure padlock icon
			# self.httpsicon.setIcon(QIcon(self.Phaleron.imgDir + 'lock-ssl.svg'))
			self.httpsicon.load(self.Phaleron.imgDir + 'lock-ssl.svg')

		else:
			# Insecure padlock icon
			# self.httpsicon.setIcon(QIcon(self.Phaleron.imgDir + 'lock-nossl.svg'))
			self.httpsicon.load(self.Phaleron.imgDir + 'lock-nossl.svg')

		self.urlEdit.setText(q.toString())
		self.urlEdit.setCursorPosition(0)

	def sectionChanged(self, section):

		print(section)
		self.categoryBox.clear()
		self.categoryBox.addItem("CATEGORY")
		if section != "SECTION":
			self.categoryBox.addItems(self.sectionsCategories[section])


		pass

	# Threads
	def archive(self, url):

		self.articleArchive = ResearchThread(self, 1, url)
		self.articleArchive.archiveFinished.connect(self.Phaleron.dialogs.infoBox)
		self.articleArchive.researchHTTPError.connect(self.Phaleron.dialogs.infoBox)
		self.articleArchive.researchURLError.connect(self.Phaleron.dialogs.infoBox)
		self.articleArchive.archiveInvalidSelection.connect(self.Phaleron.dialogs.infoBox)
		self.articleArchive.researchDBError.connect(self.Phaleron.dialogs.infoBox)
		self.articleArchive.start()

		pass

	def updateWikiGroup(self):

		dataList = [('Category Name', '')]
		title = "Choose Page"
		comment = "Input Group Top Page"
		print(title, comment)
		results = fedit(dataList, title, comment)
		print(results)

		if results == None:

			pass

		else:
			self.groupGet = ResearchThread(self, 2, results[0])
			self.groupGet.groupFinished.connect(self.wikiGroupView)
			self.groupGet.researchHTTPError.connect(self.Phaleron.dialogs.infoBox)
			self.groupGet.researchURLError.connect(self.Phaleron.dialogs.infoBox)
			self.groupGet.start()

		pass
	
	# FIX THIS TO GET TEXT FROM DOCUMENT TODO
	def addWikiArticle(self):#, html):

		html = self.searchText.toHtml()
		# print "html =", self.html
		nextId = None
		articleImageList = []
		articleAudioList = None
		articleVideoList = None
		articlePdfList = None
		articleFileList = None
		articleUrl = str(html).split('\n', 1)[0]
		# print 'articleUrl =', articleUrl
		self.html = str(html).replace("{0}\n".format(articleUrl), "")
		infile = self.opener.open(articleUrl)
		# print 'infile =', infile
		page = infile.read()
		soup = BeautifulSoup(page)
		title = (str(soup.title).replace("<title>", "").replace("</title>", "").replace(",", "")).split(" ")
		articleSection = title[2]
		articleCategory = title[0]
		articleTitle = " ".join(title)
		soup = BeautifulSoup(self.html)
		imgs = soup.findAll('img')
		imgList = [i.get('src') for i in imgs]
		for i in imgList:
			localFilePath = self.database.upImages(i, articleSection, articleCategory)
			self.html = self.html.replace(i, localFilePath)
			articleImageList.append(localFilePath)
		articleText = str(self.html)#.encode('unicode_escape').decode('ascii', 'ignore')

		sql = "INSERT INTO `TESTdb`.`data_articles` (`id`, `articleUrl`, `articleTitle`, `articleSection`, `articleCategory`, `articleText`, `articleImageList`, `articleAudioList`, `articleVideoList`, `articlePdfList`, `articleFileList`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		args = [nextId, articleUrl, articleTitle, articleSection, articleCategory, articleText, str(articleImageList), articleAudioList, articleVideoList, articlePdfList, articleFileList]
		# print "sql =\n{0}\nargs =\n{1}".format(sql, args)
		self.parent.database.dbExecute(sql, args)
		print("\nARTICLE UPLOADED")

		pass

class ResearchThread(QThread):

	# Signals

	archiveFinished = pyqtSignal(list)
	researchHTTPError = pyqtSignal(list)
	researchURLError = pyqtSignal(list)
	archiveInvalidSelection = pyqtSignal(list)
	researchDBError = pyqtSignal(list)
	groupFinished = pyqtSignal(list)


	def __init__(self, parent, stype, *args):
		super(ResearchThread, self).__init__(parent)
		QThread.__init__(self)

		self.Research = parent
		self.Phaleron = parent.parentWidget().parentWidget()
		print("RESEARCH PARENTS: ", self.Phaleron, self.Research)
		
		self.opener = self.Phaleron.opener

		self.stype = stype
		self.args = []
		for arg in args:
			self.args.append(arg)

	def run(self):

		if self.stype == 1:
			self.archiveArticle(self.args[0])

		if self.stype == 2:
			self.wikiGroupGet(self.args[0])

		pass

	# Pull audio/video/docs and change audio/video/docs links todo
	# Add html2text function todo
	def archiveArticle(self, url):

		# articleName 	articleUrl 	articleDate 	articleText 	articleSection 	articleCategory 	articleArchiveDate
		imageLinks = []
		self.domain = url[8:].split("/")[0]
		self.articleSection = self.Research.sectionBox.currentText()
		self.articleCategory = self.Research.categoryBox.currentText()
		self.textChecked = self.Research.archiveRadio.isChecked()
		self.articleName = self.Research.tabs.currentWidget().page().title()
		self.articleUrl = url
		print(self.articleUrl)

		if self.articleSection == "SECTION" or self.articleCategory == "CATEGORY":
			self.archiveInvalidSelection.emit(['Invalid Selection', 'You must select a Section AND Category'])
			return
		
		
		try:
			file = self.opener.open(url)
			page = file.read().decode()
			print('Page Downloaded')

			# Feed plain text to the Monad immediately — the Monad is the memory.
			# BeautifulSoup strips tags; separator=' ' keeps word boundaries intact.
			try:
				_soup = BeautifulSoup(page, 'html.parser')
				_plain = _soup.get_text(separator=' ', strip=True)
				_learner = getattr(getattr(self.Research, 'Ptolemy', None),
								   'monad_learner', None)
				if _learner and _plain:
					_learner.enqueue(_plain)
			except Exception:
				pass

		except HTTPError:
			self.researchHTTPError.emit(['HTTP Error', '404 Error\nPage Not Found.'])

		except URLError:
			self.researchURLError.emit(['URL Error', 'Can not find the internet'])

		try:
			self.articleDate = ADE.extractArticlePublishedDate('', html=page).date()

		except AttributeError:
			self.articleDate = "No Article Date"

		print("ARTICLE DATE:", self.articleDate)
		# self.articleText = page.encode()


		# Gather Images
		self.root = HTML.fromstring(page)
		images = self.root.findall(".//img[@src]")
		for i in images:

			# Figure out how to separate wiki stuff todo
			if 'math/render' in i.attrib['src']:
				imageLinks.append(i.attrib['src'])

			elif i.attrib['src'][-4] != ".":
				pass

			elif i.attrib['src'].startswith('http'):
				imageLinks.append(i.attrib['src'])

			elif i.attrib['src'].startswith("//"):
				imageLinks.append('http:' + i.attrib['src'])

			else:
				pass
			
		# # Download Images
		# os.chdir(self.Phaleron.mediaDir + "images/")
		# if not os.path.isdir(self.domain):
		# 	os.mkdir(self.domain)
		# os.chdir(self.domain)
		#
		#
		# for i in imageLinks:
		# 	fileName = i[8:].split("/")[-1]
		# 	if os.path.isfile(fileName):
		#
		# 		pass
		#
		# 	else:
		# 		os.system('wget -q -O {0} {1}'.format(fileName, i))
		#
		# 		if 'wikipedia' in self.domain:
		# 			if 'math/render/' in i:
		# 				os.system('cp {0} {0}.svg'.format(fileName))

		# Replace Image Links
		html = page
		print("HTML TYPE:", type(html))

		for i in imageLinks:
			IP = processImage()
			
			self.findThis = i
			# print("FINDTHIS: ", self.findThis)
			self.conversion = IP.image2text(self.findThis)
			# print("CONVERSION: ", self.conversion)
			self.fileName = self.conversion[0]
			self.fileType = self.conversion[1]
			self.withThis = self.conversion[2]
			
			
			if 'wikipedia' in self.domain:
				if 'math/render/svg' in i:
					self.fileType = 'svg'
					shortBlock = html[:html.find(i)]
					# print("SHORTBLOCK: ", shortBlock)
					self.imageStartTag = shortBlock.rfind('<img')
					# print("STARTTAG: ", self.imageStartTag)
					self.imageEndTag = html.find('/>', self.imageStartTag) + 2
					# print("ENDTAG: ", self.imageEndTag)
					self.findThis = html[self.imageStartTag: self.imageEndTag]
					# print("SVG STUFF: ", self.findThis)
					
				sourceSet = re.findall(r'srcset=".*?"', html, re.DOTALL)
				for i in sourceSet:
					html = html.replace(i, "")
					
			# print("LENGTHS: ", len(self.findThis), " : ", len(self.withThis))
			print("*FINDTHIS: ", self.findThis, "\n*WITHTHIS: ", self.withThis)
			if self.fileType == 'svg':
				html = html.replace(self.findThis, self.withThis)
			else:
				html = html.replace(self.findThis[self.findThis.find('/'):], self.withThis)
			# print("AFTER HTML:", html)
			
		# for i in images:
		# 	findThis = i.attrib['src']
		# 	fileName = findThis.split("/")[-1]
		#
		# 	if 'wikipedia' in self.domain:
		# 		if fileName[-4] != "." and not fileName.endswith('.jpeg'):
		# 			fileName = fileName + ".svg"
		# 			findThis = i
		# 			withThis = IP.image2text()
		#
		# 		sourceSet = re.findall(r'srcset=".*?"', html, re.DOTALL)
		# 		for i in sourceSet:
		# 			html = html.replace(i, "")
		#
		# 	# withThis = PTOL_ROOT + '/media/images/' + str(self.domain) + "/" + str(fileName)
		# 	withThis = IP.image
		# 	html = html.replace(findThis, withThis)
		self.articleText = html.encode()
		title = self.Research.tabs.currentWidget().page().title().replace(" ", "") + ".html"
		

		# articleName 	articleUrl 	articleDate 	articleText 	articleSection 	articleCategory 	articleArchiveDate

		sql = "INSERT INTO `PTOLdb`.`data_articles` (`id`, `articleName`, `articleUrl`, `articleDate`, `articleText`, `articleSection`, `articleCategory`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
		args = [None, self.articleName, self.articleUrl, self.articleDate, self.articleText, self.articleSection, self.articleCategory]

		# try:
		# 	self.Phaleron.database.dbExecute(sql, args)
		#
		# except UnicodeEncodeError:
		#
		# 	self.researchDBError.emit(['Database UnicodeEncodeError', 'Article NOT Archived'])

		os.chdir(self.Phaleron.mediaDir + "docs/")
		if not os.path.isdir(self.domain):
			os.mkdir(self.domain)
		os.chdir(self.domain)
		print(os.getcwd())

		newFile = open(title, 'w+')
		newFile.write(str(html))
		newFile.close()

		os.chdir(self.Phaleron.homeDir)

		self.archiveFinished.emit(['Archiving Finished', 'The article has been archived'])





		pass

	# Convert to PDFs todo
	def wikiGroupGet(self, topPage):

		self.groupDir = self.Phaleron.mediaDir + "docs/wikiGroupPdfs/"
		self.url = "https://en.wikipedia.org/wiki/{0}".format(urllib.request.quote(topPage))
		self.navboxLinks = [self.url]
		self.finalLinks = []


		page = self.Phaleron.opener.open(self.url).read()

		self.root = HTML.fromstring(page)
		self.links = self.root.findall(".//table[@class='vertical-navbox nowraplinks']//a[@href]")
		for link in self.links:
			if link.attrib['href'].startswith('/wiki/'):
				self.navboxLinks.append('http://en.wikipedia.org' + link.attrib['href'])
		
		# try:
		self.links2 = self.root.findall(".//div[@class='NavFrame collapsed']//a[@href]")
		for link in self.links2:
			if link.attrib['href'].startswith('/wiki/'):
				if 'http://en.wikipedia.org' + link.attrib['href'] not in self.navboxLinks:
					self.navboxLinks.append('http://en.wikipedia.org' + link.attrib['href'])
		


		for link in self.navboxLinks:

			if "/Template_talk:" in link or '/Template:' in link or "/File:" in link or "/Book:" in link or '/Wikipedia:' in link:
				pass

			else:
				self.finalLinks.append(link)

		print(self.finalLinks)
		print(len(self.finalLinks))
		for i in self.finalLinks: print(i)

		os.chdir(self.groupDir)
		if not os.path.isdir(topPage):
			os.mkdir(topPage)
		os.chdir(self.groupDir + topPage)
		os.system('rm *')

		LINKNUMBER = 0
		finalLinksLength = len(self.finalLinks)
		for link in self.finalLinks:
			LINKNUMBER += 1
			self.title = str(LINKNUMBER) + "-" + urllib.request.unquote(link.split('/')[-1])

			try:
				_page = self.Phaleron.opener.open(link).read().decode('utf-8', errors='ignore')
				_soup = BeautifulSoup(_page, 'html.parser')
				_plain = _soup.get_text(separator=' ', strip=True)
				_learner = getattr(getattr(self.Research, 'Ptolemy', None), 'monad_learner', None)
				if _learner and _plain:
					_learner.enqueue(_plain)
			except Exception:
				pass

			pdfkit.from_url(link, self.title)

		self.groupFinished.emit(['Wikipedia Group Download Complete', topPage + " group has been downloaded"])

		pass

	def wikipediaArticle(self, url):

		try:
			page = self.Phaleron.opener.open(url).read().decode()

		except HTTPError:
			self.researchHTTPError.emit(['HTTP Error', '404 Error\nPage Not Found.'])

		except URLError:
			self.researchURLError.emit(['URL Error', 'Can not find the internet'])


		# Gather Images
		self.root = HTML.fromstring(page)
		images = self.root.findall(".//img[@src]")
		for i in images:

			if 'math/render' in i.attrib['src']:
				imageLinks.append(i.attrib['src'])

			elif i.attrib['src'][-4] != ".":
				pass

			elif i.attrib['src'].startswith("//"):
				imageLinks.append('http:' + i.attrib['src'])

			elif i.attrib['src'].startswith('http://'):
				imageLinks.append(i.attrib['src'])

			elif i.attrib['src'].startswith("https://"):
				imageLinks.append(i.attrib['src'])

			else:
				pass

		os.chdir(self.Phaleron.mediaDir + "images/")
		if not os.path.isdir(self.domain):
			os.mkdir(self.domain)
		os.chdir(self.domain)

		# Download Images
		for i in imageLinks:
			fileName = i[8:].split("/")[-1]
			if os.path.isfile(fileName):

				pass

			else:
				os.system('wget -q -O {0} {1}'.format(fileName, i))

				if 'math/render/' in i:
					os.system('cp {0} {0}.svg'.format(fileName))

		# Replace Image Links
		html = page

		for i in images:
			findThis = i.attrib['src']
			fileName = findThis.split("/")[-1]

			if fileName[-4] != ".":
				fileName = fileName + ".svg"

			sourceSet = re.findall(r'srcset=".*?"', html, re.DOTALL)
			for i in sourceSet:
				html = html.replace(i, "")

   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			withThis = PTOL_ROOT + '/media/images/' + str(self.domain) + "/" + str(fileName)

			html = html.replace(findThis, withThis)

		title = self.Research.tabs.currentWidget().page().title().replace(" ", "") + ".html"

		# articleName 	articleUrl 	articleDate 	articleText 	articleSection 	articleCategory 	articleArchiveDate

		newFile = open(title, 'w+')
		newFile.write(str(html))
		newFile.close()

		os.chdir(self.Phaleron.homeDir)

		pass

# FINISH FUNCTIONS TODO
class OCR(QWidget):

	def __init__(self, parent=None):
		dbprint('OCR.__init__')

		super(OCR, self).__init__(parent)
		QWidget.__init__(self)

		self.parent = parent.parentWidget()

		# self.setFixedSize(150, 150)
		self.setStyleSheet(self.parent.styles)
		
		self.initUI()
		
	def initUI(self):

		#Combo Box
		self.ocrType = QComboBox(self)#QTDESIGNER FOR COLORS TODO
		# self.ocrType.setFixedWidth(125)
		self.ocrType.setStyleSheet(self.parent.styles)
		self.ocrType.addItems(['Which Type?', 'Image', 'PDF'])

		#image Box
		self.ocrIn = QLineEdit(self)
		# self.ocrIn.setFixedWidth(125)
		self.ocrIn.setStyleSheet(self.parent.styles)
		self.ocrIn.setFocus()

		#Image File Dialog Button
		self.ocrFileBtn = QPushButton("Select File", self)
		# self.ocrFileBtn.setFixedWidth(125)
		self.ocrFileBtn.setStyleSheet(self.parent.styles)
		self.ocrFileBtn.clicked.connect(self.ocrFile)


		#image Button
		self.ocrGo = QPushButton('Process', self)
		# self.ocrGo.setFixedWidth(125)
		self.ocrGo.setStyleSheet(self.parent.styles)
		self.ocrGo.setToolTip('Perform Image Text Recognition')
		self.ocrGo.clicked.connect(self.ocrStart)

		#Layout
		self.layout = QGridLayout(self)
		self.layout.addWidget(self.ocrType, 0, 0, 1, 1)
		self.layout.addWidget(self.ocrIn, 1, 0, 1, 1)
		self.layout.addWidget(self.ocrFileBtn, 2, 0, 1, 1)
		self.layout.addWidget(self.ocrGo, 3, 0, 1, 1)
		self.setLayout(self.layout)

		
	def ocrFile(self):

		self.filePath = QFileDialog.getOpenFileName(self, 'Open File', '/home/rendier/Ptolemy')
		print(str(self.filePath))
		self.ocrIn.setText(self.filePath)

		pass

	# Enable Button ONLY with not default selected and file path added TODO
	def ocrStart(self):

		pass

class ThreadIndicator(QWidget):

	def __init__(self, count, parent=None):
		super(ThreadIndicator, self).__init__(parent)
		QWidget.__init__(self)

		self.layout = QGridLayout()

		self.layout.setMargin(0)
		self.label = QLabel()
		self.label.setStatusTip("Thread " + count + " Blue")
		self.label.resize(8, 8)

		# Make these with painter for actions todo
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.blue = QPixmap(PTOL_ROOT + "/images/Phaleron/blue-indicator.png")
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.green = QPixmap(PTOL_ROOT + "/images/Phaleron/green-indicator.png")
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.red = QPixmap(PTOL_ROOT + "/images/Phaleron/red-indicator.png")
		self.label.setPixmap(self.blue.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))
		self.layout.addWidget(self.label)
		self.setLayout(self.layout)
		# self.connect(self.label, QtCore.SIGNAL('indicatorChange(QString)'), self.indicatorChange)

	def indicatorChange(self, state):

		# print "INDICATOR CHANGE"
		# code = "self.label.setPixmap(self." + state + ".scaled(self.label.width(), self.label.height(), QtCore.Qt.KeepAspectRatio))"
		# print "change code", code
		# exec code
		pass

class TreasureHunt(PMainWindow, PtolFace):

	def __init__(self, parent=None):
		super(TreasureHunt, self).__init__(parent)
		PMainWindow.__init__(self)

		self.Ptolemy = parent
		print("TREASURE HUNT PARENT: ", self.Ptolemy)

		# self.setWindowTitle('Phaleron - Ptolemy')

		# Phaleron References
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.homeDir = PTOL_ROOT + '/'
		os.chdir(self.homeDir)
		self.win = self.frameGeometry()
		self.imgDir = self.homeDir + 'images/Phaleron/'
		self.tempDir = self.homeDir + 'temp/'
		self.mediaDir = self.homeDir + 'media/'
		self.flippingBookDir = self.homeDir + 'include/flipbookjs/'
		self.flipBooksDir = self.homeDir + 'include/flipbookjs/books/'
		self.setWindowTitle("Ptolemy")

		self.TABNUMBER = 0
		self.tabList = []

  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.setWindowIcon(QIcon(PTOL_ROOT + '/images/ptol.svg'))
		self.styles = "QMainWindow { border: 1px solid white; background-color: black; color: white } " \
					  "QWidget { background-color: black; color: white } " \
					  "QMenuBar { border: 1px solid white; background-color: black; color: white } " \
					  "QMenuBar::item { background-color: black; color: white } " \
					  "QToolBar { border: 1px solid white; background-color: black; color: white } " \
					  "QToolButton { background-color: black; color: white } " \
					  "QToolButton::hover { background-color: blue; color: white } " \
					  "QStatusBar { border: 1px solid white; background-color: black; color: white } " \
					  "QTabWidget { border: 1px solid white; background-color: black; color: white } " \
					  "QTabBar::tab { border: 1px solid white; background-color: black; color: white } " \
					  "QWebView { border: 1px solid white; background-color: white; color: black } " \
					  "QComboBox { border: 1px solid white; background-color: grey; color: black } " \
					  "QComboBox::item { background-color: grey; color: black } " \
					  "QPushButton { border: 1px solid white; background-color: black; color: white } " \
					  "QPushButton::hover {border: 1px solid blue } " \
					  "QLineEdit { border: 1px solid white; background-color: grey; color: black } " \
					  "QDockWidget { border: 1px solid white; background-color: black; color: white } " \
					  "QTableWidget { background-color: white; color: black } " \
					  "QTextBrowser { border: 1px solid black; background-color: white; color: black } " \
					  "QLabel {border: 0px } " \
					  "QListWidget { background-color: grey; color: black } " \
					  "QListWidgetItem { border: 1px solid black } " \
					  "QTableWidget { background-color: black; color: white } " \
					  "QTableWidget::item:focus { border: 1px solid white; background-color: blue; color: white } " \
					  "QHeaderView::section { background-color: darkblue; color: white }"
		self.setStyleSheet(self.styles)

		self.allowedTags = ['span', 'tr', 'html', 'th', 'sup', 'table', 'td', 'body']



		# Modules
		if self.Ptolemy:
			self.dialogs = self.Ptolemy.dialogs
			print(self.dialogs)
			self.database = self.Ptolemy.db
			self.opener = self.Ptolemy.opener
			print("Loaded Ptolemy Modules")

		else:
			self.dialogs = Dialogs(parent=self)
			self.database = Database(parent=self)
			self.opener = build_opener()
			self.opener.addheaders = [("User-agent", "Mozilla/5.0 (X11; Linux x86_64)"), ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"), ("Accept_encoding", "gzip, deflate, br"), ("Accept_language", "en-US,en;q=0.9"), ("Upgrade_insecure_requests", "1")]
			print("Loaded Phaleron Modules")


		# Flags
		self.TABNUMBER = 0
		self.SEARCHOPEN = 0
		self.OCROPEN = 0
		self.LIBRARYOPEN = 0
		self.RESEARCHOPEN = 0

		self.initUi()

	def initUi(self):

		#Main Widget
		self.widget = QWidget(self)
		self.widget.setStyleSheet(self.styles)

		#Status Bar
		self.status = QStatusBar(self)
		self.status.setStyleSheet(self.styles)
		
		self.setStatusBar(self.status)

		self.researchOpen()


	def resizeEvent(self, QResizeEvent):

		self.win = self.geometry()

		pass

	# FLESH THIS OUT TODO
	def closeEvent(self, QCloseEvent):

		#Temp Clearing
		clean = [
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			PTOL_ROOT + '/temp/harvest/article/',
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			PTOL_ROOT + '/temp/harvest/infobox/',
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			PTOL_ROOT + '/temp/latex/',
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			PTOL_ROOT + '/temp/ocr/'
		]
		for i in clean:
			os.chdir(i)
			os.system('rm *.*')
			os.chdir(self.homeDir)

		qApp.quit

	def createActions(self):
		#Actions
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.exitAction = QAction(QIcon(PTOL_ROOT + '/images/Phaleron/power.svg'), 'Exit', self)
		self.exitAction.setShortcut('Ctrl+X')
		self.exitAction.setStatusTip('Exit Application')
		self.exitAction.triggered.connect(self.closeEvent)

  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.searchAction = QAction(QIcon(PTOL_ROOT + '/images/Phaleron/search.svg'), 'Search', self)
		self.searchAction.setShortcut('Ctrl+S')
		self.searchAction.setStatusTip('Open Search Dock')
		self.searchAction.triggered.connect(self.searchOpen)

  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.ocrAction = QAction(QIcon(PTOL_ROOT + '/images/Phaleron/ocr.svg'), "OCR", self)
		self.ocrAction.setShortcut('Ctrl+R')
		self.ocrAction.setStatusTip('Optical Character Recognition')
		self.ocrAction.triggered.connect(self.ocrOpen)

  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.libraryAction = QAction(QIcon(PTOL_ROOT + '/images/Phaleron/library.svg'), 'Library', self)
		self.libraryAction.setShortcut('Ctrl+L')
		self.libraryAction.setStatusTip('Reference Library')
		self.libraryAction.triggered.connect(self.libraryOpen)

  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.researchAction = QAction(QIcon(PTOL_ROOT + '/images/Phaleron/research.svg'), 'Research', self)
		self.researchAction.setShortcut('Ctrl+A')
		self.researchAction.setStatusTip('Research Dock')
		self.researchAction.triggered.connect(self.researchOpen)

	def addTab(self, widget, searchText):
		self.TABNUMBER += 1
		self.tabs.addTab(widget, "{0} {1}".format(searchText, self.TABNUMBER))

	def hideShow(self):
		if self.isVisible():
			self.hide()
			self.trayIcon.menu.removeAction(self.trayIcon.hideAction)
			self.trayIcon.menu.addAction(self.trayIcon.showAction)


		else:
			self.show()

	def ocrOpen(self):

		if self.OCROPEN == 0:
			self.OCROPEN = 1

			self.ocrDock = QDockWidget("OCR Dock", self)
			self.ocrDock.setStyleSheet(self.styles)
			self.ocrDock.setAllowedAreas(Qt.LeftDockWidgetArea)
			# self.ocrDock.setFixedWidth(150)

			self.ocr = OCR(self.ocrDock)
			self.ocr.setStyleSheet(self.styles)
			self.ocrDock.setWidget(self.ocr)
			self.addDockWidget(Qt.LeftDockWidgetArea, self.ocrDock)

		elif self.OCROPEN == 1:
			self.OCROPEN = 0


			self.ocrDock.close()
			del self.ocr
			del self.ocrDock

	def researchOpen(self):

		if self.RESEARCHOPEN == 0:
			self.RESEARCHOPEN = 1

			self.researchDock = QDockWidget('Treasure Hunter', self)
			self.researchDock.setStyleSheet(self.styles)
			self.researchDock.setAllowedAreas(Qt.TopDockWidgetArea)
			# self.archiveDock.setFixedWidth(150)

			self.research = Research(self.researchDock)
			self.research.setStyleSheet(self.styles)
			self.researchDock.setWidget(self.research)
			self.addDockWidget(Qt.TopDockWidgetArea, self.researchDock)

		elif self.RESEARCHOPEN == 1:
			self.RESEARCHOPEN = 0

			self.researchDock.close()
			del self.research
			del self.researchDock


			


def main():

	app = QApplication(sys.argv)
	app.setApplicationName('Phaleron - Ptolemy')
	app.setFont(QFont('DejaVu Sans'))


	Phaleron = TreasureHunt()
	Phaleron.resize(int(QApplication.primaryScreen().geometry().width() * 0.8), int(QApplication.primaryScreen().geometry().height() * 0.8))
	Phaleron.setWindowTitle('Phaleron - Ptolemy')

	Phaleron.win = Phaleron.frameGeometry()
	Phaleron.show()

	# trayIcon = SystemTrayIcon(QIcon('images/ptol.svg'), parent=Phaleron)
	# trayIcon.show()

	# trayIcon = SystemTrayIcon(QIcon('images/ptol.svg'))
	# trayIcon.show()

	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
