#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWidgets import *

from PIL import Image
from urllib.request import build_opener
from urllib.error import HTTPError, URLError
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)

import sys, os, string, math, pdfkit
from Pharos.PtolFace import PtolFace
from Pharos.PGui import PMainWindow


# make listwidget into tree, add categories w/parents to db. TODO
class Library(PMainWindow, PtolFace):
	
	def __init__(self, parent=None):
		super(Library, self).__init__(parent)
		PMainWindow.__init__(self)
		
		self.Ptolemy = parent
		print("LIBRARY PARENTS: ", self.Ptolemy)
		
		self.ADMIN = 0
		
		self.superDict = {"0": u"\u2070", "1": u"\xb9", "2": u"\xb2", "3": u"\xb3", "4": u"\u2074", "5": u"\u2075",
						  "6": u"\u2076", "7": u"\u2077", "8": u"\u2078", "9": u"\u2079", "+": u"\u207A",
						  "-": u"\u207B", u'\u2212': u"\u207B", "=": u"\u207C", "(": u"\u207D", ")": u"\u207E",
						  "n": u"\u207F", u'[': u'\u207D', u']': u'\u207E', 'm': u'\u1d50'}
		# self.setFixedSize(150, 250)
		self.setAutoFillBackground(True)
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.setWindowIcon(QIcon(PTOL_ROOT + '/images/ptol.svg'))
		self.resize(int(QApplication.primaryScreen().geometry().width() * 0.8), int(QApplication.primaryScreen().geometry().height() * 0.8))
		self.setWindowTitle('Mouseion Library - Ptolemy')
		
		# print "stylesheet", self.styleSheet()
		self.fbPath = 'include/flipbookjs/books'
		
		if self.Ptolemy:
			self.database = self.Ptolemy.db
			self.dialogs = self.Ptolemy.dialogs
			self.homeDir = self.Ptolemy.homeDir
			self.styles = self.Ptolemy.stylesheet
			
		else:
			from Callimachus.Database import Database
			from Pharos.Dialogs import Dialogs
			self.database = Database(self)
			self.dialogs = Dialogs(self)
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			self.homeDir = PTOL_ROOT + "/"
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
		os.chdir(self.homeDir)
		self.win = self.frameGeometry()
		print("FRAME GEO: ", self.win)
		self.imgDir = self.homeDir + 'images/Musaeum/'
		self.tempDir = self.homeDir + 'temp/'
		self.mediaDir = self.homeDir + 'media/'
		self.flippingBookDir = self.homeDir + 'include/flipbookjs/'
		self.flipBooksDir = self.homeDir + 'include/flipbookjs/books/'
		
		self.TABNUMBER = 0
		self.SIDEBAR = 1
		
		self.initUI()
	
	# Clean Up Objects TODO
	def __del__(self):
		
		pass
	
	def initUI(self):
		
		self.Dock = QDockWidget('Mouseion Library', self)
		self.Dock.setStyleSheet(self.styles)
		self.Dock.setAllowedAreas(Qt.LeftDockWidgetArea)
		# self.Dock.closeEvent()
		
		self.widget = QWidget(self)
		# self.widget.setFixedWidth(250)
		self.Dock.setWidget(self.widget)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.Dock)
		
		self.tabs = QTabWidget(self)
		self.tabs.setStyleSheet("QTabWidget { width: 100%; height: 100% }")
		self.tabs.setDocumentMode(True)
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_current_tab)
		self.setCentralWidget(self.tabs)
		
		self.libraryLable = QLabel('Please choose from\nOur selection of books')
		self.libraryLable.setStyleSheet("QLabel { border: 1px solid white; }")
		self.libraryLable.setAlignment(Qt.AlignCenter)
		
		self.libraryList = QListWidget(self)
		self.libraryList.setFont(QFont('Monospace', 9))
		self.libraryList.setStyleSheet(self.styles)
		# self.libraryList.setFixedWidth(250)
		self.libraryList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.libraryList.itemDoubleClicked.connect(self.libraryDoubleClicked)
		
		self.libraryAdmin = QCheckBox('Admin')
		self.libraryAdmin.setStyleSheet('QCheckBox { border: 1px solid white; }')
		self.libraryAdmin.clicked.connect(self.adminShow)
		
		self.libraryHide = QCheckBox('Hide Sidebar')
		self.libraryHide.setStyleSheet('QCheckBox { border: 1px solid white; }')
		self.libraryHide.clicked.connect(self.hideSidebar)
		
		
		self.libraryPdfBtn = QPushButton('Add Pdf Book')
		self.libraryPdfBtn.setStyleSheet(self.styles)
		self.libraryPdfBtn.setToolTip('Add PDF to Flippingbook')
		self.libraryPdfBtn.clicked.connect(self.flipbookPdf)
		
		self.libraryImgBtn = QPushButton('Add Batch Images')
		self.libraryImgBtn.setStyleSheet(self.styles)
		self.libraryImgBtn.setToolTip('Add batch images to Flippingbook')
		self.libraryImgBtn.clicked.connect(self.flipbookBatch)
		
		self.libraryTxtBtn = QPushButton('Add Text File')
		self.libraryTxtBtn.setStyleSheet(self.styles)
		self.libraryTxtBtn.setToolTip('Add text file to Flippingbook')
		self.libraryTxtBtn.clicked.connect(self.flipbookText)
		
		self.libraryPatBtn = QPushButton('Add Patent')
		self.libraryPatBtn.setStyleSheet(self.styles)
		self.libraryPatBtn.setToolTip('Add Google Patent to Flippingbook')
		self.libraryPatBtn.clicked.connect(self.flipbookPatent)
		
		self.libraryRmBtn = QPushButton('Remove Book')
		self.libraryRmBtn.setStyleSheet(self.styles)
		self.libraryRmBtn.setToolTip('Remove book from Flippingbook')
		self.libraryRmBtn.clicked.connect(self.flipbookRemove)
		
		self.makeList()
		
		# Layout
		self.layout = QGridLayout(self.widget)
		self.layout.setHorizontalSpacing(0)
		self.layout.addWidget(self.libraryLable, 0, 0, 1, 2)
		self.layout.addWidget(self.libraryList, 1, 0, 12, 2)
		self.layout.addWidget(self.libraryAdmin, 12, 0, 1, 1)
		self.layout.addWidget(self.libraryHide, 12, 1, 1, 1)
		self.layout.addWidget(self.libraryPdfBtn, 13, 0, 1, 2)
		self.layout.addWidget(self.libraryImgBtn, 14, 0, 1, 2)
		self.layout.addWidget(self.libraryTxtBtn, 15, 0, 1, 2)
		self.layout.addWidget(self.libraryPatBtn, 16, 0, 1, 2)
		self.layout.addWidget(self.libraryRmBtn, 17, 0, 1, 2)
		self.setLayout(self.layout)
		
		self.libraryImgBtn.hide()
		self.libraryPatBtn.hide()
		self.libraryPdfBtn.hide()
		self.libraryRmBtn.hide()
		self.libraryTxtBtn.hide()
	
	def close_current_tab(self, i):
		if self.tabs.count() < 2:
			return

		self.tabs.removeTab(i)
	
	def hideSidebar(self, event):
		
		pass
	
	def makeList(self):
		# sql = "SELECT * FROM `TESTdb`.`data_books` ORDER BY `bookName` ASC"
		# args = []
		# rows = self.database.dbReturnFA(sql, args)
		#
		# self.libraryList.clear()
		# for book in rows:
		# 	self.libraryList.addItem(QListWidgetItem(book[1]))  # .lower().replace(" ", ""))) TODO
		
		bookList = []
		for i in os.listdir(self.flipBooksDir):
			bookList.append(i)
		# print("BOOKLIST: ", bookList)
		
		for book in sorted(bookList):
			self.libraryList.addItem(QListWidgetItem(book))
	
	def adminShow(self):
		
		if self.ADMIN == 0:
			self.ADMIN = 1
			
			self.libraryImgBtn.show()
			self.libraryPatBtn.show()
			self.libraryPdfBtn.show()
			self.libraryRmBtn.show()
			self.libraryTxtBtn.show()
		
		elif self.ADMIN == 1:
			self.ADMIN = 0
			
			self.libraryImgBtn.hide()
			self.libraryPatBtn.hide()
			self.libraryPdfBtn.hide()
			self.libraryRmBtn.hide()
			self.libraryTxtBtn.hide()
	
	def libraryDoubleClicked(self, item):
		
		self.book = FlippingBook(item.text(), parent=self)
		self.addTab(self.book, item.text())
		
		pass
	
	def addTab(self, widget, searchText):
		self.TABNUMBER += 1
		self.tabs.addTab(widget, "{0} {1}".format(searchText, self.TABNUMBER))
	
	def flipbookBatch(self, directory=None):
		
		# print "directory", str(directory)
		if directory == False:
			# print "None"
			bookImgs = QFileDialog.getExistingDirectory(self, "Select Image Directory",
														"{0}/{1}".format(self.homeDir, self.fbPath))
		else:
			# print "directory"
			bookImgs = directory
		
		self.batchEnter = LibraryThread(self.Research, 1, bookImgs)
		self.batchEnter.libraryBatchPublished.connect(self.dialogs.infoBox)
		self.batchEnter.libraryBatchMakeList.connect(self.makeList)
		self.batchEnter.start()
		
		pass
	
	# Fix pink floyd problem TODO
	# VERIFY DIRECTORY AND IMAGES BEFORE PROCESS PDF TODO
	def flipbookPdf(self):
		
		fPath = QFileDialog.getOpenFileNameAndFilter(self, 'Choose PDF File', self.homeDir, "PDF (*.pdf)")
		# print homeDir, "THIS ONE"
		# print "fpath[0]", fPath[0]
		
		self.pdfEnter = LibraryThread(self.Research, 2, fPath)
		self.pdfEnter.libraryBatchMakeList.connect(self.makeList)
		self.pdfEnter.libraryBatchPublished.connect(self.dialogs.infoBox)
		self.pdfEnter.start()
		
		pass
	
	def flipbookText(self):
		
		# SPLIT TEXT INTO 66 LINES TODO
		fPath = QFileDialog.getOpenFileNameAndFilter(self, 'Open Text File', self.homeDir, "TXT (*.txt)")
		# print "fPath", fPath[0]
		fileName = str(fPath[0].split("/")[-1].split(".")[0]).lower()
		# pre = fileName
		# print "filename", fileName
		
		self.textEnter = LibraryThread(self.Research, 3, fileName, fPath)
		self.textEnter.libraryBatchPublished.connect(self.dialogs.infoBox)
		self.textEnter.libraryBatchMakeList.connect(self.makeList)
		self.textEnter.start()
		
		pass
	
	def flipbookPatent(self):
		
		input, ok = QInputDialog.getText(self, 'Download and publish patent',
										 'Please enter name of patent\nthat you would like archived?')
		if ok:
			self.patentEnter = LibraryThread(self.Research, 4, input)
			self.patentEnter.libraryHTTPError.connect(self.dialogs.infoBox)
			self.patentEnter.libraryURLError.connect(self.dialogs.infoBox)
			self.patentEnter.libraryBatchMakeList.connect(self.makeList)
			self.patentEnter.libraryBatchPublished.connect(self.dialogs.infoBox)
			self.patentEnter.start()
		
		pass
	
	# TODO
	def flipbookRemove(self):
		
		book = self.libraryList.currentItem().text()
		pass


