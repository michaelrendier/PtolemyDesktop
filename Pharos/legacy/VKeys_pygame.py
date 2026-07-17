#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pygame

from include.virtualkeyboard.virtualKeyboard import VirtualKeyboard


class VirtualKeys(QWidget):
	
	def __init__(self, parent=None):
		super(VirtualKeys, self).__init__(parent)
		
		self.parent = parent
		
		pygame.display.init()
		size = 800, 450
		screen = pygame.display.set_mode(size, pygame.NOFRAME)
		self.keyboard = VirtualKeyboard(screen)
		self.userinput = self.keyboard.run()
		
	def get_input(self):
		return self.userinput