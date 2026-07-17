#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import turtle
import tkinter as tk
from math import *

def forward(): # Pixels
	t.forward(100)

def back(): # Pixels
	t.back(100)

def left(): # Deg
	t.left(90)

def right(): # Deg
	t.right(90)
	
def theodorusSpiral():
	
	unit = 23 # Pixels
	radius = unit * sqrt(2)
	lastradius = 1
	angle = 45
	lastangle = 0
	
	firstTriangle(radius, angle, unit)
	for i in range(1, 23):
		
		print("R:", radius, "A:", angle, "LR:", lastradius, "LA:", lastangle)

		# Angle Growth Rate = arctan(1/sqrt(n))
		# Radius Growth Rate = sqrt(n + 1) - sqrt(n)

		if i == 1: # Skipping first number because of bug TODO
			
			pass
		
		else:
			
			t.setheading(lastangle)
			t.forward(lastradius)
			t.left(90)# Deg
			t.forward(unit)
			t.goto(0, 0)
		
		
		
		lastangle = angle
		angle += atan(1 / sqrt(i + 1)) * (180 / pi)
		lastradius = radius
		radius += unit * (sqrt(i + 2) - sqrt(i + 1))
	
	pass

def firstTriangle(radius, angle, unit=100):
	
	t.forward(unit)
	t.left(90)
	t.forward(unit)
	t.left(180 + angle)
	t.goto(0, 0)
	t.setheading(0)
	
	pass

root = tk.Tk()
canvas = tk.Canvas(master = root, width = 900, height = 800)
canvas.pack()

t = turtle.RawTurtle(canvas)
t.pencolor("#ff0000") # Red

t.penup()   # Regarding one of the comments
t.pendown() # Regarding one of the comments

tk.Button(master = root, text = "Forward", command = forward).pack(side = tk.LEFT)
tk.Button(master = root, text = "Back", command = back).pack(side = tk.LEFT)
tk.Button(master = root, text = "Left", command = left).pack(side = tk.LEFT)
tk.Button(master = root, text = "Right", command = right).pack(side = tk.LEFT)
tk.Button(master = root, text = 'Spiral', command = theodorusSpiral).pack(side = tk.LEFT)

root.mainloop()