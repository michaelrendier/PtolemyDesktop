#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import turtle as tkt


class Shape:
	tkt.tracer(8, 0)
	
	def __init__(self, sides, size):
		self.sides = sides
		self.size = size
	
	#    self.screen=screen
	
	# self.t.tracer=(8,0)
	
	def __call__(self):
		for i in range(self.sides):
			tkt.forward(self.size)
			tkt.left(360 / self.sides)


# Sq.square()
# mainloop

square = Shape(4, 150)
triangle = Shape(3, 170)
pentagon = Shape(5, 180)
circle = Shape(360, 1.8)

for i in range(8):
	square()
	tkt.left(45)
	triangle()
	pentagon()
	circle()

tkt.mainloop()