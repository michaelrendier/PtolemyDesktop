#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *

from PyQt6.QtSvgWidgets import *
from PyQt6.QtWidgets import *

from PyQt6.QtMultimedia import *



import sys, os



class Earth(QGraphicsItem):
	
	def __init__(self, parent=None):
		super(Earth, self).__init__(parent)
		QGraphicsItem.__init__(self)
		
		self.Ptolemy = parent
		print("EARTH PARENT: ", self.Ptolemy)
		
		
		
	def __del__(self):
		
		pass
	
	def initUi(self):
		
		pass
	
	def paint(self, painter)