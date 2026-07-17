#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'




class Level:
	
	def __init__(self, current_level=1, current_xp=0, level_up_base=200, level_up_factor=150):
		self.current_level = current_level
		self.current_xp = current_xp
		self.level_up_base = level_up_base
		self.level_up_factor = level_up_factor
		
	def __str__(self):
		return self.__repr__()
	
	def __repr__(self):
		return f"{self.__class__.__name__}(current_level={self.current_level}, current_xp={self.current_xp}, level_up_base={self.level_up_base})"
		
	@property
	def experience_to_next_level(self):
		return self.level_up_base + self.current_level * self.level_up_factor
	
	def add_xp(self, xp):
		self.current_xp += xp
		
		if self.current_xp > self.experience_to_next_level:
			self.current_xp -= self.experience_to_next_level
			self.current_level += 1
			
			return True
		
		else:
			return False