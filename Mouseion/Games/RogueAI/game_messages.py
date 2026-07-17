#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import tcod as libtcod

import textwrap

class Message:
	
	def __init__(self, text, color=libtcod.white):
		self.text = text
		self.color = color
		
	def __str__(self):
		return "FIX THIS MESSAGE STRING"
	
	def __repr__(self):
		return f"{self.__class__.__name__}(text='{self.text}', color={self.color}))"
		
class MessageLog:
	
	def __init__(self, x, width, height, messages=None):
		self.messages = []
		self.x = x
		self.width = width
		self.height = height
		
	def __str__(self):
		return "FIX THIS MESSAGE LOG STRING"
	
	def __repr__(self):
		return f"{self.__class__.__name__}(x={self.x}, width={self.width}, height={self.height}, messages={[repr(message) for message in self.messages]})"
		
	def add_message(self, message):
		# Split the message if necessary, among multiple lines
		new_msg_lines = textwrap.wrap(message.text, self.width)
		
		for line in new_msg_lines:
			# If the buffer is full, remove the first line to make room for the new one
			if len(self.messages) == self.height:
				del self.messages[0]
				
			# Add the new line as a Message object, with the text and the color
			self.messages.append(Message(line, message.color))