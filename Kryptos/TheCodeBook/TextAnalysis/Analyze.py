#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'




class TextAnalyze(object):
	
	def __init__(self, text, parent=None):
		super(TextAnalyze, self).__init__()
		
		self.text = text
		self.parent = parent
		
		self.textcount = self.chr_count(self.text)
		
		
	def chr_count(self, text):
		
		for i in set(text):
			self.textcount[i] = text.count(i)
			
		return