class LibraryThread(QThread):
	# Signals
	libraryHTTPError = pyqtSignal(list)
	libraryURLError = pyqtSignal(list)
	libraryFlipTextFinished = pyqtSignal()
	libraryPdfWrongFileType = pyqtSignal(list)
	libraryBatchMakeList = pyqtSignal()
	libraryBatchPublished = pyqtSignal(list)
	
	def __init__(self, parent, stype, *args):
		super(LibraryThread, self).__init__(parent)
		QThread.__init__(self)
		
		self.parent = parent
		self.stype = stype
		self.args = []
		for arg in args:
			self.args.append(arg)
		self.fbPath = 'include/flipbookjs/books'
	
	def __del__(self):
		
		pass
	
	def run(self):
		
		if self.stype == 1:
			self.flipbookBatch(self.args[0])
		
		elif self.stype == 2:
			self.flipbookPdf(self.args[0])
		
		elif self.stype == 3:
			self.flipbookText(self.args[0], self.args[1])
		
		elif self.stype == 4:
			self.flipbookPatent(self.args[0])
		
		pass
	
	def flipbookBatch(self, bookImgs):
		
		folder = bookImgs.split('/')[-1]
		# print bookImgs
		pages = []
		os.chdir(bookImgs)
		# fix home directory thing TODO
		for i in sorted(os.listdir(".")):
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			pages.append(PTOL_ROOT + "/include/flipbookjs/books/{0}/{1}".format(folder, i))
		# print pages
		img = Image.open(pages[0])
		# w, h = img.size
		w = float(img.size[0])
		h = float(img.size[1])
		# print 'img', w, h
		ratio = w / h  # FIX FOR LANDSCAPE TODO
		# print 'ratio', ratio
		bookHeight = round(400 / ratio)
		# print bookHeight
		
		os.chdir("../..")
		
		# Collect MYSQL errors here too TODO
		# SEARCH DB TO SEE IF ALREADY ADDED TODO
		sql = "INSERT INTO `TESTdb`.`data_books` (`id`, `bookName`, `bookImages`, `bookRatio`, `bookWidth`, `bookHeight`, `bookPath`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
		args = [None, folder, str(pages), ratio, "800", bookHeight, bookImgs]
		self.parent.database.dbExecute(sql, args)
		self.libraryBatchMakeList.emit()
		self.libraryBatchPublished.emit(['Task Completed', 'Book has been published.'])
		
		pass
	
	def flipbookPdf(self, fPath):
		
		fName = fPath[0].split("/")[-1]
		# print "fName", fName
		pre = str(fName.split('.')[0]).lower()
		# print pre
		prefix = ""
		for i in pre:
			if i in string.ascii_lowercase or string.digits:
				prefix = prefix + i
		# print "prefix", prefix
		directory = "{0}/{1}/{2}".format(self.parent.homeDir, self.fbPath, prefix)
		# print "directory", directory
		
		# Process Pdf
		if str(fName).lower().endswith(".pdf"):
			try:
				os.makedirs(directory)
				os.system("cp {0} {1}/".format(fPath[0], directory))
				os.chdir(directory)
				os.system("pdftoppm -jpeg {0} pages".format(fName))
				os.system("rm *.pdf")
				os.chdir(self.parent.homeDir)
				self.flipbookBatch(directory)
			
			except OSError:
				pass
		else:
			self.libraryPdfWrongFileType.emit(['Wrong File Type', 'Please choose a .pdf file.'])
	
	def flipbookText(self, fileName, fPath):
		
		prefix = ""
		for i in fileName:
			if i in string.ascii_lowercase:
				prefix = prefix + i
		# print "prefix", prefix
		fileText = open(str(fPath[0]), 'rb').read()
		fileLines = fileText.split(str("\n"))
		fileNum = int(math.ceil(len(fileLines) / float(66)))
		# print "fileNum", fileNum
		
		os.chdir("temp/flipbook")
		# print "After the change", os.getcwd()
		for i in range(fileNum):
			page = []
			num = "{:0>4d}".format(i)
			for i in range(66):
				try:
					page.append(fileLines.pop(0))
				except IndexError:
					break
			newFile = open("{0}-{1}.txt".format(prefix, num), 'wb')
			newFile.write(str("\n".join(page)))
			newFile.close()
			os.system("convert {0}-{1}.txt {0}-{1}.jpg".format(prefix, num))
		# FIX FOR IF BOOK ALREADY EXISTS TODO
		os.makedirs("{0}/{1}/{2}".format(self.parent.homeDir, self.fbPath, prefix))
		os.system("mv *.jpg {0}/{1}/{2}/".format(self.parent.homeDir, self.fbPath, prefix))
		os.system("rm *")
		self.flipbookBatch("{0}/{1}/{2}".format(self.parent.homeDir, self.fbPath, prefix))
		os.chdir(self.parent.homeDir)
		# print os.getcwd()
		self.libraryFlipTextFinished.emit()
		pass
	
	def flipbookPatent(self, title):
		
		try:
			url = "https://patentimages.storage.googleapis.com/pdfs/{0}.pdf".format(title)
   # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
			os.chdir(PTOL_ROOT + "/temp/flipbook/")
			os.system("wget -q " + url)
			fPath = os.getcwd() + "/" + title + '.pdf'
			# print "fPath BEFORE", [fPath]
			self.flipbookPdf([fPath])
		
		except HTTPError:
			print("Page Not Found")
			self.libraryHTTPError.emit(['HTTP Error', '404 Page not found.'])
		
		except URLError:
			print("No Connection Found")
			self.libraryURLError.emit(['URL Error', 'Could not find the internet.'])
		
		pass


