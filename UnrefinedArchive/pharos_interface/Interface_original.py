#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSvg import *
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import *


from math import *
from random import randrange
from subprocess import Popen, PIPE, call
from OpenGL.GLUT import *

# SpectroSecurity moved to Archimedes — import via proper path
try:
    from Archimedes.SpectroSecurity import LiveSpectrogram as LS
except ImportError:
    LS = None  # stub — Archimedes.SpectroSecurity not available

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
			# self.command_input
			pass
		
		pass

class UserDisplay(QGraphicsItem):

	def __init__(self, parent=None):
		super(UserDisplay, self).__init__()
		QGraphicsItem.__init__(self)

		self.User = parent
		self.Ptolemy = self.User.Ptolemy
		print("USERDISPLAY PARENTS: ", self.User, self.Ptolemy)
		# print("USERDISPLAY RECT INSIDE: ", self.User.displayRect)

		# self.x = 15
		# self.y = self.Ptolemy.scene.height() - 400
		# self.w = 230
		# self.h = 300
		
		# Coordinates are proxy-relative (0,0 = top-left of User widget)
		self.x = 0
		self.y = 0
		self.w = self.User.w
		self.h = self.User.h

		self.centerx = self.w // 2 + 11
		self.centery = self.h // 2 + 11

		self.centerrect = QRectF(self.centerx - 75, self.centery - 75, 100, 100)

		self.rect = QRectF(0, 0, self.w, self.h)

		self.setAcceptHoverEvents(True)

		phila = self.Ptolemy.Philadelphos
		self.output = phila.setOutput if phila and hasattr(phila, "setOutput") else None
		self.interfaceimgs = self.Ptolemy.pharosImg
		self.media = self.Ptolemy.mediaDir
		self.scene = self.Ptolemy.scene

		self.MONITOR = False
		self.MINI = False

		self.screensaver = QTimer()
		self.screensaver.timeout.connect(self.switchMonitor)
		self.screensaver.setSingleShot(True)
		

		self.identity = "Pharos"
		self.cwd = "*".join(self.Ptolemy.cwd()[1:].split("/")[-3:])

		images = os.listdir(self.interfaceimgs)
		rand = randrange(len(images))
		self.bgimage = "nav_seal_200.png"  # ""nav_seal.jpg"#images[rand]

		# print("STARTING INDICATOR")
		# self.indicator = QGraphicsSvgItem(self.interfaceimgs + 'threading_indicator_red.svg', parent=self)
		# self.indicator.setPos(self.x + 10, self.y + 35)
		# self.indicator.setToolTip("Threading Indicator")
		# self.indicator.setScale(0.23)
		# self.indicator.mousePressEvent = self.output("This is the click of the indicator")
		# self.indicator.show()

		

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
		self.red = (255, 0, 0)
		self.darkRed = (128, 0, 0)
		self.green = (0, 255, 0)
		self.darkGreen = (0, 128, 0)
		self.blue = (0, 0, 255)
		self.cyan = (0, 255, 255)
		self.magenta = (255, 0, 255)
		self.yellow = (255, 255, 0)
		self.darkYellow = (128, 128, 0)
		self.darkBlue = (0, 0, 128)
		self.white = (255, 255, 255)
		self.black = (0, 0, 0)
		self.pink = (255, 200, 200)
		self.grey = (79, 79, 79)
		GLFonts = [
			GLUT_BITMAP_8_BY_13,
			GLUT_BITMAP_9_BY_15,
			GLUT_BITMAP_TIMES_ROMAN_10,
			GLUT_BITMAP_HELVETICA_10,
			GLUT_BITMAP_HELVETICA_12
		]
		
		# NOT added to scene directly — setParentItem(_pharos_proxy) in Ptolemy3
		self.setZValue(1)

	# def __del__(self):
	#     del self.indicator

	def hoverEnterEvent(self, event):
		print('hoverEnterEvent')

		self.User.displayEnter()

		if not self.MINI:
			self.MONITOR = False
			if self.screensaver.isActive():
				self.screensaver.stop()

		pass

	def hoverLeaveEvent(self, event):

		self.User.displayLeave()

		self.setToolTip("Pharos Interface")
		if not self.MINI:
			self.screensaver.start(10000)

		pass

	def boundingRect(self):

		return self.rect

	def paint(self, painter, option, widget):

		self.refresh()

		painter.setPen(self.Ptolemy.pen(self.color))
		painter.setBrush(self.Ptolemy.brush('black'))
		painter.setFont(self.Ptolemy.font(12))
		# painter.drawRect(self.rect)
		# painter.drawRect(self.x + 2, self.y + 2, self.w - 4, self.h - 4)

		# self.renderer.render(painter, QRectF(self.centerx - 100, self.centery - 100, 200, 200))

		self.title(painter, self.name, 0, 15)
		# self.title(painter, self.platform, 1, 28)
		self.title(painter, self.user, 1, 28)#43)
		# self.title(painter, self.nodename, 1, 58)

		if self.MONITOR == True:
			self.procMonitor(painter)
		# self.procMonitor(painter)
		# self.systemTray(painter)

		self.archtype(painter, self.identity)

		# self.Ptolemy.scene.addItem(self)
		pass

	def mousePressEvent(self, event):
		super().mousePressEvent(event)
		self.User._restart_mini_timer()

	def set_mini(self, mini: bool):
		self.MINI = mini
		if mini:
			self.MONITOR = True
			if self.screensaver.isActive():
				self.screensaver.stop()
		else:
			self.MONITOR = False
			self.screensaver.start(10000)
		self.update(self.rect)

	def changeIdentity(self, identity):
		self.identity = identity
		self.update(self.rect)

	def archtype(self, painter, persona=None):

		painter.setPen(self.Ptolemy.pen('white'))
		painter.setFont(self.Ptolemy.font(18))
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

		radius = int(self.User.display.height() / 2.3)
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
			painter.setFont(self.Ptolemy.font(18))
			radius = int(self.User.display.height() / 2.25)
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

		self.name = str(self.Ptolemy.name)
		self.user = str(self.Ptolemy.user)[2:-1]
		self.platform = str(self.Ptolemy.platform)[2:-1]
		self.nodename = str(self.Ptolemy.nodename)[2:-1]

		self.time = self.Ptolemy.sysTime()
		self.date = self.Ptolemy.sysDate()

		if self.identity == 'Pharos':
			self.color = 'darkcyan'

		elif self.identity == 'Alexandria':# in self.Ptolemy.PharosMenu.crumbs:
			self.color = 'magenta'

		elif self.identity == 'Anaximander':
			self.color = 'orange'

		elif self.identity == 'Archimedes':# in self.Ptolemy.PharosMenu.crumbs:
			self.color = 'darkblue'

		elif self.identity == 'Callimachus':# in self.Ptolemy.PharosMenu.crumbs:
			self.color = 'darkgreen'

		elif self.identity == 'Kryptos':
			self.color = 'purple'

		elif self.identity == 'Phaleron':# in self.Ptolemy.PharosMenu.crumbs:
			self.color = 'grey'

		elif self.identity == 'Mouseion':# in self.Ptolemy.PharosMenu.crumbs:
			self.color = 'white'

		elif self.identity == 'Tesla':
			self.color = 'darkred'

		

		self.update(self.rect)

	def switchMonitor(self):

		self.MONITOR = True

	def procMonitor(self, painter):

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
		if int(self.w * 0.08) % 2 != 0:
			kwidth = int(self.w * 0.08) + 2
		else:
			kwidth = int(self.w * 0.08)
			
		centerAdjust = (kwidth + 1) / 2
		painter.setBrush(self.Ptolemy.brush('white'))
		# self.KERNEL = painter.drawEllipse(self.centerx - 10, self.centery - 10, 19, 19)
		self.KERNEL = painter.drawEllipse(int(self.centerx) - int(centerAdjust), int(self.centery) - int(centerAdjust), int(kwidth), int(kwidth))
		# Cpu
		for i in range(self.cpuCount):
			color = self.colordict[self.colors[i + 3]]
			painter.setPen(self.Ptolemy.pen(color, 5))
			exec("self.CPU{0} = self.arc(painter, self.centerx, self.centery, 30, i * self.cpuAngle, self.cpuAngle * (self.cpuPercent[i] / 100.))".format
					(i))

		# Ram
		painter.setPen(self.Ptolemy.pen('cyan', 5))
		self.RAM = self.arc(painter, self.centerx, self.centery, 40, 0, self.memAngle)

		# VMEM
		self.VMEM = self.arc(painter, self.centerx, self.centery, 50, 0, self.swapAngle)

		# GPU
		self.GPU = self.arc(painter, self.centerx, self.centery, 60, 0, 360)

		# Net
		for i in range(len(self.netIF)):
			color = self.colordict[self.colors[i + 1]]
			# Placeholder
			painter.setPen(self.Ptolemy.pen(color, 1))
			# self.arc(painter, self.centerx, self.centery, 60, i * self.netAngle, self.netAngle)
			painter.setPen(self.Ptolemy.pen(color, 5))
			if self.netstat(self.netIF[i]) == True:
				exec("self.NET{0} = self.arc(painter, self.centerx, self.centery, 70, i * self.netAngle, self.netAngle)".format(
					i))

		# Proc FIX THIS for different colors according to status and place Zombie or Dead processes perm TODO
		painter.setPen(self.Ptolemy.pen('cyan', 23))
		for i in range(self.procNum):
			try:
				procPercent = self.procList[i].cpu_percent()
			except psutil.NoSuchProcess:
				pass
			else:
				if procPercent > 0:
					exec("self.PROC{0} = self.arc(painter, self.centerx, self.centery, 80, i * self.procAngle, self.procAngle)".format(
						i))

		pass

	def cmdline(self, command):

		process = Popen(
			args=command,
			stdout=PIPE,
			stderr=PIPE,
			shell=True
		)
		return process.communicate()[0]

	def netstat(self, interface):

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

		# if str(title).startswith("b'"):
		# 	self.title = str(title)[2:-1]
		# else:
		# 	self.title = str(title)

		self.titlex = self.x + x
		self.titley = self.y + y
		painter.setPen(self.Ptolemy.pen(self.color))
		painter.setBrush(self.Ptolemy.brush(self.color))
		painter.setFont(self.Ptolemy.font(18))
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
			painter.drawText(int(x + cx), int(y + cy), i)

			t = x
			x = c * x - s * y
			y = s * t + c * y

	def arc(self, painter, x, y, radius, start_angle, sweep_angle):

		arcRect = QRectF(
			x - radius,
			y - radius,
			2 * radius + 1,
			2 * radius + 1
		)

		start_angle *= 16
		sweep_angle *= 16

		painter.drawArc(arcRect, int(start_angle), int(sweep_angle))

