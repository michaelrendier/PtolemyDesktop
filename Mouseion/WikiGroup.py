#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWidgets import QWidget, QGridLayout, QApplication, QComboBox, QListWidget, QListWidgetItem, QPushButton

import sys, os, re, pdfkit

# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)
from lxml import html as HTML
from urllib.request import build_opener, quote, unquote
from Pharos.Dialogs import Dialogs
from Pharos.PtolFace import PtolFace
from Pharos.PGui import PMainWindow

class WikiThread(QThread):
	groupFinished = pyqtSignal(list)
	researchHTTPError = pyqtSignal(list)
	researchURLError = pyqtSignal(list)
	
	def __init__(self, parent, stype, *args):
		super(WikiThread, self).__init__(parent)
		
		self.Wiki = parent
		self.Ptolemy = self.Wiki.parent()
		print("RESEARCH PARENTS: ", self.Wiki, self.Ptolemy)

		if self.Ptolemy:
			self.opener = self.Ptolemy.opener
			self.dialogs = self.Ptolemy.dialogs
		else:
			self.opener = build_opener()
			self.opener.addheaders = [("User-agent", "Mozilla/5.0 (X11; Linux x86_64)"), ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"), ("Accept_encoding", "gzip, deflate, br"), ("Accept_language", "en-US,en;q=0.9"), ("Upgrade_insecure_requests", "1")]
			self.dialogs = Dialogs()

		self.stype = stype
		self.args = []
		for arg in args:
			self.args.append(arg)
	
	def run(self):
		print("RUNNING")
		if self.stype == 1:
			self.wikiGroupGet(self.args[0])
		
		pass
	
	def wikiGroupGet(self, topPage):
		print("GETTING WIKI GROUP")
		self.groupDir = self.Wiki.groupDir#.mediaDir + "docs/wikiGroupPdfs/"
		print("GROUPDIR", self.groupDir)
		self.url = f"https://en.wikipedia.org/wiki/{quote(topPage)}"
		self.navboxLinks = [self.url]
		self.finalLinks = []
		print(f"Opening Page {self.url}")
		page = self.opener.open(self.url).read()
		
		self.root = HTML.fromstring(page)
		self.links = self.root.findall(".//table[@class='vertical-navbox nowraplinks plainlist']//a[@href]")
		for link in self.links:
			if link.attrib['href'].startswith('/wiki/'):
				self.navboxLinks.append('http://en.wikipedia.org' + link.attrib['href'])
		print("NaveboxLinks", self.navboxLinks)
		# try:
		# self.links2 = self.root.findall(".//div[@class='NavFrame collapsed']//a[@href]")
		# for link in self.links2:
		# 	if link.attrib['href'].startswith('/wiki/'):
		# 		if 'http://en.wikipedia.org' + link.attrib['href'] not in self.navboxLinks:
		# 			self.navboxLinks.append('http://en.wikipedia.org' + link.attrib['href'])
		
		for link in self.navboxLinks:
			
			if "/Template_talk:" in link or '/Template:' in link or "/File:" in link or "/Book:" in link or '/Wikipedia:' in link or '/Category:' in link or '/Portal:' in link:
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
		if os.listdir():
			os.system('rm *')
		
		LINKNUMBER = 0
		finalLinksLength = len(self.finalLinks)
		for link in self.finalLinks:
			LINKNUMBER += 1
			self.title = str(LINKNUMBER) + "-" + unquote(link.split('/')[-1])
			
			pdfkit.from_url(link, self.title)
		
		self.groupFinished.emit(['Wikipedia Group Download Complete', topPage + " group has been downloaded"])
		
		pass

class WikiGroup(PMainWindow, PtolFace):

	def __init__(self, parent=None):
		super(WikiGroup, self).__init__(parent)
		PMainWindow.__init__(self)

		self.Ptolemy = parent
		print("WIKIGROUP PARENT: ", self.Ptolemy)
		
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.setWindowIcon(QIcon(PTOL_ROOT + '/images/ptol.svg'))
		self.resize(int(QApplication.primaryScreen().geometry().width() * 0.8), int(QApplication.primaryScreen().geometry().height() * 0.8))
		self.setWindowTitle('Mouseion Wikipedia Books - Ptolemy')
		
		if self.Ptolemy:
			
			self.groupDir = self.Ptolemy.mediaDir + "docs/wikiGroupPdfs/"
			self.styles = self.Ptolemy.stylesheet
			self.setStyleSheet(self.styles)
			self.dialogs = self.Ptolemy.dialogs
			
		else:
			
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
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			self.groupDir = PTOL_ROOT + '/media/docs/wikiGroupPdfs/'
			self.setStyleSheet(self.styles)
			self.dialogs = Dialogs()
			

		self.initUi()

	# Add Update Wikipedia Groups Button todo
	def initUi(self):
		
		self.widget = QWidget(self)
		self.setCentralWidget(self.widget)

		self.layout = QGridLayout(self.widget)
		# self.layout.setMargin(0)

		self.list = QComboBox(self)
		# self.list.setMaximumWidth(300)
		self.list.activated.connect(lambda : self.loadGroupPdfs(self.list.currentText()))

		self.contents = QListWidget(parent=self)
		self.contents.setMaximumWidth(300)
		self.contents.itemDoubleClicked.connect(self.setWeb)

		self.updateBtn = QPushButton('Add or Update a Group')#QIcon(self.Phaleron.imgDir + "newtab.svg"), '', parent=self)
		self.updateBtn.setStyleSheet(self.styles)
		self.updateBtn.setToolTip('Add or Update a Wikipedia Group')
		# self.updateBtn.setFixedSize(self.list.height(), self.list.height())
		self.updateBtn.clicked.connect(self.updateGroup)

		self.loadGroupNames()


		from PyQt6.QtWebEngineCore import QWebEngineProfile
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
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.path = QUrl.fromLocalFile(PTOL_ROOT + "/media/docs/wikiGroupPdfs/") # Fix home directory thing TODO

		self.webView = QWebEngineView(parent=self)
		self.webView.setStyleSheet("QWebEngineView { background-color: grey; }")

		self.layout.addWidget(self.updateBtn, 10, 0, 1, 1)
		self.layout.addWidget(self.list, 0, 0, 1, 1)
		self.layout.addWidget(self.contents, 1, 0, 9, 1)
		self.layout.addWidget(self.webView, 0, 1, 11, 6)
		self.widget.setLayout(self.layout)

		pass

	def loadGroupNames(self):

		self.groupList = ['Choose Your Wiki Book']
		self.pdfList = []

		os.chdir(self.groupDir)


		dir = os.listdir()
		print("dir: ", dir)
		for i in dir:
			if "." not in i:
				self.groupList.append(i)
		print('groupList: ', self.groupList)

		for dir in self.groupList:
			self.list.addItem(dir)

		pass

	def loadGroupPdfs(self, group):

		if group == 'Choose Your Wiki Book':

			pass

		else:

			self.group = group
			self.fileList = {}
			os.chdir(self.groupDir + str(self.group))
			print("GROUP : " + os.getcwd())

			self.files = os.listdir()
			self.filesLength = len(self.files)
			# print(self.files.sort())

			for file in self.files:

				index = re.findall(r'\d+', file)

				self.fileList[int(index[0]) - 1] = file

			# print(self.fileList)
			self.finalFilesList = []
			for i in range(self.filesLength):
				self.finalFilesList.append(self.fileList[i])

			self.contents.clear()

			for i in self.finalFilesList:
				item = QListWidgetItem(str(i))
				self.contents.addItem(item)

	def setWeb(self, item):

		PDFJS = 'file:///home/rendier/Ptolemy/include/pdfjs/web/viewer.html'

		pageName = item.text()# + ".pdf"
		groupName = self.list.currentText()
		print(pageName)

		PDF = f'file:///home/rendier/Ptolemy/media/docs/wikiGroupPdfs/{groupName}/{pageName}'
		print("PDF : ", PDF)

		self.webView.load(QUrl.fromUserInput(f'{PDFJS}?file={PDF}'))

		pass

	def updateGroup(self):

		dataList = [('Category Name', '')]
		title = "Choose Page"
		comment = "Input Group Top Page"
		print("TITLE COMMENT", title, comment)
		results = fedit(dataList, title, comment, parent=self)
		print("RESULTS", results)
		
		if results == None:

			pass

		else:
			self.groupGet = WikiThread(self, 1, results[0])
			self.groupGet.groupFinished.connect(self.dialogs.infoBox)
			self.groupGet.researchHTTPError.connect(self.dialogs.infoBox)
			self.groupGet.researchURLError.connect(self.dialogs.infoBox)
			self.groupGet.start()

	def finished_group(self, text):
		print(f"FINISHED {text}")

		
def main():

	app = QApplication(sys.argv)
	app.setApplicationName('Mouseion Library - Ptolemy')
	app.setFont(QFont('DejaVu Sans'))


	Textbooks = WikiGroup()
	Textbooks.win = Textbooks.frameGeometry()
	Textbooks.show()

	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec())


if __name__ == "__main__":
	main()