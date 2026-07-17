#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
#Builtins
from math import *
from subprocess import PIPE, Popen

from Alexandria.Earth import Earth
# from Alexandria.Core import Core
from Mouseion.GLGUI import GUI

#OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLE import *
from OpenGL.GLUT import *
# import OpenGL_accelerate as glAcc
# import OpenGLContext

#Installed
import psutil
import ast
import numpy
from PIL import Image, ImageDraw, ImageFont


import ctypes, io
libc = ctypes.CDLL(None)

from contextlib import redirect_stdout, redirect_stderr



class Viewer(object):

    def __init__(self, view=None, rotate=False, parent=None):
        super(Viewer, self).__init__()
        object.__init__(self)

        self.Ptolemy = parent
        self.view = view
        self.rotate = rotate

        self.g_fViewDistance = 9.
        self.g_Width = 600
        self.g_Height = 600

        self.g_nearPlane = 0.1
        self.g_farPlane = 100.

        self.action = ""
        self.xStart = self.yStart = 0.
        self.zoom = 20.

        self.xRotate = 0.
        self.yRotate = 0.
        self.zRotate = 0.

        self.xTrans = 0.
        self.yTrans = 0.

        self.fonts = [GLUT_BITMAP_8_BY_13, GLUT_BITMAP_9_BY_15, GLUT_BITMAP_TIMES_ROMAN_10, GLUT_BITMAP_HELVETICA_10,
                 GLUT_BITMAP_HELVETICA_12
                 ]

        self.colorsAll = [(r, g, b) for r in range(0, 254) for g in range(0, 254) for b in range(0, 254)]
        self.colors = [(r, g, b) for r in (0, 1) for g in (0, 1) for b in (0, 1)]

        self.red = (255, 0, 0)
        self.darkRed = (128, 0, 0)
        self.green = (0, 255, 0)
        self.darkGreen = (0, 128, 0)
        self.blue = (0, 0, 255)
        self.cyan = (0, 255, 255)
        self.magenta = (255, 0, 255)
        self.yellow = (255, 255, 0)
        self.darkyellow = (128, 128, 0)
        self.darkBlue = (0, 0, 128)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.pink = (255, 200, 200)
        self.grey = (79, 79, 79)

        # GLUT Window Initialization
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # zBuffer
        glutInitWindowSize(self.g_Width, self.g_Height)
        # glutInitWindowPosition(0 + 4, self.g_Height / 4)
        glutCreateWindow("PTOLEMY II Core")

        # Initialize OpenGL graphics state

        self.init()

        # Register callbacks
        glutReshapeFunc(self.reshape)
        glutDisplayFunc(self.display)
        glutMouseFunc(self.mouse)
        glutMotionFunc(self.motion)
        glutKeyboardFunc(self.keyboard)
        # glutIdleFunc(self.timerEvent)
        glutCloseFunc(self.finished)
        # if rotate:
        #     print("rotate = True")
        #     glutIdleFunc(self.rotate)
        # else:
        #     glutIdleFunc(glutPostRedisplay)
        # glutCreateMenu(processMenuEvents)
        self.printHelp()
        # glutTimerFunc(1000, self.timerEvent, 1)


        self.gui = GUI(parent=self)

        glEnable(GL_NORMALIZE)
        # glLightfv(GL_LIGHT0, GL_POSITION, [.0, 10.0, 10., 0.])
        # glLightfv(GL_LIGHT0, GL_AMBIENT, [1.0, 1.0, 1.0, 1.0]);
        # glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0]);
        # glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0]);
        # glEnable(GL_LIGHT0)
        # glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glShadeModel(GL_SMOOTH)
        glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
        glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)

        self.resetView()

        glutMainLoop()

    def __del__(self):
        return

    def finished(self):
        print("FINISHED")
        
        del(self)
    
    def closeEvent(self):
        print('closeEvent')

        pass


    def printHelp(self):
        print(
        """\n\n
    		 -------------------------------------------------------------------\n
    		 Left Mousebutton       - move eye position (+ Shift for third axis)\n
    		 Middle Mousebutton     - translate the scene\n
    		 Right Mousebutton      - move up / down to zoom in / out\n
    		  Key                - reset viewpoint\n
    		  Key                - exit the program\n
    		 -------------------------------------------------------------------\n
    		 \n""")

    def init(self):
        glEnable(GL_NORMALIZE)
        # glLightfv(GL_LIGHT0, GL_POSITION, [.0, 10.0, 10., 0.])
        # glLightfv(GL_LIGHT0, GL_AMBIENT, [1.0, 1.0, 1.0, 1.0]);
        # glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0]);
        # glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0]);
        # glEnable(GL_LIGHT0)
        # glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glShadeModel(GL_SMOOTH)
        glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
        glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)

        self.resetView()

    def resetView(self):
        # global zoom, xRotate, yRotate, zRotate, xTrans, yTrans
        self.zoom = 65.
        self.xRotate = 0.
        self.yRotate = 0.
        self.zRotate = 0.
        self.xTrans = 0.
        self.yTrans = 0.
        glutPostRedisplay()

    def display(self):
        # Clear frame buffer and depth buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Set up viewing transformation, looking down -Z axis
        glLoadIdentity()
        gluLookAt(0, 0, self.g_fViewDistance, 0, 0, 0, -.1, 0, 0)
        # Set perspective (also zoom)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.zoom, float(self.g_Width) / float(self.g_Height), self.g_nearPlane, self.g_farPlane)
        glMatrixMode(GL_MODELVIEW)
        glColor3f(1, 1, 1)
        # Render the scene
        self.polarView()

        # ctypes.cast(id(a), ctypes.py_object).value

        # Input = Command()

        self.View = self.view(parent=self)

        # if self.rotate:
        #     print("rotate = True")
        #     glutIdleFunc(self.View.timerEvent)
        # else:
        #     glutIdleFunc(glutPostRedisplay)

        # Make sure changes appear onscreen
        glutSwapBuffers()

    def reshape(self, width, height):
        # global g_Width, g_Height
        self.g_Width = width
        self.g_Height = height
        glViewport(0, 0, self.g_Width, self.g_Height)

    def polarView(self):
        glTranslatef(self.yTrans / 100., 0.0, 0.0)
        glTranslatef(0.0, -self.xTrans / 100., 0.0)
        glRotatef(-self.zRotate, 0.0, 0.0, 1.0)
        glRotatef(-self.xRotate, 1.0, 0.0, 0.0)
        glRotatef(-self.yRotate, 0.0, 1.0, 0.0)

    def keyboard(self, key, x, y):
        global zTr, yTr, xTr
        if (key == 'r'): self.resetView()
        # if (key == 'o'): self.Kernel.hide()
        if (key == 'q'): exit(0)
        glutPostRedisplay()

    def mouse(self, button, state, x, y):
        # global action, self.xStart, self.yStart
        if (button == GLUT_LEFT_BUTTON):
            if (glutGetModifiers() == GLUT_ACTIVE_SHIFT):
                self.action = "MOVE_EYE_2"
            else:
                self.action = "MOVE_EYE"
        elif (button == GLUT_MIDDLE_BUTTON):
            self.action = "ZOOM"
        elif (button == GLUT_RIGHT_BUTTON):
            self.action = "ZOOM"
        # ~ elif (button == ctypes.c_int(3)):
        # ~ action = "ZOOM"
        # ~ print "positive"
        # ~ elif (button == ctypes.c_int(4)):
        # ~ action = "ZOOM"
        # ~ print "negative"
        self.xStart = x
        self.yStart = y

    def motion(self, x, y):
        # global zoom, xStart, yStart, xRotate, yRotate, zRotate, xTrans, yTrans
        if (self.action == "MOVE_EYE"):
            self.xRotate += (x - self.xStart) / 500
            self.yRotate -= (y - self.yStart) / 500
        elif (self.action == "MOVE_EYE_2"):
            self.zRotate += (x - self.xStart) / 500
        # yRotate -= y - yStart
        elif (self.action == "TRANS"):
            self.xTrans += (x - self.xStart) / 500
            self.yTrans -= (y - self.yStart) / 500
        elif (self.action == "ZOOM"):
            self.zoom -= (y - self.yStart) / 500
            if self.zoom > 200.:
                self.zoom = 200.
            elif self.zoom < 1.1:
                self.zoom = 1.1
        else:
            print("unknown action\n", self.action)
        xStart = x
        yStart = y
        glutPostRedisplay()

    def cmdline(self, command):
        process = Popen(
            args=command,
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()[0]

    def rotate(self):
        print('rotating')
        glRotate(30, 0, 1.0, 0)
        glutPostRedisplay()
        # glutSwapBuffers()

    def timerEvent(self):
        print("timerEvent")
        glRotate(20, 0, 1, 0)
        # glutPostRedisplay()


# try:
if __name__ == "__main__":

    # View = Viewer(Core)
    View = Viewer(Earth)
    # Turn the flow of control over to GLUT
    # glutMainLoop()

# except:
#
#     f = io.StringIO()
#     with redirect_stderr(f):
#         print('foobar')
#         print(12)
#         libc.puts(b'this comes from C')
#         os.system('echo and this is from echo')
#     print('Got stdout: "{0}"'.format(f.getvalue()))