#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Philadelphos/CommandInput_qt.py — Qt Command Input Shell
=========================================================
Migrated from Ptolemy2/Pharos/Philadelphos/CommandInput.py (2026-05-07).

Full PyQt5 command widget — target for QTermWidget upgrade.
Pending: replace WebKit/OpenGL/espeak stack with QTermWidget when built.
See: Ainulindale ValaQuenta engine/console_qt.py for QTermWidget scaffold.

CommandInput.py (curses redirect stub) remains as the active entry point
until QTermWidget is confirmed installed and this widget is wired to PtolBus.
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebKitWidgets import *
from PyQt5.QtSvg import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKit import *

from subprocess import Popen, PIPE, call
from urllib.request import build_opener
from OpenGL.GLUT import *
from PIL import Image, ImageQt
from random import randrange
from espeak import espeak
from math import *
from collections import OrderedDict

import sys, os, time, inspect, psutil, pygame

from Pharos.VKeys import VirtualKeys





class Command(QWidget):

    def __init__(self, parent=None):
        super(Command, self).__init__(parent)
        
        self.Ptolemy = parent
        print("COMMAND PARENT", self.Ptolemy)

        # self.CommandGroup = self.scene.createItemGroup([self.Input])
        # self.CommandGroup.setFlag(QGraphicsItem.ItemIsMovable, True)
        # self.CommandGroup.setFiltersChildEvents(False)
        # self.CommandGroup.setAcceptHoverEvents(True)


        self.timeStamp = [self.Ptolemy.sysDate(), self.Ptolemy.sysTime(), self.Ptolemy.sysYear()]

        # Command Line Vars
        # self.cmdhistory = self.parent.cmdhistory

        self.x = 300
        self.y = 200
        self.w = 300
        self.h = 25

        self.x2 = 300
        self.y2 = 225
        self.w2 = 300
        self.h2 = 300

        self.rect = QRectF(self.x, self.y, 300, 325)
        self.boundrect = QRectF(self.x, self.y, 305, 330)

        # Ptolemy.scene.addRect(self.x - 1, self.y - 1, 152, 202, Ptolemy.pen('white'), Ptolemy.brush('black'))

        self.stylesheet = "QLabel {background-color: #000000; color: white} " \
                          "QLineEdit {background-color: #303030; color: white; border: 1px solid red} " \
                          "QWidget {background-color: #000000} " \
                          "QTextEdit {background-color: black; color: white; border: 1px solid blue}"

        self.setMouseTracking(True)

        self.setGeometry(300, 200, 300, 325)
        self.initUI()

    def __del__(self):

        pass

    def initUI(self):

        # self.cmdlbl = QtGui.QLabel()
        # self.cmdlbl.setText('  P. Philadelphos:')
        # self.cmdlbl.setStyleSheet(self.stylesheet)
        # self.cmdlbl.resize(100, 25)
        # self.cmdlbl.move(self.x + 5, self.y)

        self.cmd = QLineEdit(self)
        self.cmd.setStyleSheet(self.stylesheet)
        self.cmd.setFont(self.Ptolemy.font(10))
        # self.cmd.returnPressed.connect(self.cmdProcess(self.cmd.text().split(" ")))
        self.cmd.setGeometry(self.x, self.y, self.w, self.h)
        # self.cmd.resize(Ptolemy.screen.width() - 364, 25)
        # self.cmd.move(self.x + 110, self.y + 1)
        self.keys = QLabel('KEYS', parent=self)
        self.keys.setStyleSheet(self.stylesheet)
        # self.keys.setGeometry(self.x, self.y, self.h, self.h)
        self.keys.mousePressEvent = self.vkeys

        # self.statbox = QtGui.QGraphicsRectItem(self.x2, self.y2, self.w2, self.h2)
        # self.statbox.setPen(self.parent.pen('white', 1))

        self.PtolOut = QTextBrowser(self)
        self.PtolOut.setReadOnly(True)
        self.PtolOut.setStyleSheet(self.stylesheet)
        self.initialText = "Ex Fidelitas, Et Integritas, Nobilitas\nHello " + self.Ptolemy.user.decode() + ":\n" + str \
            (self.Ptolemy.timeStamp()) + "\n" + self.shIn('uname -a')[0].decode() + "\n"
        self.PtolOut.setText(self.initialText)
        self.PtolOut.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.PtolOut.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.PtolOut.setGeometry(self.x2, self.y2, self.w2, self.h2)
        self.PtolOut.setFont(self.Ptolemy.font(8))
        self.PtolOut.moveCursor(QTextCursor.End)
        self.PtolOut.setMouseTracking(True)
        self.PtolOut.ensureCursorVisible()
        self.PtolOut.mouseDoubleClickEvent = self.cornerEvent

        # self.outLog = OutLog(parent=self)

        # sys.stdout = self.outLog(color='white')
        # sys.stderr = self.outLog(color='red')

        self.layout = QGridLayout()
        self.layout.setSpacing(0)

        self.layout.addWidget(self.cmd, 0, 0, 1, 1)
        self.layout.addWidget(self.keys, 0, 1, 1, 1)
        self.layout.addWidget(self.PtolOut, 1, 0, 4, 1)

        self.setLayout(self.layout)
        self.corner = self.Ptolemy.scene.addRect(
            self.x + self.w - 25,
            self.y + self.h + self.h2 - 25,
            28,
            28,
            self.Ptolemy.pen('white', 1),
            self.Ptolemy.brush('black')
        )
        self.Ptolemy.scene.addItem(self.corner)
        self.corner.enterEvent = self.cornerEvent
        self.corner.mousePressEvent = self.cornerEvent
        self.corner.setZValue(0)


        self.cmd.setFocus()

    def vkeys(self, event):

        self.Keyboard = VirtualKeys(parent=self)
        
        self.cmd.setText(self.Keyboard.get_input())
    
    def boundingRect(self):

        return self.boundrect

    def cornerEvent(self, event):

        self.setOutput('entered corner box' + str(event))
        pass

    def keyPressEvent(self, event):

        if self.cmd.hasFocus() == True:

            if event.key() == Qt.Key_Return:
                print(str(self.cmd.text()))
                self.cmdProcess(str(self.cmd.displayText()))

            if event.key() == Qt.Key_Up:
                self.setOutput('Look Here Up Arrow')
                self.cmd.setText(self.Ptolemy.cmdhistory[-1][1])

    def mousePressEvent(self, event):

        self.setOutput('Philadelphos mouse press event')
        # self.setOutput(self.parent.scene.itemAt(event.x(), event.y()))

        # if Ptolemy.CommandGroup.handlesChildEvents == True:
        # 	Ptolemy.CommandGroup.setHandlesChildEvents(False)
        # 	self.corner.setZValue(1)
        #
        # else:
        # 	Ptolemy.CommandGroup.setHandlesChildEvents(True)
        # 	self.corner.setZValue(0)

        self.setOutput("Πτολεμαῖος Φιλάδελφος", voice='other/grc', speak=True)

    def mouseDoubleClickEvent(self, event):

        self.setOutput('Command Double Click Event')

    def enterEvent(self, event):

        self.setOutput(f'{self.__class__.__name__} enter event')

    # Command Processing
    def cmdProcess(self, commands):  # FIX FOR PLATFORM INDEPENDENT TODO

        cmdtype = commands[0]
        command = commands[1:]

        POut = None
        PErr = None

        if commands.lower() == 'ptol out':
            self.saveLog("cmdhistory.log", str(self.Ptolemy.cmdhistory))
            self.speak("Goodbye")
            exit()


        elif cmdtype == "?":  # Create Ptolemy Command Parser TODO
            self.setOutput("FIX PTOLEMY II COMMAND PARSER", 'yellow')
            self.setOutput("Normal Output Text", 'cyan')
            pass

        # Python Prompt
        elif cmdtype == ">":

            self.pyIn(command, parent=self)

        # Bash Prompt
        elif cmdtype == "$":
            try:
                POut, PErr = self.shIn(str(command))
                print("POUT", POut, 'PERR', PErr)
                if len(PErr) != 0:
                    print("RAISING")
                    raise ValueError(f"Raising Shell Error #{str(PErr)}")

            except ValueError:
                self.setOutput("SHELL ERROR:\n" + str(PErr), color='red', speak=True)

            else:
                self.setOutput("Shell Output:\n" + str(POut), color='cyan', speak=True)
            pass

        # Root Prompt#FIX FOR ROOT SHELL COMMANDS TODO
        elif cmdtype == "#":
            try:
                POut, PErr = self.shIn("gksudo " + command)

            except:
                self.setOutput("ROOT SHELL ERROR:\n" + str(PErr), 'red')

            else:
                self.setOutput("FIX FOR ROOT SHELL COMMANDS\n" + str(POut), 'red')  # TODO
            pass

        else:
            POut = "No Prompt Chosen"
            PErr = "PTOLEMY ERROR:\nNO PROMPT"
            self.setOutput((POut + PErr), 'red')
            self.speak("Ptolemy Error: Placeholder, No Speech Parser Installed Yet")  # TODO
            pass

        self.Ptolemy.cmdhistory.append([self.Ptolemy.timeStamp(), str(cmdtype) + command, POut, PErr])
        self.cmd.clear()
        self.cmd.setFocus()
        pass

    def speak(self, text, voice='en'):

        # self.setOutput('Text:\n' + text, 'red')
        espeak.set_parameter(espeak.Parameter.Rate, 175)
        espeak.set_parameter(espeak.Parameter.Wordgap, 3)
        espeak.set_parameter(espeak.Parameter.Pitch, 65)
        espeak.set_parameter(espeak.Parameter.Volume, 55)
        # espeak.set_parameter(espeak.Parameter.Capitals, 1)
        # German: 'de', Ancient Greek: 'other/grc', English: 'en'
        espeak.set_voice(voice)
        espeak.synth(text)

    # Make so automagically speaks language written but only those characters TODO
    def setOutput(self, text, color='white', voice='en', speak=False):  ###FIX: length text marquee

        # print "INOUTPUT"
        self.PtolOut.moveCursor(QTextCursor.End)
        self.PtolOut.setTextColor(self.Ptolemy.color(color))

        try:
            unicode(text)

        except UnicodeDecodeError:
            self.PtolOut.append(text.decode('utf-8') + "\n")

        else:
            try:
                self.PtolOut.append(text + "\n")

            except TypeError:
                self.PtolOut.append(str(text) + "\n")

        if speak == True:
            if len(text) < 140:
                self.speak(text, voice)
            else:
                self.speak(" ".join(text.split()[:19]), voice)

        self.PtolOut.setTextColor(self.Ptolemy.color('white'))
        self.PtolOut.moveCursor(QTextCursor.End)
        self.PtolOut.ensureCursorVisible()

    def saveLog(self, logname, text):

        with open("/home/rendier/Ptolemy/include/logs/{}".format(logname), "a") as f:
            # content = f.read()
            # f.write(content + "\n" + text)
            f.write(text)
            f.close()

    def pyIn(self, command, parent=None):

        PErr = ""
        try:
            print("TRYING EVAL")
            POut = eval(command)

        except AttributeError:
            PErr = sys.__stderr__
            self.setOutput("PYTHON ATTRIBUTE ERROR:\n" + str(PErr), 'red')

        except SyntaxError:
            # PErr = sys.__stderr__
            # self.setOutput("PYTHON SYNTAX ERROR: Using Exec Command", 'blue')
            # self.setOutput("PYTHON SYNTAX ERROR:\n" + str(PErr) + "Using exec command.", 'red')
            try:
                print("TRYING EXEC")
                POut = sys.stdout
                self.setOutput(f'Python Exec Output {POut}', 'white')
                exec(command)
                print(dir())

            except:
                PErr = sys.stderr
                self.setOutput(f'PYTHON INDEX ERROR\n {PErr}', 'red')

        except:
            PErr = sys.__stderr__
            PErr.readable = True
            print("PYTHON ERROR")
            print("TYPE:", type(PErr), "\n", dir(PErr))
            print(PErr.errors, "\n", PErr.read, "\n", PErr.tell, "\n", PErr.name, "\n", PErr.flush)
            
            self.setOutput(f'Python Error\n{sys.__stderr__}', 'red', speak=True)

        # self.setOutput("Python Output:\n" + str(POut), 'green', speak=True)

        # except:
        # 	PErr = 'Code Exception'
        # 	self.speak('Python Exec Error')
        # 	self.setOutput('PYTHON EXEC ERROR\n' + str(PErr), 'red')
        # 	# you can use <traceback> module here

        # self.setOutput(PErr, 'red')
        # sys.stdout = __stdout
        # # return result

        else:
            self.setOutput("Python Output:\n" + str(POut), 'green', speak=True)
            # pass

            self.Ptolemy.cmdhistory.append([self.Ptolemy.timeStamp(), '>' + command, POut, PErr])
            self.cmd.clear()
            self.cmd.setFocus()
        pass

    def shIn(self, command):
        print("SH IN:", command)
        process = Popen(
            args=command,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()
        pass

    # ADD SPEECH TO TEXT HERE TODO
    def PtolIn(self, command):

        pass

    def outLog(self, msg=None, color=None):

        self.color = color
        self.msg = msg

        if self.color:
            # tc = self.edit.textColor()
            self.PtolOut.setTextColor(QColor(self.color))

        self.PtolOut.moveCursor(QTextCursor.End)
        self.PtolOut.insertPlainText(self.msg)

    # if self.color:
    # 	self.edit.setTextColor(tc)

    # if self.out:
    # 	self.out.write(self.msg + "\n")