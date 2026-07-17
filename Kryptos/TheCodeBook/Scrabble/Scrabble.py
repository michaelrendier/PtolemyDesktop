#!/usr/bin/python3
# -*- coding: utf-8 -*-
__all__ = []
__version__ = '3.6.6'
__author__ = 'rendier'

import string




class Scrabble(object):
	
	def __init__(self, parent=None):
		super(Scrabble, self).__init__(self)
		
		self.transtable = self.createList()
	
	def createList(self, translist):
		original = string.ascii_lowercase
		nextstr = original
		translist = []
		for i in range(26):
			print("I:", i)
			if i == 0:
				translist.append(nextstr)
				pass
			else:
				for j in range(i):
					nextstr = nextstr[-1] + nextstr[:-1]
				print("NEXTSTR:", nextstr)
			translist.append(nextstr)
			nextstr = original
			
		nextstr = reversed(original)
		
		for i in range(26)
		
		
thisone = Scrabble()