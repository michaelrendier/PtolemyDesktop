#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import os, sys
from colorama import Fore, Back, Style
from Pharos.Commandow import Stamps
import cmd


class Tools(object):
	
	def __init__(self, parent=None):
		super(Tools, self).__init__()
		
		self.parent = parent
		print("TOOLS PARENT:", self.parent)
		pass

	def shape_up(self, shape, data):
		return dict(zip(shape, data))
	
	def printxy(self, x, y, text):
		
		if "\n" in text:
			text = text.split("\n")
			for i in range(len(text)):
				sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text[i]))
				sys.stdout.flush()
				x += 1
		else:
			sys.stdout.write(u"\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text))
			sys.stdout.flush()
	
	def stamp(self, data):
		
		returned = []
		try:
			data[0] + 0
			
			for i in range(len(data)):
				returned.append(data[i])
			returned.append("\n")
		
		except TypeError:
			
			for i in range(len(data)):
				for j in range(len(data[i])):
					returned.append(data[i][j])
				returned.append("\n")
		
		return "".join(returned)
	
	def stamp_zip(self, mapping, shape):
		tempList = []
		for line in shape:
			for char in line:
				tempList.append(char)
				
		return dict(zip(mapping, tempList))


class Window(object):
	
	def __init__(self, x, y, width, height, style="regular", color='blue', parent=None):
		super(Window, self).__init__()
		
		self.parent = parent
		print("WINDOW PARENT:", self.parent)
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.style = style
		self.color = color
		self.shape = {}
		self.vert = []
		self.hor = []
		
		self.set_style(self.style)
		self.initWin(self.x, self.y, self.width, self.height)
		
		pass
	
	def initWin(self, x, y, height, width):
		
		width *= 2
		self.wincolor = None
		print("COLOR:", self.color)
		code = f'self.wincolor = Fore.{self.color.upper()}'
		print("CODE:", code)
		exec(code)
		print("WINCOLOR:", self.wincolor)
		self.printxy(x, y, self.wincolor + self.shape['tl'] + Style.RESET_ALL)
		self.printxy(x, y + 1, self.wincolor + self.shape['hor'] * (width - 2) + Style.RESET_ALL)
		self.printxy(x, y + width - 1, self.wincolor + self.shape['tr'] + Style.RESET_ALL)

		print_x = x + 1
		for i in range(height - 2):
			self.printxy(print_x, y, self.wincolor + self.shape['vert'] + " " * (width - 2) + self.shape['vert'] + Style.RESET_ALL)
			print_x += 1

		self.printxy(x + height - 1, y, self.wincolor + self.shape['bl'] + Style.RESET_ALL)
		self.printxy(x + height - 1, y + 1, self.wincolor + self.shape['hor'] * (width - 2) + Style.RESET_ALL)
		self.printxy(x + height - 1, y + width - 1, self.wincolor + self.shape['br'] + Style.RESET_ALL)
		
		pass
	
	def printxy(self, x, y, text):
		
		sys.stdout.write(f"\x1b7\x1b[{x};{y}f{text}\x1b8")
		sys.stdout.flush()
	
	def set_style(self, style):
		#regular, bold, double
		print("STYLE:", style)
		code = f'self.hor = Stamps.{style}_h'
		exec(code)
		code = f'self.vert = Stamps.{style}_v'
		exec(code)
		code = f'self.shape = self.parent.tools.stamp_zip(Stamps.shape_3x3, Stamps.{style}_shape)'
		exec(code)
		self.shape['hor'] = self.hor[0]
		self.shape['vert'] = self.vert[0]
		print("STYLE SHAPE:", self.shape)
		print("HOR VERT:", self.hor, self.vert)
	
		
		
class Commandow(object):
	
	def __init__(self, parent=None):
		super(Commandow, self).__init__()
		
		self.parent = parent
		self.tools = Tools(parent=self)
		
		self.attempt = Window(11, 6, 10, 10, parent=self)
		
	def shelf_screen(self, window):
		
		pass
		
		
		
if __name__ == '__main__':
	
	Manager = Commandow()



# if [ "$color_prompt" = yes ]; then
#     #PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
#     PS1="\[\033[25;0f${debian_chroot:+($debian_chroot)}\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "
# else
#     #PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
#     PS1="\[\033[25;0f${debian_chroot:+($debian_chroot)}\]\u@\h:\w\$ "
