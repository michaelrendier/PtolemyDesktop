#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
#Builtins
from math import *

from Pharos.UtilityFunctions import *

#OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# import OpenGL_accelerate as glAcc
# import OpenGLContext

#Installed
import numpy
from PIL import Image

#for returning of C errors
import ctypes

libc = ctypes.CDLL(None)


class Graphing(object):  # ADD GLSCALE TO THIS TODO

    def __init__(self, equation=None, boxplot_data=None, center=(0, 0, 0), grid_range=10, step=1, color=(1, 1, 1), size=15, resolution=2, parent=None):
        super(Graphing, self).__init__()
        object.__init__(self)

        self.GraphPlot = parent
        print("GRAPHPLOT PARENT: ", self.GraphPlot)
        print("GRAPHPLOT EQUATION: ", equation)

        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        self.imgDir = PTOL_ROOT + '/images/Alexandria/'

        # if center:

        self.cx = center[0]
        self.cy = center[1]

        try:
            self.cz = center[2]
        except IndexError:
            pass

        # else:
        #     self.cx = self.GraphPlot.g_Width / 2
        #     self.cy = self.GraphPlot.g_Height / 2
        #     self.cz = 0

        self.center = center
        self.range = grid_range
        self.step = step
        if equation:
            self.equation = equation
        if boxplot_data:
            self.boxplot_data = boxplot_data
        self.color = color
        self.size = size
        self.resolution = resolution
        self.gui = GUI(self)

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
        self.darkBlue = (0, 0, 128)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.pink = (255, 200, 200)
        self.grey = (79, 79, 79)

        self.build()

    # self.show(self, id(self))

    def build(self):
        # if len(self.center) == 2:
        if self.boxplot_data:
            self.BoxAndWhisker(self.boxplot_data)
            self.grid2d(self.range, self.step)
            pass
        
        elif 'y' not in self.equation[0]:
            print("2D equation")
            for i in range(len(self.equation)):
                print(i)
                if i > 6:
                    print('over')
                    i = i - 6
                    print(i)
                self.graph2d(self.equation[i], self.colors[i + 1])
            self.grid2d(self.range, self.step)

        elif 'y' in self.equation[0]:
            print("3D equation")
            self.image = Image.open(self.imgDir + "trans-grad.png")  # MCP_3D_Graphic.jpg")#kerneltex.jpg")
            self.ix = self.image.size[0]
            self.iy = self.image.size[1]
            self.image = self.image.convert("RGBA").tobytes("raw", "RGBA")

            self.LoadTextures(self.image)

            if type(self.equation) == str:
                self.graph3d(self.equation, self.color)
            elif type(self.equation) == list:
                for i in range(len(self.equation)):
                    self.graph3d(self.equation[i], self.colors[i + 1])
            self.grid3d(self.range, self.step)
            self.halo3d(self.range)

    def LoadTextures(self, image):

        # Create Texture
        textures = glGenTextures(3)
        glBindTexture(GL_TEXTURE_2D, int(textures[1]))  # 2d texture (x and y size)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, self.ix, self.iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        #
        # Create Linear Filtered Texture
        glBindTexture(GL_TEXTURE_2D, int(textures[1]))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, self.ix, self.iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)

        # Create MipMapped Texture
        glBindTexture(GL_TEXTURE_2D, int(textures[2]))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST)
        gluBuild2DMipmaps(GL_TEXTURE_2D, 3, self.ix, self.iy, GL_RGBA, GL_UNSIGNED_BYTE, image)

    def halo3d(self, grid_range):  # FIX GRADIENT TRANSPARANCY TRY TRANSPARENT TEXTURE TODO

        # glEnable(GL_TEXTURE_2D)
        # glEnable(GL_TEXTURE_GEN_S)
        # glEnable(GL_TEXTURE_GEN_T)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1, 1, 1, 0.4)

        glPushMatrix()
        glBegin(GL_QUADS)
        glVertex3f((grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glVertex3f((grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f((grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glVertex3f((grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f((grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glVertex3f((grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f((-grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size, (0 + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (-grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glVertex3f((-grid_range + self.cx) * self.size, (grid_range + self.cy) * self.size,
                   (grid_range + self.cz) * self.size)
        glEnd()

        glPopMatrix()
        # glDisable(GL_TEXTURE_GEN_S)
        # glDisable(GL_TEXTURE_GEN_T)
        # glDisable(GL_TEXTURE_2D)

        glDisable(GL_BLEND)

    def grid3d(self, grid_range, step):

        glColor3f(0.2, 0.2, 0.2)

        for x in range(-grid_range, grid_range + 1, step):
            self.gui.label3d((x + self.cx) * self.size, (self.cy + grid_range) * self.size, (self.cz - grid_range) * self.size,
                    str(x))
            for y in range(-grid_range, grid_range + 1, step):
                self.gui.label3d((grid_range + self.cx) * self.size, (self.cy + y) * self.size,
                        (self.cz - grid_range) * self.size, str(y))
                glBegin(GL_LINES)
                glVertex3f((x + self.cx) * self.size, (self.cy - grid_range) * self.size,
                           (self.cz - grid_range) * self.size)
                glVertex3f((x + self.cx) * self.size, (self.cy + grid_range) * self.size,
                           (self.cz - grid_range) * self.size)
                glVertex3f((self.cx - grid_range) * self.size, (self.cy + y) * self.size,
                           (self.cz - grid_range) * self.size)
                glVertex3f((self.cx + grid_range) * self.size, (self.cy + y) * self.size,
                           (self.cz - grid_range) * self.size)
                glEnd()

        # glColor3f(0, 0, 0.5)
        for x in range(-grid_range, grid_range + 1, step):
            self.gui.label3d((self.cx + x) * self.size, (self.cy - grid_range) * self.size, (self.cz + grid_range) * self.size,
                    str(x))
            for z in range(-grid_range, grid_range + 1, step):
                self.gui.label3d((self.cx + grid_range) * self.size, (self.cy - grid_range) * self.size,
                        (self.cz + z) * self.size, str(z))
                glBegin(GL_LINES)
                glVertex3f((self.cx + x) * self.size, (self.cy - grid_range) * self.size,
                           (self.cz - grid_range) * self.size)
                glVertex3f((self.cx + x) * self.size, (self.cy - grid_range) * self.size,
                           (self.cz + grid_range) * self.size)
                glVertex3f((self.cx - grid_range) * self.size, (self.cy - grid_range) * self.size,
                           (self.cz + z) * self.size)
                glVertex3f((self.cx + grid_range) * self.size, (self.cy - grid_range) * self.size,
                           (self.cz + z) * self.size)
                glEnd()

        # glColor3f(0, 0.5, 0)
        for y in range(-grid_range, grid_range + 1, step):
            self.gui.label3d((self.cx - grid_range) * self.size, (self.cy + y) * self.size, (self.cz + grid_range) * self.size,
                    str(y))
            for z in range(-grid_range, grid_range + 1, step):
                self.gui.label3d((self.cx - grid_range) * self.size, (self.cy + grid_range) * self.size,
                        (self.cz + z) * self.size, str(z))
                glBegin(GL_LINES)
                glVertex3f((self.cx - grid_range) * self.size, (self.cy - grid_range) * self.size,
                           (self.cz + z) * self.size)
                glVertex3f((self.cx - grid_range) * self.size, (self.cy + grid_range) * self.size,
                           (self.cz + z) * self.size)
                glVertex3f((self.cx - grid_range) * self.size, (self.cy + y) * self.size,
                           (self.cz - grid_range) * self.size)
                glVertex3f((self.cx - grid_range) * self.size, (self.cy + y) * self.size,
                           (self.cz + grid_range) * self.size)
                glEnd()

        axes = [
            [[(-grid_range + self.cx) * self.size, 0, 0], [(grid_range + self.cx) * self.size, 0, 0]],
            [[0, (-grid_range + self.cy) * self.size, 0], [0, (grid_range + self.cy) * self.size, 0]],
            [[0, 0, (-grid_range + self.cz) * self.size], [0, 0, (grid_range + self.cz) * self.size]]
        ]

        glColor3f(1, 1, 1)
        glBegin(GL_LINES)
        for axis in axes:
            glVertex3f(axis[0][0], axis[0][1], axis[0][2])
            glVertex3f(axis[1][0], axis[1][1], axis[1][2])
        glEnd()

    def graph3d(self, equation, color=(1, 1, 1), method=GL_QUADS):  # DO SPHERE AND INVERSE TODO
        array = []
        grid_steps = self.range * 2 * self.resolution

        for x in numpy.linspace(-self.range, self.range, grid_steps + 1):
            line = []
            for y in numpy.linspace(-self.range, self.range, grid_steps + 1):
                try:
                    # code = "z = {0}".format(equation)
                    # print("Z CODE : ", code)
                    # exec(code)
                    z = eval(equation)
                    # print("Z : ", z)
                    # z = sin(x) + cos(y)
                except ValueError:
                    pass
                except ZeroDivisionError:
                    pass
                else:
                    var = ((x + self.cx) * self.size, (y + self.cy) * self.size, (z + self.cz) * self.size)
                    line.append(var)
            array.append(line)

        array = sorted(array)

        for i in range(len(array) - 1):
            for j in range(grid_steps):
                glColor3f(color[0], color[1], color[2])
                glBegin(GL_LINE_LOOP)
                glVertex3f(array[i][j][0], array[i][j][1], array[i][j][2])  #
                glVertex3f(array[i][j + 1][0], array[i][j + 1][1], array[i][j + 1][2])
                glVertex3f(array[i + 1][j + 1][0], array[i + 1][j + 1][1], array[i + 1][j + 1][2])
                glVertex3f(array[i + 1][j][0], array[i + 1][j][1], array[i + 1][j][2])
                glEnd()

        if method == GL_QUADS:
            glColor3f(color[0] * 0.1, color[1] * 0.1, color[2] * 0.1)
            for i in range(len(array) - 1):
                for j in range(grid_steps):
                    glBegin(GL_QUADS)
                    glVertex3f(array[i][j][0], array[i][j][1], array[i][j][2])
                    glVertex3f(array[i][j + 1][0], array[i][j + 1][1], array[i][j + 1][2])
                    glVertex3f(array[i + 1][j + 1][0], array[i + 1][j + 1][1], array[i + 1][j + 1][2])
                    glVertex3f(array[i + 1][j][0], array[i + 1][j][1], array[i + 1][j][2])
                    glEnd()

        self.grid3d(self.range, self.step)

    def grid2d(self, grid_range, step):

        axes = [
            [[(-grid_range * self.size) + self.cx, self.cy], [(grid_range * self.size) + self.cx, self.cy]],
            [[self.cx, (-grid_range * self.size) + self.cy], [self.cx, (grid_range * self.size) + self.cy]]
        ]
        self.gui.refresh2d()

        glColor3f(0.4, 0.4, 0.4)
        # glScale(self.size, self.size, self.size)
        glBegin(GL_LINES)
        for axis in axes:
            glVertex2f(axis[0][0], axis[0][1])
            glVertex2f(axis[1][0], axis[1][1])
        glEnd()

        glColor3f(0.2, 0.2, 0.2)

        for x in range(-grid_range, grid_range + 1, step):
            self.gui.label((x * self.size + self.cx), (self.cy + grid_range * self.size), str(x))
            for y in range(-grid_range, grid_range + 1, step):
                self.gui.label((self.cx + grid_range * self.size), (y * self.size + self.cy), str(y))
                glBegin(GL_LINES)
                glVertex2f((x * self.size + self.cx), (self.cy - grid_range * self.size))
                glVertex2f((x * self.size + self.cx), (self.cy + grid_range * self.size))
                glVertex2f((self.cx - grid_range * self.size), (self.cy + y * self.size))
                glVertex2f((self.cx + grid_range * self.size), (self.cy + y * self.size))
                glEnd()

        self.gui.refresh3d()

    def graph2d(self, equation, color=(1, 1, 1), method=GL_LINES):  # fix for +/- root etc TODO
        array = []
        grid_steps = (self.range * 100)
        # y = ""

        for x in numpy.linspace(-self.range, self.range, grid_steps):
            try:
                y = eval(equation)
                # print("LITERAL: ", y)
            except ValueError:
                pass
            except ZeroDivisionError:
                pass
            else:
                # print(x, self.size, self.cx, y, self.size, self.cy)
                array.append(((x * self.size + self.cx), (y * self.size + self.cy)))

        glColor3f(color[0], color[1], color[2])
        self.gui.refresh2d()
        glBegin(method)
        for i in range(len(array) - 1):
            glVertex2f(array[i][0], array[i][1])
            if i < len(array):
                glVertex2f(array[i + 1][0], array[i + 1][1])

        glEnd()
        self.gui.refresh3d()
        
    def BoxAndWhisker(self, box_data, color=(1, 1, 1), method=GL_LINES):
        
        m1, q1, q2, q3, m2 = box_data[0], box_data[1], box_data[2], box_data[3], box_data[4]
        print("THESE:", [m1, q1, q2, q3, m2])
        
        self.gui.refresh2d()
        glColor3f(color[0], color[1], color[2])
        glScale(45, 45, 45)
        glBegin(method)
        glVertex2f(0.8, float(m1))
        glVertex2f(1.2, float(m1))
        glVertex2f(1, float(m1))
        glVertex2f(1, float(q1))
        glVertex2f(0.8, float(q1))
        glVertex2f(0.8, float(q3))
        glVertex2f(1.2, float(q3))
        glVertex2f(1.2, float(q1))
        glVertex2f(0.8, float(q1))
        glVertex2f(0.8, float(q2))
        glVertex2d(1.2, float(q2))
        glVertex2d(1.2, float(q3))
        glVertex2d(1.0, float(q3))
        glVertex2d(1.0, float(m2))
        glVertex2d(0.8, float(m2))
        glVertex2d(1.2, float(m2))
        glEnd()
        
        self.gui.refresh3d()
        
        
        

class GUI(object):  # FIX TRANCPARENCY IN IDENTITY TODO

    def __init__(self, parent=None):
        super(GUI, self).__init__()
        object.__init__(self)

        self.GraphPlot = parent
        
        self.Graphing = self.GraphPlot.Graphing
        print("GUIGRAPHING", self.Graphing)
        # self.Ptolemy = parent.parent
        print("GUI GRAPHING : " + str(self.Graphing))
        print("GUI GRAPHPLOT : ", str(self.GraphPlot))
        # print("GUI PTOLEMY : " + str(self.GraphPlot))

        self.user = cmdline('whoami')[0: -1]
        self.platform = cmdline("uname -o")[0: -1]
        self.nodename = cmdline('uname -n')[0: -1]

        self.fonts = [GLUT_BITMAP_8_BY_13, GLUT_BITMAP_9_BY_15, GLUT_BITMAP_TIMES_ROMAN_10, GLUT_BITMAP_HELVETICA_10,
                      GLUT_BITMAP_HELVETICA_12
                      ]

    def refresh2d(self):
        glViewport(0, 0, self.GraphPlot.g_Width, self.GraphPlot.g_Height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.GraphPlot.g_Width, 0.0, self.GraphPlot.g_Height, 0.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def refresh3d(self):
        glLoadIdentity()
        gluLookAt(0, 0, self.GraphPlot.g_fViewDistance, 0, 0, 0, -.1, 0, 0)  # -.1,0,0
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.GraphPlot.zoom, float(self.GraphPlot.g_Width) / float(self.GraphPlot.g_Height), self.GraphPlot.g_nearPlane, self.GraphPlot.g_farPlane)
        glMatrixMode(GL_MODELVIEW)
        self.GraphPlot.polarView()

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

    def label3d(self, x, y, z, text, font=GLUT_BITMAP_8_BY_13):
        blending = False
        if glIsEnabled(GL_BLEND):
            blending = True

        glEnable(GL_BLEND)
        glRasterPos3f(x, y, z)
        for ch in text:
            glutBitmapCharacter(font, ctypes.c_int(ord(ch)))

        if not blending:
            glDisable(GL_BLEND)

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

            glColor3f(self.GraphPlot.colors[icolor][0], self.GraphPlot.colors[icolor][1], self.GraphPlot.colors[icolor][2])
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

class GraphPlot(object):

    def __init__(self, equation=None, parent=None):
        super(GraphPlot, self).__init__()
        object.__init__(self)

        self.Ptolemy = parent
        self.equation = equation

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
        glutCreateWindow("Archimedes GraphPlot - Ptolemy")
        # glutCloseFunc(self.close)
        # Initialize OpenGL graphics state

        self.init()

        # Register callbacks
        glutReshapeFunc(self.reshape)
        glutDisplayFunc(self.display)
        glutMouseFunc(self.mouse)
        glutMotionFunc(self.motion)
        glutKeyboardFunc(self.keyboard)
        glutIdleFunc(glutPostRedisplay)
        # glutCreateMenu(processMenuEvents)
        # self.printHelp()
        # glutTimerFunc(10, self.timerEvent, 1)

        # self.gui = GUI(parent=self)

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
        # self.resetView()


        # gui.bargraph(150, g_Height/2, 350, 150, [(0, "zero"), (1, "one"), (2, "two"), (3, "three"), (4, "four")], (1, 0, 0), "nexttime", "trythis")#, "Vertical")
        # ~ Plot2d = Graphing(center=(g_Width/2, g_Height/2), size=2)
        # Plot2d = Graphing(['sqrt(3364 - x ** 2)', '-(sqrt(3364 - x ** 2))', "50 * sin(0.1 * x)"], grid_range=100, step=10, center=(self.g_Width/2, self.g_Height/2), size=2
# , parent=self)
        # Plot3d = Graphing(equation=["sin(x) + cos(y)", "x + y"], center=(0, 0, 0), grid_range=10, step=1, color=(1, 0, 0), size=0.25)
        # Plot3d = Graphing(equation=["sin(x) + cos(y)", "x + y"], parent=self)

        # plot = Graphing(equation=self.equation, size=1, parent=self)
        self.gui = GUI(parent=self)
        # self.input_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        # Stats = SP()
        # self.boxplot_data = Stats.boxplot_data(self.input_list)
        # plot = Graphing(boxplot_data=self.boxplot_data, size=45, parent=self)
        self.gui.percentarc(50, 50, 5, 10, 0, 45, 0.125, self.red, title=None, sides=36, loops=36, method=GL_FILL)
        
        # plot = Graphing()



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

    def timerEvent(self):
        glRotate(10, 0, 1, 0)
        glutPostRedisplay()

    def close(self):
        del(self)


if __name__ == "__main__":

    Graph = GraphPlot()

    # Turn the flow of control over to GLUT
    # glutMainLoop()