#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import *
from PyQt5.QtWidgets import *

from DebugPrint import dbprint

from math import *
from random import randrange
from subprocess import Popen, PIPE, call
from OpenGL.GLUT import *

import os, psutil


class WorkThread(QThread):
    workFinished = pyqtSignal(list)
    
    def __init__(self, parent, stype, *args):
        super(WorkThread, self).__init__(parent)
        
        self.parent = parent
        self.Ptolemy = parent
        
        self.run_signal = stype
    
    def __del__(self):
        pass
    
    def run(self):
        if self.run_signal == 1:
            self.command_input
        
        pass

class User(QGraphicsItem):
    print('-=User=-')

    # Signals
    interfaceMouseEvent = pyqtSignal(QEvent)

    def __init__(self, Ptolemy, parent=None):
        super(User, self).__init__(parent)
        QGraphicsItem.__init__(self)

        self.Ptolemy = Ptolemy
        print(self.Ptolemy)

        self.DEBUGPRINT = 0
        dbprint('User.__init__', self)





        self.x = Ptolemy.scene.width() / 2 - 76
        self.y = Ptolemy.scene.height() / 2 - 175
        self.w = 225
        self.h = 350
        self.centerx = self.x + self.w / 2
        self.centery = self.y + self.h / 2

        self.centerrect = QRectF(self.centerx - 75, self.centery - 75, 100, 100)

        self.rect = QRectF(self.x, self.y, self.w, self.h)

        # self.userGroup = self.Ptolemy.scene.createItemGroup([self])
        # self.userGroup.setFlag(QGraphicsItem.ItemIsMovable, True)
        # self.userGroup.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # self.userGroup.setFlag(QGraphicsItem.ItemIsFocusable, True)
        # self.userGroup.installSceneEventFilter(self)
        # self.userGroup.setAcceptHoverEvents(True)
        # self.userGroup.setFiltersChildEvents(True)
        # self.userGroup.setZValue(1)
        # self.interfaceMouseEvent.connect(self.mousePressEvent)
        # self.userGroup.mousePressEvent = self.mousePressEvent(QGraphicsSceneMouseEvent)
        # self.userGroup.mousePressEvent(QGraphicsSceneMouseEvent).accept()

        
        
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.setAcceptHoverEvents(True)
        # self.installSceneEventFilter(self)


        self.output = self.Ptolemy.Philadelphos.setOutput
        self.interfaceimgs = self.Ptolemy.pharosImg
        self.media = self.Ptolemy.mediaDir
        self.scene = self.Ptolemy.scene

       

        self.GROUP_FLAG = False
        self.AUDIO_UP = False
        self.KEYS_UP = False
        self.TERM_UP = False
        self.PKG_UP = False
        self.MINER_UP = False
        self.MONITOR = False

        self.ALEXANDRIA_MENU = False
        self.ARCHIMEDES_MENU = False
        self.CALLIMACHUS_MENU = False
        self.PHALERON_MENU = False
        self.PHAROS_MENU = True
        self.MUSAEUM_MENU = False

        self.screensaver = QTimer()
        self.screensaver.timeout.connect(self.switchMonitor)
        self.screensaver.setSingleShot(True)

        self.identity = "Pharos"
        self.cwd = "*".join(Ptolemy.cwd()[1:].split("/")[-3:])

        # self.setToolTip(self.identity + ' Interface')





        images = os.listdir(self.interfaceimgs)
        rand = randrange(len(images))
        self.bgimage = "nav_seal_200.png"  # ""nav_seal.jpg"#images[rand]

        self.renderer = QSvgRenderer(self.interfaceimgs + 'nav-seal.svg')

        # Redraw
        self.Ptolemy.cronJob(0.01, self.refresh())

        self.colors = [(r, g, b) for r in (0, 1) for g in (0, 1) for b in (0, 1)]
        self.colordict = {
            (0, 0, 0): 'black',
            (0, 0, 1): 'blue',
            (0, 1, 0): 'green',
            (0, 1, 1): 'cyan',
            (1, 0, 0): 'red',
            (1, 0, 1): 'yellow',
            (1, 1, 0): 'magenta',
            (1, 1, 1): 'white',

        }
        GLFonts = [
            GLUT_BITMAP_8_BY_13,
            GLUT_BITMAP_9_BY_15,
            GLUT_BITMAP_TIMES_ROMAN_10,
            GLUT_BITMAP_HELVETICA_10,
            GLUT_BITMAP_HELVETICA_12
        ]

    # self.Clock = Clock(parent=self)
    # self.Power = Power(0, parent=self)
    # self.OnScreenKeys = OnScreenKeyboard(1, parent=self)
    # self.Sound = Sound(2, parent=self)
    # self.Terminal = Terminal(3, parent=self)
    # self.Miner = Norton(4, parent=self)
    # self.CodeBrowser = Packages(5, parent=self)


    # # self.setFlag(QGraphicsRectItem.)
    # self.setZValue(Ptolemy.scene.items()[0].zValue() + 1)

    # Ptolemy.scene.addItem(self)


    def boundingRect(self):
        dbprint('User.boundingRect', self)

        return self.rect

    def paint(self, painter, option, widget):

        self.refresh()

        painter.setPen(self.Ptolemy.pen(self.color))
        painter.setBrush(self.Ptolemy.brush('black'))
        painter.setFont(self.Ptolemy.font(12))
        painter.drawRect(self.rect)
        painter.drawRect(self.x + 2, self.y + 2, self.w - 4, self.h - 4)

        self.renderer.render(painter, QRectF(self.centerx - 100, self.centery - 100, 200, 200))

        self.title(painter, self.name, 0, 13)
        self.title(painter, self.platform, 1, 28)
        self.title(painter, self.user, 1, 43)
        self.title(painter, self.nodename, 1, 58)

        if self.MONITOR == True:
            self.procMonitor(painter)

        self.systemTray(painter)

        self.archtype(painter, self.identity)
        pass

    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent'):
        print('User.mousePressEvent')

        # self.output("User Mouse Press Event" + str(event.pos()))
        # self.output(dir(self.parent.scene.itemAt(event.pos())))
        # self.setZValue(Ptolemy.scene.items()[0].zValue() + 1)
        locs = locals()


        if event.button() == Qt.LeftButton:
            # self.output("Event Left Button")

            if event.pos() in self.powerrect:
                self.saveLog("cmdhistory.log", str(self.Ptolemy.cmdhistory))
                exit()
                pass

            if event.pos() in self.phaleronifrect:
                # self.Search = self.Ptolemy.Phaleron.TreasureHunter.Main()
                # self.Search.show()
                pass

            # elif event.pos() in self.onscreenkeysrect:
            # 	# FIX TO ADD THE FOUR PROMPTS TO OSK TODO
            # 	# Fix keys to dynamically size TODO
            # 	# fix input to command line TODO
            # 	# fix pygame.error video system not initialized TODO
            # 	if self.KEYS_UP == False:
            # 		from Pharos.VirtualKeyboard import VirtualKeyboard
            # 		self.KEYS_UP = True
            #
            # 		self.keyboard = VirtualKeyboard()
            #
            # 		pygame.display.init()
            # 		size = 800, 450
            # 		screen = pygame.display.set_mode(size, pygame.NOFRAME)
            #
            # 		userinput = self.keyboard.run(screen)
            #
            # 		# Ptolemy.Philadelphos.cmd.setText(u'userinput')
            #
            # 		Ptolemy.Philadelphos.cmd.setText(userinput)
            # 		Ptolemy.Philadelphos.setFocus()
            #
            # 		pygame.display.quit()
            #
            # 		self.KEYS_UP = False
            #
            # 		del self.keyboard
            #
            #
            # 	elif self.KEYS_UP == True:
            #
            # 		self.KEYS_UP = False
            # 		pygame.display.quit()
            #
            # 		del self.keyboard
            #
            # 	pass

            # Make into own window TODO
            # elif event.pos() in self.soundrect:
            # 	self.output('Sound Click', 'red')
            # 	if self.AUDIO_UP == False:
            # 		self.AUDIO_UP = True
            # 		self.audiobox = self.Ptolemy.scene.addRect(
            # 			self.Ptolemy.scene.width() - 703,
            # 			self.Ptolemy.scene.height() - 435,
            # 			641,
            # 			410,
            # 			self.Ptolemy.pen('white'),
            # 			self.Ptolemy.brush('black')
            # 		)
            # 		self.player = self.parent.scene.addWidget(AudioPlayer(self.Ptolemy.mediaDir + 'audio/NES_FFprelude.mp3'))
            # 		self.player.setZValue(1)
            # 		self.player.setPos(self.w - 702, self.h - 434)
            # 		self.translate(0, -12)
            # 		self.player.setFocus()
            #
            # 	elif self.AUDIO_UP == True:
            # 		self.AUDIO_UP = False
            # 		self.parent.scene.removeItem(self.audiobox)
            # 		self.parent.scene.removeItem(self.player)
            # 		del self.audiobox
            # 		del self.player
            # 		self.translate(0, 12)
            # 	pass
            #
            # 	pass

            # FIX EACH MENU TO UPDATE CRUMBS TODO
            if self.PHAROS_MENU == True:

                if event.pos() in self.alexandriaifrect:
                    print
                    "Alexandria Menu"
                    self.ALEXANDRIA_MENU = True
                    self.PHAROS_MENU = False

                elif event.pos() in self.archimedesifrect:
                    print
                    "Archimedes Menu"
                    self.ARCHIMEDES_MENU = True
                    self.PHAROS_MENU = False
                #
                elif event.pos() in self.callimachusifrect:
                    print
                    "Callimachus Menu"
                    self.CALLIMACHUS_MENU = True
                    self.PHAROS_MENU = False

                elif event.pos() in self.phaleronifrect:
                    print
                    "Phaleron Menu"
                    self.PHALERON_MENU = True
                    self.PHAROS_MENU = False

                elif event.pos() in self.musaeumifrect:
                    print
                    "Musaeum Menu"
                    self.MUSAEUM_MENU = True
                    self.PHAROS_MENU = False

                pass

            elif self.CALLIMACHUS_MENU == True:

                pass

            elif self.ALEXANDRIA_MENU == True:

                pass

            elif self.ARCHIMEDES_MENU == True:

                pass

            elif self.PHALERON_MENU == True:

                pass

            elif self.MUSAEUM_MENU == True:

                pass

            # elif event.pos() in self.terminalrect:
            # 	self.output('Terminal Click', 'red')
            #
            # 	if self.TERM_UP == False:
            # 		self.TERM_UP = True
            # 		self.termbox = Ptolemy.scene.addRect(self.scene.width() - 703, self.scene.height() - 435, 641, 385, Ptolemy.pen('white'), Ptolemy.brush('black'))
            # 		self.console = Ptolemy.scene.addWidget(QTermWidget.QTermWidget())
            # 		self.console.setZValue(1)
            # 		self.console.setGeometry(QtCore.QRectF(self.scene.width() - 702, self.scene.height() - 434, 639, 384))
            # 		self.console.setFocus()
            #
            # 	elif self.TERM_UP == True:
            # 		self.TERM_UP = False
            # 		Ptolemy.scene.removeItem(self.console)
            # 		Ptolemy.scene.removeItem(self.termbox)
            # 		del self.console
            # 		del self.termbox
            #
            # 	pass

            # elif event.pos() in self.minerrect:
            # 	# call(['python', 'scripts/Phaleron/Norton.py'])
            # 	os.system('python scripts/Phaleron/Norton.py')
            # 	print 'not yet'

            pass

        # elif event.button() == QtCore.Qt.RightButton:
        # 	self.output("Event Right Button")
        #
        # 	if event.pos() in QtCore.QRectF(self.x, self.y + 300, 25, 25):
        # 		pass

        # elif event.button() == QtCore.Qt.MiddleButton:
        #
        #
        # 	pass

        # self.Ptolemy.scene.mousePressEvent(event)
        pass

    def mouseDoubleClickEvent(self, event):
        dbprint('User.mouseDoubleClickEvent', self)
        # self.output("User Mouse Double Click Event")
        # if self.SystemTray.handlesChildEvents == False:
        # 	self.SystemTray.setHandlesChildEvents(True)
        #
        # else:
        # 	self.SystemTray.setHandlesChildEvents(False)

        # QGraphicsObject.mouseDoubleClickEvent(self, event)
        pass

    def mouseReleaseEvent(self, event):
        dbprint('User.mouseReleaseEvent', self)
        # self.output('User Mouse Release Event')

        # if event.pos() in QtCore.QRectF(self.x + 70, self.y + 70, 10, 10):
        # 	self.output('Event Kernel Release')
        #
        # 	pass

        # QGraphicsObject.mouseReleaseEvent(self, event)
        pass

    def mouseMoveEvent(self, event):
        dbprint('User.mouseMoveEvent', self)

        # self.output('User Mouse Move Event')
        # Ptolemy.PharosGroup.addToGroup(self.SystemTray)
        # print Ptolemy.PharosGroup.items()
        # self.SystemTray.setHandlesChildEvents(True)

        # while event.oldPos != event.pos:
        # 	Pharos.PharosGroup.addToGroup(self.sysTray)
        #
        # else:
        # 	Pharos.PharosGroup.removeFromGroup(self.sysTray)
        # QGraphicsObject.mouseMoveEvent(self, event)
        pass

    def hoverEnterEvent(self, event):
        dbprint('User.hoverEnterEvent', self)

        self.renderer = QSvgRenderer(self.interfaceimgs + 'nav-seal-over.svg')

        self.MONITOR = False
        if self.screensaver.isActive() == True:
            self.screensaver.stop()

        QGraphicsObject.hoverEnterEvent(self, event)
        pass

    def hoverLeaveEvent(self, event):
        dbprint('User.hoverLeaveEvent', self)

        self.renderer = QSvgRenderer(self.interfaceimgs + 'nav-seal.svg')
        self.setToolTip("Pharos Interface")
        self.screensaver.start(10000)

        # QtGui.QGraphicsObject.hoverLeaveEvent(self, event)

        pass

    def wheelEvent(self, event):
        dbprint('User.wheelEvent', self)

        if event.delta() > 0 and event.pos() in self.soundrect:
            self.output("volume up", 'red')
            call(["amixer", "-D", "pulse", "sset", "Master", "10%+"])
            pass

        elif event.delta() < 0 and event.pos() in self.soundrect:
            self.output('volume down', 'red')
            call(["amixer", "-D", "pulse", "sset", "Master", "10%-"])
            pass

        # QGraphicsItem.wheelEvent(self, event)
        pass

    def sceneEventFilter(self, watched: 'QGraphicsItem', event: QEvent):
        if (event.type() == QEvent.MouseButtonPress and
                watched is self.userGroup):
            pos = event.pos()
            print('Event Filter Activated', pos)
        return QGraphicsItem.sceneEventFilter(self, watched, event)

    def archtype(self, painter, persona=None):
        dbprint('User.archtype', self)

        painter.setPen(self.Ptolemy.pen('white'))
        painter.setFont(self.Ptolemy.font(14))
        ####
        # radius = 70
        # painter.drawEllipse(QtCore.QRectF(
        # 	self.centerx - radius,
        # 	self.centery - radius,
        # 	2 * radius + 1,
        # 	2 * radius + 1
        # )
        # )
        # radius = 90
        # painter.drawEllipse(QtCore.QRectF(
        # 	self.centerx - radius,
        # 	self.centery - radius,
        # 	2 * radius + 1,
        # 	2 * radius + 1,
        # )
        # )
        ####

        # radius = 95
        # # One Word Vars
        # stringlength = len(self.name)
        # stringspaced = stringlength * 2 + 2
        # stringwordlength = stringspaced * stringlength
        #
        # sweep_angle = 250
        # start_angle = 145
        # self.labelcur(
        # 	painter,
        # 	self.centerx - 3, self.centery + 5,
        # 	radius, start_angle, sweep_angle,
        # 	self.name.capitalize()
        # )

        radius = 100
        sweep_angle = 160
        start_angle = 190

        self.cwd = "*".join(self.Ptolemy.cwd()[1:].split("/")[-3:])

        painter.setPen(self.Ptolemy.pen('blue'))
        self.labelcur(
            painter,
            self.centerx - 3, self.centery + 5,
            radius, start_angle, sweep_angle,
            self.cwd
        )
        painter.setPen(self.Ptolemy.pen('white'))
        self.labelcur(
            painter,
            self.centerx - 4, self.centery + 6,
            radius, start_angle, sweep_angle,
            self.cwd
        )

        if persona:
            painter.setPen(self.Ptolemy.pen('darkgreen', 2))
            painter.setFont(self.Ptolemy.font(12))
            radius = 100
            sweep_angle = -110
            start_angle = 145
            self.labelcur(
                painter,
                self.centerx - 3, self.centery + 5,
                radius, start_angle, sweep_angle,
                persona
            )
            painter.setPen(self.Ptolemy.pen('orange'))
            self.labelcur(
                painter,
                self.centerx - 4, self.centery + 6,
                radius, start_angle, sweep_angle,
                persona
            )

    def refresh(self):
        dbprint('User.refresh', self)

        self.name = str(self.Ptolemy.name)
        self.user = str(self.Ptolemy.user)[2:-1]
        self.platform = str(self.Ptolemy.platform)[2:-1]
        self.nodename = str(self.Ptolemy.nodename)[2:-1]

        self.time = self.Ptolemy.sysTime()
        self.date = self.Ptolemy.sysDate()

        voloutput = self.cmdline('amixer cget numid=13')

        self.volume = int(voloutput.decode().split(':')[1].split('\n')[0].split('=')[1])
        volumepct = self.volume / 87.

        self.volangle = 360 * volumepct

        if self.identity == 'Pharos':
            self.color = 'darkcyan'
            self.ALEXANDRIA_MENU = False
            self.ARCHIMEDES_MENU = False
            self.CALLIMACHUS_MENU = False
            self.PHALERON_MENU = False
            self.PHAROS_MENU = True
            self.MUSAEUM_MENU = False

        elif 'Alexandria' in self.Ptolemy.PharosMenu.crumbs:
            self.color = 'darkred'
            self.PHAROS_MENU = False
            self.ALEXANDRIA_MENU = True

        elif 'Archimedes' in self.Ptolemy.PharosMenu.crumbs:
            self.color = 'darkblue'
            self.PHAROS_MENU = False
            self.ARCHIMEDES_MENU = True

        elif 'Callimachus' in self.Ptolemy.PharosMenu.crumbs:
            self.color = 'darkgreen'
            self.PHAROS_MENU = False
            self.CALLIMACHUS_MENU = True

        elif 'Phaleron' in self.Ptolemy.PharosMenu.crumbs:
            self.color = 'grey'
            self.PHAROS_MENU = False
            self.PHALERON_MENU = True

        elif 'Musaeum' in self.Ptolemy.PharosMenu.crumbs:
            self.color = 'darkmagenta'
            self.PHAROS_MENU = False
            self.MUSAEUM_MENU = True

        self.update(self.rect)

    def eventFilter(self, source, event):
        dbprint('User.eventFilter', self)

    def switchMonitor(self):
        dbprint('User.switchMonitor', self)

        self.MONITOR = True

    def fileShift(self):
        dbprint('User.fileShift', self)

        pass

    def menuShift(self):
        dbprint('User.menuShift', self)

        pass

    def procMonitor(self, painter):
        dbprint('User.procMonitor', self)

        # CPU Stats
        self.cpuCount = psutil.cpu_count()
        self.cpuPercent = psutil.cpu_percent(None, True)
        self.cpuAngle = 360.0 / self.cpuCount

        # RAM Stats
        self.psMem = psutil.virtual_memory()
        self.memAngle = 360.0 * (self.psMem[2] / 100.)
        self.memDarkAngle = 360.0 - self.memAngle

        # SWAP Stats
        self.psSwap = psutil.swap_memory()
        self.swapAngle = 360 * (self.psSwap[3] / 100.0)

        # NET Stats
        # Add Interface Chooser TODO

        self.netIF = self.cmdline('ls /sys/class/net/').decode().split("\n")[:-1]
        self.netCount = len(self.netIF)
        self.netAngle = 360.0 / self.netCount
        self.netStats1 = psutil.net_io_counters(True)
        self.netTx = self.netStats1[self.netIF[0]][0]
        self.netRx = self.netStats1[self.netIF[1]][1]

        # Processes and percentages
        self.proc = psutil.process_iter()
        self.procList = []
        for i in self.proc:
            self.procList.append(i)
        self.procNum = len(self.procList)
        self.procAngle = 360.0 / self.procNum
        self.procColor = 0
        self.procSquare = ceil(sqrt(self.procNum))
        self.procNetNum = len(self.cmdline('ls /sys/class/net/').decode().split("\n")[:-1])

        # Kernel
        painter.setBrush(self.Ptolemy.brush('white'))
        self.KERNEL = painter.drawEllipse(self.centerx - 10, self.centery - 10, 19, 19)

        # Cpu
        for i in range(self.cpuCount):
            color = self.colordict[self.colors[i + 3]]
            painter.setPen(self.Ptolemy.pen(color, 3))
            exec \
                ("self.CPU{0} = self.arc(painter, self.centerx, self.centery, 20, i * self.cpuAngle, self.cpuAngle * (self.cpuPercent[i] / 100.))".format
                    (i))

        # Ram
        painter.setPen(self.Ptolemy.pen('cyan', 3))
        self.RAM = self.arc(painter, self.centerx, self.centery, 30, 0, self.memAngle)

        # VMEM
        self.VMEM = self.arc(painter, self.centerx, self.centery, 40, 0, self.swapAngle)

        # GPU
        self.GPU = self.arc(painter, self.centerx, self.centery, 50, 0, 360)

        # Net
        for i in range(len(self.netIF)):
            color = self.colordict[self.colors[i + 1]]
            # Placeholder
            painter.setPen(self.Ptolemy.pen(color, 1))
            # self.arc(painter, self.centerx, self.centery, 60, i * self.netAngle, self.netAngle)
            painter.setPen(self.Ptolemy.pen(color, 8))
            if self.netstat(self.netIF[i]) == True:
                exec
                "self.NET{0} = self.arc(painter, self.centerx, self.centery, 60, i * self.netAngle, self.netAngle)".format(
                    i)

        # Proc FIX THIS for different colors according to status and place Zombie or Dead processes perm TODO
        painter.setPen(self.Ptolemy.pen('cyan', 20))
        for i in range(self.procNum):
            try:
                procPercent = self.procList[i].cpu_percent()
            except psutil.NoSuchProcess:
                pass
            else:
                if procPercent > 0:
                    exec
                    "self.PROC{0} = self.arc(painter, self.centerx, self.centery, 80, i * self.procAngle, self.procAngle)".format(
                        i)

        pass

    # System Tray
    def systemTray(self, painter):
        dbprint('User.systemTray', self)

        self.Clock = self.clock(painter)
        self.Power = self.power(0, painter)
        self.OnScreenKeys = self.onscreenkeys(1, painter)
        self.Sound = self.sound(2, painter)

        if self.PHAROS_MENU == False:
            self.PharosIf = self.pharosif(3, painter)

        if self.ALEXANDRIA_MENU == True:
            self.alexandriaTray(painter)

        elif self.ARCHIMEDES_MENU == True:
            self.archimedesTray(painter)

        elif self.CALLIMACHUS_MENU == True:
            self.callimachusTray(painter)

        elif self.PHALERON_MENU == True:
            self.phaleronTray(painter)

        elif self.PHAROS_MENU == True:
            self.pharosTray(painter)

        elif self.MUSAEUM_MENU == True:
            self.musaeumTray(painter)

    # CREATE SYSTRAYS FOR EACH MENU TODO
    def alexandriaTray(self, painter):
        dbprint('User.alexandriaTray', self)

        """
        Pharos,
        Power, On Screen Keyboard, Volume Control,
        Core-Grid-City-Tron
        :return:
        """
        pass

    def archimedesTray(self, painter):
        dbprint('User.archimedesTray', self)

        """
        Pharos,
        Mechanics, Electromagnetics, Thermodyamics
        Statistics and Probability, Trigonometry,
        Geometry, Calculus, Algebra
        :return:
        """
        pass

    def callimachusTray(self, painter):
        dbprint('User.callimachusTray', self)

        """
        Pharos,
        Database
        :return:
        """

        pass

    def phaleronTray(self, painter):
        dbprint('User.phaleronTray', self)

        """
        Pharos,
        Package Browser, Data Miner
        :return:
        """
        self.Miner = self.miner(4, painter)
        self.CodeBrowser = self.codebrowser(5, painter)
        pass

    def pharosTray(self, painter):
        dbprint('User.pharosTray', self)

        """
        Alexandria, Archimedes, Callimachus,
        Phaleron, Musaeum
        :return:
        """

        self.Alexandria = self.alexandriaif(4, painter)
        self.Archimedes = self.archimedesif(5, painter)
        self.Callimachus = self.callimachusif(6, painter)
        self.Phaleron = self.phaleronif(7, painter)
        self.Musaeum = self.musaeumif(8, painter)

        # self.PharosIf = self.pharosif(8, painter)
        pass

    def musaeumTray(self, painter):
        dbprint('User.musaeumTray', self)

        """
        Pharos,
        FlippingBook, Audio Player, Image Viewer
        :return:
        """
        pass

    # Fix running in threads or otherwise for external programs. TODO
    # ADD CLASSES TO THIS FOR TOOLTIP MENU TODO
    def power(self, place, painter, flag=False):

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.powerrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'power.svg', self.powerrect)


        pass

    # Utilize system onscreen keyboard if available, pygame as fallback TODO
    def onscreenkeys(self, place, painter):
        dbprint('User.onscreenkeys', self)

        x = self.x + place * 25
        y = self.y + 300

        if self.KEYS_UP == True:
            y -= 12

        self.onscreenkeysrect = QRectF(x + 1, y + 1, 23, 23)

        QSvgRenderer(self.interfaceimgs + 'onscreenkeys.svg').render(painter, self.onscreenkeysrect)

        pass

    # Add streaming music to audio player and pandora TODO
    def sound(self, place, painter):
        dbprint('User.sound', self)

        x = self.x + place * 25
        y = self.y + 300

        if self.AUDIO_UP == True:
            y -= 12

        self.soundrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'volume-icon.svg', self.soundrect)

        painter.setPen(self.Ptolemy.pen(QColor(255, 0, 0, 255), 3))
        painter.drawArc(QRectF(x + 3, y + 3, 18, 18), 0, self.volangle * 16)

        pass

    def terminal(self, place, painter):
        dbprint('User.terminal', self)

        x = self.x + place * 25
        y = self.y + 300

        if self.TERM_UP == True:
            y -= 12

        self.terminalrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'terminal.svg', self.terminalrect)

        pass

    def miner(self, place, painter):
        dbprint('User.miner', self)

        x = self.x + place * 25
        y = self.y + 300

        if self.MINER_UP == True:
            y -= 12

        self.minerrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'miner.svg', self.minerrect)

    def codebrowser(self, place, painter):
        dbprint('User.codebrowser', self)

        x = self.x + place * 25
        y = self.y + 300

        if self.PKG_UP == True:
            y -= 12

        self.codebrowserrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'pkgbrowser.svg', self.codebrowserrect)

    def pharosif(self, place, painter, flag=False):
        dbprint('User.pharosif', self)

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.pharosifrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'pharossymbol.svg', self.pharosifrect)

    def alexandriaif(self, place, painter, flag=False):
        dbprint('User.alexandriaif', self)

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.alexandriaifrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'alexandriasymbol.svg', self.alexandriaifrect)

    def archimedesif(self, place, painter, flag=False):

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.archimedesifrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'archimedessymbol.svg', self.archimedesifrect)

    def callimachusif(self, place, painter, flag=False):
        dbprint('User.callimachusif', self)

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.callimachusifrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'callimachussymbol.svg', self.callimachusifrect)

    def phaleronif(self, place, painter, flag=False):
        dbprint('User.phaleronif', self)

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.phaleronifrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'phaleronsymbol.svg', self.phaleronifrect)

    def musaeumif(self, place, painter, flag=False):
        dbprint('User.musaeumif', self)

        x = self.x + place * 25
        y = self.y + 300

        if flag == True:
            y -= 12

        self.musaeumifrect = QRectF(x + 1, y + 1, 23, 23)

        self.Ptolemy.svg(painter, self.interfaceimgs + 'musaeumsymbol.svg', self.musaeumifrect)

    def clock(self, painter):
        dbprint('User.clock', self)

        self.clockrect = QRectF(self.x, self.y + self.h - 5, self.w, 25)

        painter.setPen(self.Ptolemy.pen('white'))
        painter.setFont(self.Ptolemy.font(18))

        # painter.drawRect(self.rect)

        painter.drawText(self.x, self.y + self.h - 5,
                         str([self.Ptolemy.sysTime(), self.Ptolemy.sysDate()]).replace("'", "").replace(",", ""))

    #####
    # Designate this space for modification for adding new buttons while running TODO
    #####

    # Make this use Philadelphos
    def cmdline(self, command):
        dbprint('User.cmdline', self)

        process = Popen(
            args=command,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()[0]

    def saveLog(self, logname, text):
        dbprint('User.saveLog', self)

        with open("/home/rendier/Ptolemy/include/logs/{}".format(logname), "a") as f:
            f.write(text)
            f.close()

    def netstat(self, interface):
        dbprint('User.netstat', self)

        netStats1 = psutil.net_io_counters(True)
        netTx = netStats1[interface][0]
        netRx = netStats1[interface][1]

        netStats2 = psutil.net_io_counters(True)
        nextnetTx = netStats2[interface][0]
        nextnetRx = netStats2[interface][1]

        inputTx = int(nextnetTx) - int(netTx)
        inputRx = int(nextnetRx) - int(netRx)

        if inputTx + inputRx > 0:
            return True
        elif inputTx + inputRx <= 0:
            return False

    def title(self, painter, title, x, y):
        dbprint('User.title', self)

        # if str(title).startswith("b'"):
        # 	self.title = str(title)[2:-1]
        # else:
        # 	self.title = str(title)

        self.titlex = self.x + x
        self.titley = self.y + y
        painter.setPen(self.Ptolemy.pen(self.color))
        painter.setBrush(self.Ptolemy.brush(self.color))
        painter.setFont(self.Ptolemy.font(14))
        upperpoints = [
            QPointF(self.titlex + 3, self.titley - 5),
            QPointF(self.titlex + 8, self.titley - 10),
            QPointF(self.titlex + (self.w / 3) * 2, self.titley - 10),
            QPointF(self.titlex + (self.w / 3) * 2 - 5, self.titley - 5),

        ]
        upper = QPolygonF(upperpoints)
        painter.drawPolygon(upper)
        lowerpoints = [
            QPointF(self.titlex + 3, self.titley),
            QPointF(self.titlex + 8, self.titley - 5),
            QPointF(self.titlex + self.w - 5, self.titley - 5),
            QPointF(self.titlex + self.w - 10, self.titley)
        ]
        lower = QPolygonF(lowerpoints)
        painter.drawPolygon(lower)

        painter.setPen(self.Ptolemy.pen('red'))
        painter.drawLine(self.titlex + 3, self.titley - 4, self.titlex + self.w - 5, self.titley - 4)

        painter.setPen(self.Ptolemy.pen('black'))
        painter.drawText(self.titlex + 10, self.titley - 2, title  )  # str(title)[2:-1])

        painter.setPen(self.Ptolemy.pen('white'))
        painter.drawText(self.titlex + 8, self.titley - 0, title  )  # str(title)[2:-1])

        pass

    def labelcur(self, painter, cx, cy, radius, start_angle, sweep_angle, label):
        dbprint('User.labelcur', self)

        # print "Lable Curve\n", painter, cx, cy, radius, start_angle, sweep_angle, label
        try:
            theta = 2.0 / (360.0 / sweep_angle) * pi / (len(label) - 1)
        except ZeroDivisionError:
            theta = pi / 180
        c = cos(theta)
        s = sin(theta)

        x = radius * cos(start_angle * (pi / 180.))
        y = radius * sin(start_angle * (pi / 180.))

        for i in label:
            # self.label(self.x + cx, self.y + cy, label[i])# .encode("utf8"))
            painter.drawText(x + cx, y + cy, i)

            t = x
            x = c * x - s * y
            y = s * t + c * y

    def arc(self, painter, x, y, radius, start_angle, sweep_angle):
        dbprint('User.arc', self)

        arcRect = QRectF(
            x - radius,
            y - radius,
            2 * radius + 1,
            2 * radius + 1
        )

        start_angle *= 16
        sweep_angle *= 16

        painter.drawArc(arcRect, start_angle, sweep_angle)
        
    def thread_inicator(self, state):
        
        pass