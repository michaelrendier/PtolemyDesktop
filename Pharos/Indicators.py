#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSvg import *
from PyQt6.QtWidgets import *

class ThreadIndicator(QGraphicsItem):
	"""Thread Indicator
	geometry: [x, y, width, height]
	"""
	
	def __init__(self, geometry, parent=None):
		super(ThreadIndicator, self).__init__(parent)
		
		self.parent = parent
		print("INDICATOR PARENT:", self.parent)
		
		self.geometry = geometry
		
	
	def paint(self, painter, option, widget):
		
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.indicator = QIcon(PTOL_ROOT + "/images/Pharos/indicator-ball.png", parent=self)
		
	