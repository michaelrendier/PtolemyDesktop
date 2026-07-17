#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

# PyFunc.py
# Plotting functions
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from numpy import *
import sys
from math import *

XRANGE = (-5, 5)
YRANGE = (-5, 5)
THERANGE = 10

def init():
	glClearColor(0.0, 0.0, 0.0, 0.0)
	gluOrtho2D(-THERANGE, THERANGE, -THERANGE, THERANGE)
	glColor3f(1.0, 1.0, 1.0)
	
	
def plotfunc():
	glClear(GL_COLOR_BUFFER_BIT)
	glColor3f(1.0, 1.0, 1.0)
	glPointSize(3.0)
	glBegin(GL_LINES)
	glVertex2f(-THERANGE, 0.0)
	glVertex2f(THERANGE, 0.0)
	glVertex2f(0.0, THERANGE)
	glVertex2f(0.0, -THERANGE)
	glEnd()
	
	for x in arange(-THERANGE, THERANGE, 0.1):
		r=3
		y = sqrt(abs((r*r) - (x*x)))
		glBegin(GL_POINTS)
		glVertex2f(x, y)
		glEnd()
		glFlush()
		
def zoom(event):
	print(event)
		
def main():
	glutInit(sys.argv)
	glutInitDisplayMode(GLUT_SINGLE|GLUT_RGB)
	glutInitWindowPosition(50,50)
	glutInitWindowSize(400,400)
	glutCreateWindow("Function Plotter")
	glutDisplayFunc(plotfunc)
	# glutMouseWheelFunc(print("XOOM"))
	
	init()
	glutMainLoop()
main()
# End of program