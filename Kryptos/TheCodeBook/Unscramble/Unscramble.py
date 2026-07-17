#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtSvg import *

import json
import itertools as it


class Unscramble(object):
	
	def __init__(self, parent=None):
		super(Unscramble, self).__init__()
		
		self.parent = parent
		
		# Gather unscrambling data
		self.string = input("Input available letters # ").lower()
		self.length = int(input("How many letters is the answer # "))
		self.repeatletters = input("Can letters be repeated? (y/n) # ").lower()
		self.sort = input("Are letters already present? (y/n) # ").lower()
		
		self.words = {}
		
		with open("words_dictionary.json", 'r') as file:
			self.words = json.load(file)
			file.close()
			
		# print("Processing")
		
		if self.repeatletters == 'n' or self.repeatletters == 'no':
			# print("No Repeating Letters")
			self.answer = self.norepeat(self.string, self.length)
		
		else:
			# print("Repeating Letters")
			self.answer = self.repeat(self.string, self.length)
			
		if self.sort == 'n' or self.sort == 'no':
			# print("No Hint Letters")
			print(self.answer)
			
		elif self.sort == 'y' or self.sort == 'yes':
			# print("Hint Letters")
			self.hintletters = input("What letters are present? Use * for unknown letters: ")
			print(self.hints(self.hintletters))

	def norepeat(self, string, length):
		
		self.wordlist = sorted(set(["".join(i) for i in it.permutations(string, length) if "".join(i) in self.words]))
		
		return self.wordlist

	def repeat(self, string, length):
		
		self.wordlist = sorted(set([''.join(i) for i in it.product(string, repeat=length) if ''.join(i) in self.words]))
		
		return self.wordlist
	

	def hints(self, hintletters):
		
		self.letters = {}
		self.shortanswer = []
		
		for i in range(len(hintletters)):
			if hintletters[i] != "*":
				self.letters[i] = hintletters[i]
		print("LETTERS:", self.letters)
		
		for i in self.answer:
			addword = []
			for j in self.letters:
				if i[j] == self.letters[j]:
					addword.append("yes")
				else:
					addword.append("no")
			if 'no' not in addword:
				self.shortanswer.append(i)
				
		return self.shortanswer

answer = Unscramble()

