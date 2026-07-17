#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

class Tile:
	"""
	A tile on a map. It may or may not be blocked, and may or may not block sight.
	"""
	
	def __init__(self, blocked, block_sight=None, path=False, explored=False):
		self.blocked = blocked
		
		# By default, if a tile is blocked, it also blocks sight
		if block_sight is None:
			block_sight = blocked
			
		self.block_sight = block_sight
		
		self.path = path
		
		self.explored = explored
		
	def __str__(self):
		return "FIX THIS TILE STRING"
	
	def __repr__(self):
		return f"{self.__class__.__name__}(blocked={self.blocked}, block_sight={self.block_sight}, path={self.path}, explored={self.explored})"