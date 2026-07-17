#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSvg import *
from PyQt6.QtSvgWidgets import *

from Callimachus.Database import Database
from Pharos.Dialogs import Dialogs
from Pharos.PtolFace import PtolFace
from Pharos.PGui import PMainWindow


class Notepad(PMainWindow, PtolFace):
    
    def __init__(self, parent=None):
        super(Notepad, self).__init__(parent)
        PMainWindow.__init__(self)
        
        self.Ptolemy = parent
        print("NOTEPAD PARENT: ", self.Ptolemy)
        
        self.setFixedSize(700, 500)
        
        if self.Ptolemy:
            self.database = self.Ptolemy.db
            self.dialogs = self.Ptolemy.dialogs
            self.styles = self.Ptolemy.stylesheet
            self.imgDir = self.Ptolemy.imgDir + 'Phaleron/'
            
            
        
        else:
            self.database = Database(self)
            self.dialogs = Dialogs(self)
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
            self.imgDir = PTOL_ROOT + "/images/Phaleron/"
            
        self.setStyleSheet(self.styles)

        self.updateDb()
        # print("ROWS: ", self.rows)
        self.initUi()
        
    def __del__(self):
        
        pass
    
    def initUi(self):
        
        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)
        
        self.title = QLabel('Note Name')
        self.title.setAlignment(Qt.AlignCenter)
        
        
        self.group = QComboBox()
        self.group.addItem('All')
        self.group.addItem('Favorite')
        self.group.insertSeparator(2)
        self.group.currentIndexChanged.connect(self.filterNotes)
        
        
        self.noteList = QListWidget()
        self.noteList.setStyleSheet("QListWidget { background-color: black; color: white; }")
        self.noteList.itemDoubleClicked.connect(self.displayNote)
        
        
        self.note = QTextEdit()
        self.note.setFixedSize(300, 475)
        self.note.setStyleSheet("QTextEdit { border: 1px solid white; }")
        
        self.addGroupBtn = QSvgWidget(self.imgDir + 'newtab.svg')
        self.addGroupBtn.setFixedSize(23, 23)
        self.addGroupBtn.setToolTip('Add New Note')
        self.addGroupBtn.mousePressEvent = self.newNote
        
        self.addNewNoteBtn = QPushButton("New Note")
        self.addNewNoteBtn.setToolTip('Add New Note')
        self.addNewNoteBtn.clicked.connect(self.newNote)
        
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.title, 0, 0, 1, 1)
        self.layout.addWidget(self.group, 1, 0, 1, 1)
        self.layout.addWidget(self.noteList, 2, 0, 7, 1)
        self.layout.addWidget(self.addNewNoteBtn, 10, 0, 1, 1)
        self.layout.addWidget(self.note, 0, 1, 10, 10)
        self.widget.setLayout(self.layout)
        
        self.getData()
        
    def updateDb(self):
        sql = "SELECT * FROM `PTOLdb`.`data_notes`"
        self.rows = self.database.dbReturnFA(sql)
    
    def getData(self):
        
        grouplist = []
        nameList = []
        
        for row in self.rows:
            if row[5] not in grouplist:
                grouplist.append(row[5])
                
        for group in grouplist:
            self.group.addItem(group)
        
        for row in self.rows:
            if row[1] not in nameList:
                nameList.append(row[1])
            
        for name in nameList:
            self.listentry(name)

    def listentry(self, text, tcolor='white', bcolor='black'):
    
        itemIn = QListWidgetItem(text)
        itemIn.setForeground(QColor(tcolor))
        itemIn.setBackground(QColor(bcolor))
    
        self.noteList.addItem(itemIn)
        
    def displayNote(self, event):
        for row in self.rows:
            if self.noteList.currentItem().text() in row:
                self.title.setText(row[1])
                self.note.setText("{0}   {3}   {1}\n\nGroup:{4}   Fav:{2}\n\n{5}\n\n{6}".format(row[0], row[3], row[6], row[1], row[5], row[4], row[2]))
                
        pass
    
    def filterNotes(self, event):
        
        comboText = self.group.currentText()
        
        if comboText == 'Favorite':
            
            comboList = []
            
            for row in self.rows:
                if str(row[6]) == "1":
                    comboList.append(row)
                    
            self.noteList.clear()
            
            for item in comboList:
                self.listentry(item[1])
            
            pass
        
        elif comboText == 'All':
            self.noteList.clear()
            self.getData()
        
        else:
            
            comboList = []
            
            for row in self.rows:
                if row[5] == comboText:
                    comboList.append(row)
            
            self.noteList.clear()
            
            for item in comboList:
                self.listentry(item[1])

        pass
    
    def newNote(self, event):
        self.dialogs.addNoteBox()
        self.group.clear()
        self.group.addItem('All')
        self.group.addItem('Favorite')
        self.group.insertSeparator(2)
        
        self.noteList.clear()
        self.updateDb()
        self.getData()
        
        
        

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = Notepad()
    # w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle('Phaleron - Ptolemy')
    # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
    w.setWindowIcon(QIcon(PTOL_ROOT + '/images/ptol.svg'))
    w.show()

    sys.exit(app.exec())