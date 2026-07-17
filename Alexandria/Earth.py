#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
#Builtins
from math import *



#OpenGL
from OpenGL.GL import *
from OpenGL.GLUT import *
# import OpenGL_accelerate as glAcc
# import OpenGLContext

#Installed
import ast
import numpy

class Earth(object):  # FIX ROTATING THING AGAIN

    def __init__(self, center=(0, 0, 0), size=1.5, parent=None):
        super(Earth, self).__init__()
        object.__init__(self)

        self.Viewer = parent

        self.citylist = []
        self.cx = center[0]
        self.cy = center[1]
        self.cz = center[2]
        self.size = size
        self.id = id(self)
        self.live = ["Eureka"]
        self.livedin = ["Bishop", "Eureka", "Brea", "Los Angeles", "Seattle", "Murfreesboro", "New Orleans",
                        "Pensacola", "Atlanta", "Orlando", "Redding", "Gardnerville", "Carson City", "Lawton",
                        "Colorado Springs", "El Paso"]

        os.system("python /home/rendier/Ptolemy/Alexandria/GoogleEarth.py")
        print('Places Updated')

        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        with open(PTOL_ROOT + '/Alexandria/citylist.txt', 'r') as f:
            self.citylist = ast.literal_eval(f.read())

        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        with open(PTOL_ROOT + '/Alexandria/locations.txt', 'r') as nf:
            self.locations = ast.literal_eval(nf.read())

        # self.show(self, self.id)
        self.build()

    def build(self):

        glRotate(-90, 1, 0, 0)
        glRotate(-90, 0, 1, 0)
        glScale(self.size, self.size, self.size)

        for i in self.citylist:

            glColor3f(0.7, 0.7, 0.7)
            # if i[0] in self.livedin:
            # 	glPointSize(2)
            # 	glColor(1, 0, 0)

            try:
                point = self.convert(float(i[2]) * pi / 180, float(i[3]) * pi / 180)

            except ValueError:
                pass

            else:
                glPointSize(3)
                glBegin(GL_POINTS)
                glVertex3f(point[0] + self.cx, point[1] + self.cy, point[2] + self.cz)
                glEnd()

                if i[0] in self.livedin and i[7] == 'USA':
                    point2 = self.convert(float(i[2]) * pi / 180, float(i[3]) * pi / 180, 0.2)
                    glColor3f(1, 0, 0)
                    glLineWidth(2)
                    glBegin(GL_LINES)
                    glVertex3f(point[0] + self.cx, point[1] + self.cy, point[2] + self.cz)
                    glVertex3f(point2[0] + self.cx, point2[1] + self.cy, point2[2] + self.cz)
                    glEnd()
                    if i[0] in self.live:
                        glColor(0, 1, 1)
                        glPointSize(3)
                        glBegin(GL_POINTS)
                        glVertex3f(point2[0], point2[1], point2[2])
                        glEnd()
                        glColor(1, 1, 0)
                        self.Viewer.gui.circle3d(point2[0], point2[1], point2[2], 0.04, 36)

                glPointSize(1)

        for i in self.locations:

            glColor3f(1, 1, 0)

            try:
                point = self.convert(float(i[2]) * pi / 180, float(i[1]) * pi / 180)

            except ValueError:
                pass

            else:
                glPointSize(2)
                glBegin(GL_POINTS)
                glVertex3f(point[0] + self.cx, point[1] + self.cy, point[2] + self.cz)
                glEnd()

                glPointSize(1)
        self.surface(2.99)

        glScale(1 / self.size, 1 / self.size, 1 / self.size)
        glRotate(90, 0, 1, 0)
        glRotate(90, 1, 0, 0)

    def convert(self, lat, lon, alt=0):
        # see http://www.mathworks.de/help/toolbox/aeroblks/llatoecefposition.html
        rad = numpy.float64(2 * self.size)  # Radius of the Earth (in meters)
        f = numpy.float64(1.0 / 298.257223563)  # Flattening factor WGS84 Model
        cosLat = numpy.cos(lat)
        sinLat = numpy.sin(lat)
        FF = (1.0 - f) ** 2
        C = 1 / numpy.sqrt(cosLat ** 2 + FF * sinLat ** 2)
        S = C * FF

        x = (rad * C + alt) * cosLat * numpy.cos(lon)
        y = (rad * C + alt) * cosLat * numpy.sin(lon)
        z = (rad * S + alt) * sinLat

        return (x, y, z)

    def surface(self, radius, slices=36, stacks=36):

        glColor3f(1, 1, 1)
        
        glBegin(GL_LINES)
        glVertex3f(self.cx, self.cy, (-radius - 1 + self.cz))
        glVertex3f(self.cx, self.cy, (radius + 1 + self.cz))
        glEnd()

        glTranslate(self.cx, self.cy, self.cz)
        glColor(0, 0, 0)
        glutSolidSphere(radius, slices, stacks)

        glColor(0, 0, 0.5)
        glLineWidth(10.0)
        glutWireSphere(radius, slices, stacks)
        glTranslate(-self.cx, -self.cy, -self.cz)

    def timerEvent(self):
        glRotate(30, 0, 1, 0)
        glutPostRedisplay()