# Move this to own script in Museaum todo
class FlippingBook(QWidget):
	
	def __init__(self, book, parent=None):
		super(FlippingBook, self).__init__(parent)
		QWidget.__init__(self)
		
		self.Library = parent
		print("FLIPPINGBOOK PARENT: ", self.Library)
		
		self.setAutoFillBackground(True)
		self.book = book
		self.bookPath = self.Library.flipBooksDir + self.book + "/"
		self.bookSize = (500, 735)
		self.tabsSize = self.Library.tabs.geometry()
		print("TABS GEO: ", self.tabsSize)
		# print("BOOK: " + self.book, self.bookPath)
		self.homeDir = self.Library.homeDir
		self.flippingBookDir = self.Library.flippingBookDir
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.path = QUrl.fromLocalFile(PTOL_ROOT + '/include/flipbookjs/')
		
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
		QSett.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
		QSett.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
		
		self.webView = QWebEngineView(parent=self)
		
		self.loadBook()
		
		self.layout = QGridLayout(self)
		self.layout.addWidget(self.webView, 0, 0, 10, 1)
		self.setLayout(self.layout)
	
	def loadBook(self):
		
		images = os.listdir(self.bookPath)
		if 'skeletoncss.css' in images: images.remove('skeletoncss.css')
		if 'skeletonindex.html' in images: images.remove('skeletonindex.html')
		
		# print("IMAGES: ", images)
		if len(images) % 2 != 0:
			os.chdir(self.flippingBookDir)
			# print('cp blankpage.jpg {0}'.format(self.bookPath.replace(' ', '\ ') + 'zzzzzzz.jpg'))
			os.system('cp blankpage.jpg {0}'.format(self.bookPath.replace(' ', '\ ') + 'zzzzzzz.jpg'))
			images.append("zzzzzzz.jpg")
		# print("IMAGES: ", sorted(images))
		
		pagesList = "<div class='hard' style='background-image:url(/home/rendier/Ptolemy/include/flipbookjs/front-cover.jpg)'></div>\n<div class='hard'></div>"
		for image in sorted(images):
			if image.endswith('.jpg'):
				pagesList = pagesList + "<div class='page' style='background-image:url(/home/rendier/Ptolemy/include/flipbookjs/books/{0}/{1})'></div>\n".format(
					self.book.replace(" ", "\ "), image)
		
		pagesList = pagesList + "<div class='hard'></div>\n<div class='hard' style='background-image:url(/home/rendier/Ptolemy/include/flipbookjs/back-cover.jpg)'></div>\n"
		
		# HTML: {BOOKTITLE} {PAGES}
		# CSS: {BOOKTOPMARGIN} {BOOKLEFTMARGIN}
		
		self.topMargin = int((self.tabsSize.height() - 735) / 2)
		self.leftMargin = int((self.tabsSize.width() - 1000) / 2)
		print("MARGINS: ", self.topMargin, self.leftMargin)
		
		
		skeletonindex = open(self.flippingBookDir + 'skeletonindex.html', 'rb').read().decode()
		skeletonindex = skeletonindex.replace("{BOOKTITLE}", self.book)
		skeletonindex = skeletonindex.replace("{PAGES}", pagesList)
		
		os.chdir(self.bookPath)
		
		with open(self.bookPath + 'skeletonindex.html', 'w+') as file:
			file.write(skeletonindex)
			file.close()
		
		skeletoncss = open(self.flippingBookDir + 'skeletoncss.css', 'rb').read().decode()
		skeletoncss = skeletoncss.replace("{BOOKTOPMARGIN}", str(self.topMargin))
		skeletoncss = skeletoncss.replace("{BOOKLEFTMARGIN}", str(self.leftMargin))
		
		
		with open(self.bookPath + 'skeletoncss.css', 'w+') as file:
			file.write(skeletoncss)
			file.close()
		
		os.chdir(self.homeDir)
		
		# self.webView.setHtml(skeleton, self.path)
		# self.webView.load(QUrl.fromUserInput(skeleton))#'%s?file=%s' % (PDFJS, PDF)))
		self.webView.load(QUrl.fromLocalFile(self.bookPath + 'skeletonindex.html'))
	
	def resizeEvent(self, QResizeEvent):
		print("RESIZE EVENT")
		self.tabsSize = self.Library.tabs.geometry()
		self.loadBook()
		# print("FRAME GEO: ", self.Library.win)
		
		
def main():

	app = QApplication(sys.argv)
	app.setApplicationName('Mouseion Library - Ptolemy')
	app.setFont(QFont('DejaVu Sans'))


	TheStudy = Library()
	TheStudy.win = TheStudy.frameGeometry()
	TheStudy.show()

	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec())


if __name__ == "__main__":
	main()