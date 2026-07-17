#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'



class Item:
	
	def __init__(self, use_function=None, targeting=False, targeting_message=None, **kwargs):
		self.use_function = use_function
		self.targeting = targeting
		self.targeting_message = targeting_message
		self.function_kwargs = kwargs
		
	def __str__(self):
		return self.__repr__()
	
	def __repr__(self):
		return f"{self.__class__.__name__}(use_function={self.use_function.__name__}, targeting={self.targeting}, targeting_message={repr(self.targeting_message)}, kwargs={self.function_kwargs})"