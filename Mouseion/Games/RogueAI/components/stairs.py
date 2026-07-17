#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'




class Stairs:
	DOWN = +1
	UP = -1
	
	def __init__(self, floor, direction=DOWN):
		self.floor = floor + direction
		self.direction = direction
		
	def __str__(self):
		return self.__repr__()
	
	def __repr__(self):
		return f"{self.__class__.__name__}(floor={self.floor}, direction={self.direction})"