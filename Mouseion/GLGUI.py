#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
#Builtins
from math import *

#OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLE import *
# import OpenGL_accelerate as glAcc
# import OpenGLContext

class GUI(object):
    # FIX TRANCPARENCY IN IDENTITY TODO

    def __init__(self, parent=None):
        super(GUI, self).__init__()

        # self.Parent = parent
        self.Viewer = parent
        # self.Ptolemy = parent.parent
        print("GUI VIEWER : " + str(self.Viewer))
        # print("GUI PTOLEMY : " + str(self.Viewer))

        self.user = self.Viewer.cmdline('whoami')[0: -1]
        self.platform = self.Viewer.cmdline("uname -o")[0: -1]
        self.nodename = self.Viewer.cmdline('uname -n')[0: -1]

        self.fonts = self.Viewer.fonts

    def refresh2d(self):
        glViewport(0, 0, self.Viewer.g_Width, self.Viewer.g_Height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.Viewer.g_Width, 0.0, self.Viewer.g_Height, 0.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def refresh3d(self):
        glLoadIdentity()
        gluLookAt(0, 0, self.Viewer.g_fViewDistance, 0, 0, 0, -.1, 0, 0)  # -.1,0,0
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.Viewer.zoom, float(self.Viewer.g_Width) / float(self.Viewer.g_Height), self.Viewer.g_nearPlane, self.Viewer.g_farPlane)
        glMatrixMode(GL_MODELVIEW)
        self.Viewer.polarView()

    def frame(self, x, y, width, height, label=None):

        if label:
            self.title(x, y + height - 3, len(label) * 15, label)

        self.rect(x, y, width - 1, height - 1)
        self.rect(x + 2, y + 2, width - 5, height - 5)

    def title(self, x, y, width, label):

        glColor3f(1, 1, 1)
        self.label(x + 5, y, label)
        glColor3f(1, 0, 0)
        self.line(x, y + 2, x + 5 + width, y + 2)
        glColor3f(0, 0, 0.5)
        self.quad(
            x, y + 5,
               x + 5, y + 10,
               x + (width / 3) * 2, y + 10,
               x + (width / 3) * 2, y + 5
        )
        self.quad(
            x, y,
            x + 5, y + 4,
            x + 5 + width, y + 4,
            x + width, y
        )

    def label(self, x, y, text, font=GLUT_BITMAP_8_BY_13):
        blending = False
        if glIsEnabled(GL_BLEND):
            blending = True

        glEnable(GL_BLEND)
        glRasterPos2f(x, y)

        for character in text:
            glutBitmapCharacter(font, ctypes.c_int(ord(character)))

        if not blending:
            glDisable(GL_BLEND)

    # Already Moved
    def labelcur(self, cx, cy, radius, start_angle, sweep_angle, label):
        try:
            theta = 2.0 / (360.0 / sweep_angle) * pi / (len(label) - 1)
        except ZeroDivisionError:
            theta = pi / 180
        c = cos(theta)
        s = sin(theta)

        x = radius * cos(start_angle * (pi / 180.))
        y = radius * sin(start_angle * (pi / 180.))

        for i in range(len(label)):
            self.label(x + cx, y + cy, label[i])  # .encode("utf8"))

            t = x
            x = c * x - s * y
            y = s * t + c * y

    def rect(self, x, y, width, height, method=GL_LINE_LOOP):
        glBegin(method)
        glVertex2f(x, y)
        glVertex2f(x, y + height)
        glVertex2f(x + width, y + height)
        glVertex2f(x + width, y)
        glEnd()
        glutPostRedisplay()

    def quad(self, x1, y1, x2, y2, x3, y3, x4, y4, method=GL_POLYGON):

        glBegin(method)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glVertex2f(x3, y3)
        glVertex2f(x4, y4)
        glEnd()
        glutPostRedisplay()

    def button(self, x, y, lable=None, width=100, height=25):

        self.rect(x, y, width, height)
        if lable:
            self.label(x, y + (height / 2.6), lable)
        glutPostRedisplay()

    def circle(self, cx, cy, radius, sides, method=GL_LINE_LOOP):
        try:
            theta = 2.0 * pi / sides
        except ZeroDivisionError:
            theta = pi / 180
        c = cos(theta)
        s = sin(theta)

        x = radius
        y = 0

        glBegin(method)
        for i in range(0, sides + 1):
            glVertex2f(x + cx, y + cy)

            t = x
            x = c * x - s * y
            y = s * t + c * y

        glEnd()

    def circle3d(self, cx, cy, z, radius, sides, method=GL_LINE_LOOP):

        theta = 2.0 * pi / sides
        c = cos(theta)
        s = sin(theta)

        x = radius
        y = 0

        glBegin(method)
        for i in range(0, sides + 1):
            glVertex3f(x + cx, y + cy, z)

            t = x
            x = c * x - s * y
            y = s * t + c * y

        glEnd()

    def partialcircle(self, cx, cy, radius, start_angle, sweep_angle, sides, method=GL_LINE_STRIP):
        try:
            theta = -2.0 / (360.0 / sweep_angle) * pi / (sides)
        except ZeroDivisionError:
            theta = pi / 180
        c = cos(theta)
        s = sin(theta)

        x = radius * cos(start_angle * (pi / 180.))
        y = radius * sin(start_angle * (pi / 180.))

        glBegin(method)
        for i in range(sides + 1):
            glVertex2f(x + cx, y + cy)

            t = x
            x = c * x - s * y
            y = s * t + c * y
        glEnd()

    def partialdisk(self, x, y, inner, outer, slices, loops, start_angle, sweep_angle, method=GL_FILL):

        glTranslate(x, y, 0)
        quadratic = gluNewQuadric()
        gluQuadricNormals(quadratic, GLU_SMOOTH)  # Create Smooth Normals (NEW)
        gluQuadricTexture(quadratic, GL_TRUE)
        gluQuadricDrawStyle(quadratic, method)
        gluPartialDisk(quadratic, inner, outer, slices, loops, start_angle, sweep_angle)
        glTranslate(-x, -y, 0)
        glutPostRedisplay()

    def line(self, x1, y1, x2, y2, method=GL_LINE_STRIP):
        glBegin(method)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()

    def percentbar(self, x, y, width, height, percent, color, title=None, type="Horizontal"):
        self.refresh2d()
        if type == "Vertical":
            t = width
            width = height
            height = t

        if title:
            self.title(x, y + height, width, "{} {}".format(title, percent))

        percent = int(percent) / 100.0
        glColor3f(color[0], color[1], color[2])

        if percent != 0:
            self.rect(x, y, width, height)
            self.rect(x, y, width * percent, height, GL_POLYGON)
        self.refresh3d()

    def percentarc(self, x, y, inner, outer, start_angle, sweep_angle, percent, color, title=None, sides=36, loops=36,
                   method=GL_FILL):
        self.refresh2d()
        if title:
            self.title(x - outer, y + outer, 2 * outer, "{} {}".format(title, percent))

        percent = int(percent) / 100.0
        glColor3f(color[0], color[1], color[2])

        if percent != 0:
            self.partialdisk(x, y, inner, outer, sides, loops, start_angle, sweep_angle * percent, method)
        self.refresh3d()

    def percentarc3d(self, x, y, z, inner, outer, start_angle, sweep_angle, height, type, percent, method=GL_FILL, slices=36,
                     loops=36):
        """
        type 0 = Angle
        type 1 = Height
        type 2 = Both
        :param x:
        :param y:
        :param z:
        :param inner:
        :param outer:
        :param start_angle:
        :param sweep_angle:
        :param height:
        :param type:
        :param method:
        :param slices:
        :param loops:
        :return:
        """
        percent = int(percent) / 100.0

        if percent != 0:

            if type == 0:
                self.arcCylinder(x, y, z, inner, outer, slices, loops, start_angle, sweep_angle * percent, height,
                            method)

            elif type == 1:
                self.arcCylinder(x, y, z, inner, outer, slices, loops, start_angle, sweep_angle, height * percent,
                            method)
                glColor3f(1, 1, 1)
                self.partialDisk(x, y, z + height, inner, outer, slices, loops, start_angle, sweep_angle, GLU_SILHOUETTE)

            elif type == 2:

                self.arcCylinder(x, y, z, inner, outer, slices, loops, start_angle, sweep_angle * percent, height * percent,
                            method)
                glColor3f(1, 1, 1)
                self.partialDisk(x, y, z + height, inner, outer, slices, loops, start_angle, sweep_angle * percent,
                            GLU_SILHOUETTE)

        glutPostRedisplay()

    def marquee(self, x, y, width, height, title, input, color):  # FIX MARQUEE TODO

        self.refresh2d()
        marqueeList = [0] * (width - 2)
        self.refresh2d()
        self.rect(x, y, width, height)

        for i in range(len(marqueeList)):
            self.line(x + 1 + i, y + 1, x + 1 + i, y + (height / 2))

        self.refresh3d()

    def bargraph(self, x, y, width, height, data, color, label1, title=None, type="Horizontal",
                 method=GL_QUADS):  # FIX VERTICAL TODO

        data = [(0, "zero"), (1, "one"), (2, "two"), (3, "three"), (4, "four")]
        # data = [
        # 	(31, "January"),
        # 	(28, "February"),
        # 	(31, "March"),
        # 	(30, "April"),
        # 	(31, "May"),
        # 	(30, "June"),
        # 	(31, "July"),
        # 	(31, "August"),
        # 	(30, "September"),
        # 	(31, "October"),
        # 	(30, "November"),
        # 	(31, "December"),
        # ]
        strlen = 0
        for i in data:
            if len(i[1]) > strlen:
                strlen = len(i[1])
        width = strlen * 9 * len(data) + 30
        numbervalue = len(data)
        maxvalue = max(data)[0]

        self.refresh2d()

        if type == "Vertical":
            glTranslate(x + width / 2, y + height / 2, 0)
            glRotate(90, 0, 0, 1)
            glTranslate(-x, -y, 0)
            t = width
            width = height
            height = t

        barwidth = (width - 15) / numbervalue
        barunit = (height - 25) / maxvalue

        if title:
            self.title(x, y + height, width, title)

        glColor3f(color[0], color[1], color[2])

        self.rect(x, y, width, height)

        newstring = ""
        for i in label1:
            newstring += i + " "

        # FIX AUTOWIDTH TODO

        for i in range(len(label1)):
            glRotate(i / 2 * (5 / len(label1)), 0, 0, 1)
            glRasterPos2f(x - 15, y + i * height / len(label1) + 10)

            glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ctypes.c_int(ord(str(label1[-1 - i]))))
            glRotate(- i / 2 * (5 / len(label1)), 0, 0, 1)

        for i in range(len(data)):
            glColor(1, 1, 1)
            icolor = i - (i / 8) * 8  # colors[i]

            if icolor == 0:
                icolor += 4

            glColor3f(self.Viewer.colors[icolor][0], self.Viewer.colors[icolor][1], self.Viewer.colors[icolor][2])
            self.rect(x + (i * barwidth) + 10 + 5, y + 20, barwidth - 5, barunit * data[i][0], method)

            if data[i][1] != "":
                self.label(x + (i * barwidth) + 10 + 5 + (barwidth / 2 - (len(data[i][1]) * 9) / 2), y + 10,
                           str(data[i][1]), GLUT_BITMAP_8_BY_13)

        self.refresh3d()

    def io2on1(self):
        # input/output both on one bar graph with different colors
        # as range increases change range and adjust
        pass

    def io2on2(self):
        # input/output on two graphs back to back same color
        pass

    def Cylinder(self, x, y, z, base, top, height, slices, stacks, method=GL_FILL):
        quadratic = gluNewQuadric()
        glTranslate(x, y, z)
        gluQuadricNormals(quadratic, GLU_SMOOTH)  # Create Smooth Normals (NEW)
        gluQuadricTexture(quadratic, GL_TRUE)
        gluQuadricDrawStyle(quadratic, method)
        glColor3f(1, 0, 0)
        gluCylinder(quadratic, base, top, height, slices, stacks)
        glTranslate(-x, -y, -z)

    def arcCylinder(self, x, y, z, inner, outer, slices, loops, start_angle, sweep_angle, height,
                    method=GL_FILL):  # ADD SIDES IN QUADS TODO
        c1 = cos((-start_angle + 90) * pi / 180)
        s1 = sin((-start_angle + 90) * pi / 180)
        c2 = cos(((-start_angle + 90) - sweep_angle) * pi / 180)
        s2 = sin(((-start_angle + 90) - sweep_angle) * pi / 180)
        quad1 = [(inner * c1, inner * s1, z),
                 (outer * c1, outer * s1, z),
                 (inner * c1, inner * s1, z + height),
                 (outer * c1, outer * s1, z + height)]

        quad2 = [(inner * c2, inner * s2, z),
                 (outer * c2, outer * s2, z),
                 (inner * c2, inner * s2, z + height),
                 (outer * c2, outer * s2, z + height)]

        glBegin(GL_TRIANGLE_STRIP)
        for i in quad1:
            glVertex3fv(i)
        glEnd()

        glBegin(GL_TRIANGLE_STRIP)
        for i in quad2:
            glVertex3fv(i)
        glEnd()

        # GLU_FILL , GLU_LINE , GLU_SILHOUETTE , and GLU_POINT
        quad = gluNewQuadric()
        glTranslatef(x, y, z)
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        gluQuadricDrawStyle(quad, method)
        gluPartialDisk(quad, inner, outer, slices, loops, start_angle, sweep_angle)
        self.partialCylinder(x, y, z, inner, height, -start_angle + 90, sweep_angle, slices, GL_TRIANGLE_STRIP)
        self.partialCylinder(x, y, z, outer, height, -start_angle + 90, sweep_angle, slices, GL_TRIANGLE_STRIP)
        glTranslatef(x, y, z + height)
        gluPartialDisk(quad, inner, outer, slices, loops, start_angle, sweep_angle)
        glTranslatef(-x, -y, -(z + height))

    def partialCylinder(self, cx, cy, cz, radius, height, start_angle, sweep_angle, sides, method=GL_TRIANGLE_STRIP):
        try:
            theta = -2.0 / (360.0 / sweep_angle) * pi / (sides)
        except ZeroDivisionError:
            theta = pi / 180
        c = cos(theta)
        s = sin(theta)

        x = radius * cos(start_angle * pi / 180.)
        y = radius * sin(start_angle * pi / 180.)

        glBegin(method)
        for i in range(sides + 1):
            glVertex3f(x + cx, y + cy, cz)
            glVertex3f(x + cx, y + cy, cz + height)

            t = x
            x = c * x - s * y
            y = s * t + c * y
        glEnd()

    def partialDisk(self, x, y, z, inner, outer, slices, loops, start_angle, sweep_angle, method=GL_FILL):
        quadratic = gluNewQuadric()
        glTranslate(x, y, z)
        gluQuadricNormals(quadratic, GLU_SMOOTH)  # Create Smooth Normals (NEW)
        gluQuadricTexture(quadratic, GL_TRUE)
        gluQuadricDrawStyle(quadratic, method)
        gluPartialDisk(quadratic, inner, outer, slices, loops, start_angle, sweep_angle)
        glTranslate(-x, -y, -z)