class User(QWidget):

	def __init__(self, parent=None):
		super(User, self).__init__(parent)
		QWidget.__init__(self)

		self.Ptolemy = parent
		print("USER PARENT: ", self.Ptolemy)
		

		self.styles = self.Ptolemy.stylesheet

		self.x = int(self.Ptolemy.scene.width() / 2) - 76
		self.y = int(self.Ptolemy.scene.height() / 2) - 175
		self.w = 225
		self.h = 350
		self.centerx = self.x + self.w // 2
		self.centery = self.y + self.h // 2

		self.setGeometry(self.x, self.y, self.w, self.h)

		self.setStyleSheet(self.styles)
		self.setStyleSheet("QWidget { background-color: transparent; } ")

		phila = self.Ptolemy.Philadelphos
		self.output = phila.setOutput if phila and hasattr(phila, "setOutput") else None
		self.interfaceImg = self.Ptolemy.pharosImg
		print("PATH:", self.interfaceImg)
		self.mediaDir = self.Ptolemy.mediaDir
		self.scene = self.Ptolemy.scene

		self.MONITOR = False

		# self.procTimer = QTimer()
		# self.procTimer.timeout.connect(self.switchMonitor)
		# self.procTimer.setSingleShot(True)

		self.identity = "Pharos"
		self.cwd = "*".join(self.Ptolemy.cwd()[1:].split("/")[-3:])

		self.setToolTip(self.identity + " Interface")
		images = os.listdir(self.interfaceImg)
		rand = randrange(len(images))
		self.bgImage = "nav_seal_200.png"

		

		# self.enterEvent = self.displayEnter

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

		self.red = (255, 0, 0)
		self.darkRed = (128, 0, 0)
		self.green = (0, 255, 0)
		self.darkGreen = (0, 128, 0)
		self.blue = (0, 0, 255)
		self.cyan = (0, 255, 255)
		self.magenta = (255, 0, 255)
		self.yellow = (255, 255, 0)
		self.darkyellow = (128, 128, 0)
		self.darkBlue = (0, 0, 128)
		self.white = (255, 255, 255)
		self.black = (0, 0, 0)
		self.pink = (255, 200, 200)
		self.grey = (79, 79, 79)

		GLFonts = [
			GLUT_BITMAP_8_BY_13,
			GLUT_BITMAP_9_BY_15,
			GLUT_BITMAP_TIMES_ROMAN_10,
			GLUT_BITMAP_HELVETICA_10,
			GLUT_BITMAP_HELVETICA_12
		]

		self.sysTrayList = ['display',
							'power',
							'alexandria',
							'archimedes',
							'anaximander',
							'callimachus',
							'kryptos',
							'mouseion',
							'phaleron',
							'pharos',
							'tesla',
							'treasureHunt',
							'navigation',
							'core',
							'earth',
							'graph',
							'stanDev',
							'dbCPanel',
							'library',
							'wikiGroup',
							'clock'
							]

		self.FS = 44100  # Hz
		self.CHUNKSZ = 1024  # samples
		

		self.initUi()

		self._mini = False
		self._mini_timer = QTimer(self)
		self._mini_timer.setInterval(30000)
		self._mini_timer.setSingleShot(True)
		self._mini_timer.timeout.connect(self.miniaturize)
		self._mini_timer.start()

	def __del__(self):

		pass

	def initUi(self):

		self.btnSize = 23

		# self.renderer = QSvgRenderer(self.interfaceImg + 'nav-seal.svg')
	 

		self.display = QSvgWidget(self.interfaceImg + 'nav-seal.svg', parent=self)
		self.display.setFixedSize(self.btnSize * 13, self.btnSize * 13)
		self.frame = self.frameGeometry()
		self.displayRect = QRect(self.frameGeometry().x(), self.frameGeometry().y(), self.display.rect().width(), self.display.rect().height())
		# self.displayRect = self.display.rect()
		# print("DISPLAY RECT: ", self.displayRect)

		self.UserDisplay = UserDisplay(self)
		# self.UserDisplay.setZValue(0)

		self.buildButtons()

		self.clock = QLabel(str(self.Ptolemy.timeStamp()))
		self.clock.setFixedHeight(self.btnSize)
		# self.clock.setFixedSize(230, self.btnSize)
		self.clock.setToolTip('Clock')
		self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.layout = QGridLayout(self)

		self.originalLayout()

		self.setLayout(self.layout)

		self.clockTimer = QTimer(self)
		self.clockTimer.setInterval(1000)
		self.clockTimer.timeout.connect(self.clockAnimate)
		self.clockTimer.start()

		self.spectro = None
		self.mic = None
		if LS is not None:
			self.spectro = LS.SpectrogramWidget(self)
			self.spectro.read_collected.connect(self.spectro.update)
			self.spectro.setGeometry(self.x + self.w + 30, self.y + self.h - 85, 50, 50)
			self.spectro.setWindowFlags(Qt.WindowType.CustomizeWindowHint)
			self.spectro.setStyleSheet(self.styles)
			_spectro_proxy = self.scene.addWidget(self.spectro)
			_spectro_proxy.setZValue(3)

			self.mic = LS.MicrophoneRecorder(self.spectro.read_collected)
			interval = self.FS / self.CHUNKSZ
			t = QTimer(self)
			t.timeout.connect(self.mic.read)
			t.start(int(1000 / interval))

		self.indicator = QLabel(parent=self)
		self.indicatorIcon = QPixmap(self.interfaceImg + 'indicator-ball.gif')
		self.indicator.setPixmap(self.indicatorIcon)
		self.indicator.setGeometry(self.x + 10, self.y + 35, 75, 75)
		self.indicator.mousePressEvent = self.output("This is the click of the Thread Indicator")

		self.scene.addWidget(self.indicator)

		self.indicator.show()
		self.indicator.setVisible(True)
		print("INDICATOR VISIBLE:", self.indicator.isVisible(), self.indicator, self.indicatorIcon)
		
	def clockAnimate(self):
		# print('Clock Animate')
		self.layout.removeWidget(self.clock)
		self.clock.setText(str(self.Ptolemy.timeStamp()))
		del(self.clockBtn)
		self.clockBtn = QLabel(str(self.Ptolemy.timeStamp()))
		self.clockBtn.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.clockBtn.setFixedHeight(self.btnSize)
		self.clockBtn.setToolTip('Clock  [CTRL+D]')
		self.layout.addWidget(self.clockBtn, 12, 0, 1, 10)

	def displayEnter(self):
		
		self.display.load(self.interfaceImg + 'nav-seal-over.svg')

	def displayLeave(self):
		
		self.display.load(self.interfaceImg + 'nav-seal.svg')

	def mouseMoveEvent(self, event):
		super().mouseMoveEvent(event)

	def mousePressEvent(self, event):
		super().mousePressEvent(event)
		self._restart_mini_timer()

	def _restart_mini_timer(self):
		if self._mini:
			self.restore()
		self._mini_timer.stop()
		self._mini_timer.start()

	def miniaturize(self):
		self._mini = True
		self.display.hide()
		for name in self.sysTrayList[1:-1]:
			btn = getattr(self, name + 'Btn', None)
			if btn:
				btn.hide()
		self.UserDisplay.set_mini(True)

	def restore(self):
		self._mini = False
		self.display.show()
		for name in self.sysTrayList[1:-1]:
			btn = getattr(self, name + 'Btn', None)
			if btn:
				btn.show()
		self.UserDisplay.set_mini(False)

	def buildButtons(self):
		self.clockBtn = QLabel(str(self.Ptolemy.timeStamp()))
		self.clockBtn.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.clockBtn.setFixedHeight(self.btnSize)
		self.clockBtn.setToolTip('Clock  [CTRL+D]')
		# self.layout.addWidget(self.clockBtn, 12, 0, 1, 10)

		self.blankBtn = QSvgWidget(self.interfaceImg + 'blank.svg')
		self.blankBtn.setFixedSize(self.btnSize, self.btnSize)

		self.powerBtn = QSvgWidget(self.interfaceImg + "power.svg")
		self.powerBtn.setFixedSize(self.btnSize, self.btnSize)
		self.powerBtn.setToolTip("Exit Program  [CTRL+Q]")
		self.powerBtn.mousePressEvent = self.power

		self.archimedesBtn = QSvgWidget(self.interfaceImg + 'archimedessymbol.svg')
		self.archimedesBtn.setFixedSize(self.btnSize, self.btnSize)
		self.archimedesBtn.setToolTip("Archimedes Menu  [CTRL+A]")
		self.archimedesBtn.mousePressEvent = self.archimedesMenu

		self.anaximanderBtn = QSvgWidget(self.interfaceImg + 'anaximandersymbol.svg')
		self.anaximanderBtn.setFixedSize(self.btnSize, self.btnSize)
		self.anaximanderBtn.setToolTip("Anaximander Menu  [CTRL+N]")
		self.anaximanderBtn.mousePressEvent = self.anaximanderMenu

		self.alexandriaBtn = QSvgWidget(self.interfaceImg + 'alexandriasymbol.svg')
		self.alexandriaBtn.setFixedSize(self.btnSize, self.btnSize)
		self.alexandriaBtn.setToolTip('Alexandria  [CTRL+V]')
		self.alexandriaBtn.mousePressEvent = self.alexandriaMenu

		self.callimachusBtn = QSvgWidget(self.interfaceImg + 'callimachussymbol.svg')
		self.callimachusBtn.setFixedSize(self.btnSize, self.btnSize)
		self.callimachusBtn.setToolTip('Callimachus Menu  [CTRL+L]')
		self.callimachusBtn.mousePressEvent = self.callimachusMenu

		self.kryptosBtn = QSvgWidget(self.interfaceImg + 'kryptossymbol.svg')
		self.kryptosBtn.setFixedSize(self.btnSize, self.btnSize)
		self.kryptosBtn.setToolTip('Kryptos Menu  [CTRL+K]')
		self.kryptosBtn.mousePressEvent = self.kryptosMenu

		self.mouseionBtn = QSvgWidget(self.interfaceImg + 'mouseionsymbol.svg')
		self.mouseionBtn.setFixedSize(self.btnSize, self.btnSize)
		self.mouseionBtn.setToolTip('Mouseion Menu  [CTRL+M]')
		self.mouseionBtn.mousePressEvent = self.mouseionMenu

		self.phaleronBtn = QSvgWidget(self.interfaceImg + 'phaleronsymbol.svg')
		self.phaleronBtn.setFixedSize(self.btnSize, self.btnSize)
		self.phaleronBtn.setToolTip('Phaleron Menu  [CTRL+P]')
		self.phaleronBtn.mousePressEvent = self.phaleronMenu

		self.pharosBtn = QSvgWidget(self.interfaceImg + 'pharossymbol.svg')
		self.pharosBtn.setFixedSize(self.btnSize, self.btnSize)
		self.pharosBtn.setToolTip('Pharos Menu  [CTRL+H]')
		self.pharosBtn.mousePressEvent = self.pharosMenu

		self.teslaBtn = QSvgWidget(self.interfaceImg + 'teslasymbol.svg')
		self.teslaBtn.setFixedSize(self.btnSize, self.btnSize)
		self.teslaBtn.setToolTip('Tesla Menu  [CTRL+T]')
		self.teslaBtn.mousePressEvent = self.teslaMenu

		self.treasureHuntBtn = QSvgWidget(self.interfaceImg + 'treasurehunt.svg')
		self.treasureHuntBtn.setFixedSize(self.btnSize, self.btnSize)
		self.treasureHuntBtn.setToolTip('Treasure Hunt  [CTRL+F]')
		self.treasureHuntBtn.mousePressEvent = self.Ptolemy.openSearch

		self.navigationBtn = QSvgWidget(self.interfaceImg + 'navigation.svg')
		self.navigationBtn.setFixedSize(self.btnSize, self.btnSize)
		self.navigationBtn.setToolTip('Navigation Assistant')
		self.navigationBtn.mousePressEvent = self.Ptolemy.openNavigation

		self.coreBtn = QSvgWidget(self.interfaceImg + 'procmonitor.svg')
		self.coreBtn.setFixedSize(self.btnSize, self.btnSize)
		self.coreBtn.setToolTip('Core')
		self.coreBtn.mousePressEvent = self.Ptolemy.openCore

		self.earthBtn = QSvgWidget(self.interfaceImg + 'earth.svg')
		self.earthBtn.setFixedSize(self.btnSize, self.btnSize)
		self.earthBtn.setToolTip('Earth')
		self.earthBtn.mousePressEvent = self.Ptolemy.openEarth

		self.graphBtn = QSvgWidget(self.interfaceImg + 'graphplot.svg')
		self.graphBtn.setFixedSize(self.btnSize, self.btnSize)
		self.graphBtn.setToolTip('GraphPlot')
		self.graphBtn.mousePressEvent = self.Ptolemy.openGraphPlot

		self.stanDevBtn = QSvgWidget(self.interfaceImg + 'standarddeviation.svg')
		self.stanDevBtn.setFixedSize(self.btnSize, self.btnSize)
		self.stanDevBtn.setToolTip('Standard Deviation')
		self.stanDevBtn.mousePressEvent = self.Ptolemy.openStanDev
		
		self.dbCPanelBtn = QSvgWidget(self.interfaceImg + 'databasecpanel.svg')
		self.dbCPanelBtn.setFixedSize(self.btnSize, self.btnSize)
		self.dbCPanelBtn.setToolTip('Database Control Panel')
		self.dbCPanelBtn.mousePressEvent = self.Ptolemy.openDbCPanel
		
		self.libraryBtn = QSvgWidget(self.interfaceImg + 'library.svg')
		self.libraryBtn.setFixedSize(self.btnSize, self.btnSize)
		self.libraryBtn.setToolTip('Read Library Books')
		self.libraryBtn.mousePressEvent = self.Ptolemy.openLibrary

		self.wikiGroupBtn = QSvgWidget(self.interfaceImg + 'wikigroup.svg')
		self.wikiGroupBtn.setFixedSize(self.btnSize, self.btnSize)
		self.wikiGroupBtn.setToolTip('Read Wikipedia Books')
		self.wikiGroupBtn.mousePressEvent = self.Ptolemy.openWikiGroup

	def clearLayout(self):
		print("Clear Layout")

		for i in self.sysTrayList[2:-1]:
			code = 'self.{0}Btn.deleteLater()'.format(i)
			# print(code)
			exec(code)

		self.buildButtons()

		self.layout.addWidget(self.pharosBtn, 11, 1, 1, 1)

	def originalLayout(self):

		self.displayItem = self.layout.addWidget(self.display, 0, 0, 10, 10)
		self.powerItem = self.layout.addWidget(self.powerBtn, 11, 0, 1, 1)
		self.alexandriaItem = self.layout.addWidget(self.alexandriaBtn, 11, 1, 1, 1)
		self.archimedesItem = self.layout.addWidget(self.archimedesBtn, 11, 2, 1, 1)
		self.anaximanderItem = self.layout.addWidget(self.anaximanderBtn, 11, 3, 1, 1)
		self.callimachusItem = self.layout.addWidget(self.callimachusBtn, 11, 4, 1, 1)
		self.kryptosItem = self.layout.addWidget(self.kryptosBtn, 11, 5, 1, 1)
		self.mouseionItem = self.layout.addWidget(self.mouseionBtn, 11, 6, 1, 1)
		self.phaleronItem = self.layout.addWidget(self.phaleronBtn, 11, 7, 1, 1)
		self.pharosItem = self.layout.addWidget(self.pharosBtn, 11, 8, 1, 1)
		self.teslaItem = self.layout.addWidget(self.teslaBtn, 11, 9, 1, 1)
		self.clockItem = self.layout.addWidget(self.clock, 12, 0, 1, 10)

	def power(self, event):
		self.Ptolemy.close()

	def svgSwitch(self, position):
		
		pass
	
	def archimedesMenu(self, event):
		print('Archimedes')
		self.UserDisplay.changeIdentity('Archimedes')
		self.clearLayout()
		self.layout.addWidget(self.graphBtn, 11, 2, 1, 1)

		pass

	def alexandriaMenu(self, event):
		print('Alexandria')
		self.UserDisplay.changeIdentity('Alexandria')
		self.clearLayout()
		self.layout.addWidget(self.coreBtn, 11, 2, 1, 1)
		self.layout.addWidget(self.earthBtn, 11, 3, 1, 1)

		pass

	def anaximanderMenu(self, event):
		print('Anaximander')

		self.clearLayout()
		self.UserDisplay.changeIdentity('Anaximander')
		self.layout.addWidget(self.navigationBtn, 11, 2, 1, 1)
		pass

	def callimachusMenu(self, event):
		print('Callimachus')
		self.UserDisplay.changeIdentity('Callimachus')
		self.clearLayout()
		self.layout.addWidget(self.dbCPanelBtn, 11, 2, 1, 1)

		pass

	def kryptosMenu(self, event):
		print('Kryptos')
		self.UserDisplay.changeIdentity('Kryptos')
		self.clearLayout()

		pass

	def mouseionMenu(self, event):
		print('Mouseion')
		self.UserDisplay.changeIdentity('Mouseion')
		self.clearLayout()
		self.layout.addWidget(self.libraryBtn, 11, 2, 1, 1)
		self.layout.addWidget(self.wikiGroupBtn, 11, 3, 1, 1)

		pass

	def phaleronMenu(self, event):
		print('Phaleron')
		self.PHAROS_MENU = False
		self.clearLayout()

		self.UserDisplay.changeIdentity('Phaleron')
		self.layout.addWidget(self.treasureHuntBtn, 11, 2, 1, 1)




		pass

	def pharosMenu(self, event):
		print('Pharos')

		self.UserDisplay.changeIdentity('Pharos')
		self.clearLayout()
		self.originalLayout()

		pass

	def teslaMenu(self, event):
		print('Tesla')
		self.UserDisplay.changeIdentity('Tesla')
		self.clearLayout()

		pass

def main():

	app = QApplication(sys.argv)
	app.setApplicationName('Interface')
	# sys.setrecursionlimit(10000)
	Iface = User()

	
	# Ptolemy.setWindowFlags(Ptolemy.windowFlags() | Qt.FramelessWindowHint)
	# Ptolemy.setWindowState(Qt.WindowMaximized)
	# Ptolemy.setWindowState(QtCore.Qt.WindowFullScreen)
	Iface.show()
	# sys.stdout = OutLog(Ptolemy.Philadelphos.PtolOut, color='white')
	# sys.stderr = OutLog(Ptolemy.Philadelphos.PtolOut, color='red')

	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec())

if __name__ == "__main__":
	main()
