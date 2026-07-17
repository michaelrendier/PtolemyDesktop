#!/usr/bin/python3
# -*- coding: utf-8 -*-

from django.db import models

class Sandwiches():
	
	def __init__(self, ingredients=None):
		
		if ingredients:
			self.ingredients = ingredients
			
		else:
			self.basic_ingredients()
		

	def basic_ingredients(self):
		self.ingredients = [
			'snails',
			'leeches',
			'gorilla belly - button lint',
			'caterpillar eyebrows',
			'centipide toes'
		]
		
	def print_ingredients(self):
		
		for i in range(len(self.ingredients)):
			print(str(i + 1), self.ingredients[i])

# food = Sandwiches()
# food.print_ingredients()
# exit(10)

def pascal_triangle(layers):
	x = "*"
	for _ in range(layers):
		print("{0:^{1}}".format(x, layers * 2 + 3))
		x += "**"
	
from subprocess import Popen, PIPE

def kill_proc(process):
	
	kill = Popen(['sudo', 'killall', process], stdout=PIPE, stderr=PIPE)
	res = kill.communicate()
	print("RES:", res)
	if res[1] == b'{0}: no process found\n'.format(process):
		print("No process found")
	elif res == "b''":
		print("killed")
	else:
		print(res)
		
		

