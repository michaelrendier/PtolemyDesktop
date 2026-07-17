#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
#Builtins
from math import *
import time

from PyQt6.QtCore import QThread, pyqtSignal, QObject

#OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLE import *
# import OpenGL_accelerate as glAcc
# import OpenGLContext

#Installed
import psutil, ast, numpy, threading

from PIL import Image, ImageDraw, ImageFont



class Results(QObject):

    def __init__(self, results, parent=None):
        super(Results, self).__init__(parent)
        QObject.__init__(self)
        self.results = results
        # print('self.result:', self.results)

class NETThread(QThread):

    #Signals
    netStatReport = pyqtSignal(tuple)


    def __init__(self, interface, parent=None):
        super(NETThread, self).__init__()
        QThread.__init__(self)

        print("WORK THREAD")
        # print("CALLBACK: ", callback)

        self.NETCore = parent
        # print(self.NETCore)
        self.interface = interface
        self.netStatDict = {}

        # self.netStatFinished.connect(callback)



    def run(self):

        while True:

            for i in range(4):
                print(i, self.interface[i])

                netStats1 = psutil.net_io_counters(True)
                # print(netStats1)
                netTx = netStats1[self.interface[i].decode()][0]
                netRx = netStats1[self.interface[i].decode()][1]
                time.sleep(0.01)

                netStats2 = psutil.net_io_counters(True)
                nextnetTx = netStats2[self.interface[i].decode()][0]
                nextnetRx = netStats2[self.interface[i].decode()][1]

                inputTx = int(nextnetTx) - int(netTx)
                inputRx = int(nextnetRx) - int(netRx)

                self.netStatDict[self.interface[i]] = (inputTx, inputRx)

            # print("RESULTS", (inputTx, inputRx))
            # self.answer = Results((inputTx, inputRx))
            # self.NETCore.netStatRate = (inputTx, inputRx)
            # print("NETSTATDICT : ", self.netStatDict)
            self.NETCore.returnRate(self.netStatDict)
            # self.netStatFinished.emit((inputTx, inputRx))

            # return (inputTx, inputRx)



class Core(object):

    def __init__(self, size=0.5, parent=None):
        super(Core, self).__init__()
        object.__init__(self)
        self.size = size
        # glRotate(90, 0, 0, 1)

        self.Viewer = parent
        # self.Ptolemy = parent.parent
        # print("CORE VIEWER : " + str(self.Viewer))
        # print("CORE PTOLEMY : " + str(self.Ptolemy))

        # self.Kernel = KernelCore(0, parent=self)
        self.CPU = CPUCore(3, parent=self)
        self.RAM = RAMCore(4, parent=self)
        self.VMEM = VMEMCore(5, parent=self)
        self.GPU = GPUCore(6, parent=self)
        # self.NET = NETCore(7, parent=self)
        # self.PROC = PROCCore(8, parent=self)

        # self.show(KernelCore(0))
        # self.show(CPUCore(7))
        # # self.show(CPUCore(7))
        # self.show(RAMCore(8))
        # self.show(VMEMCore(9))
        # self.show(GPUCore(10))
        # # self.show(NETCore(11))
        # self.show(PROCCore(12))

        self.initUI()

    def initUI(self):
        # self.Kernel.build()
        self.CPU.build()
        self.RAM.build()
        self.VMEM.build()
        self.GPU.build()
        # self.NET.build()
        # self.PROC.build()
        pass

    # def show(self, obj):
    #     Show.add(obj)


# Core FIX GUI FOR EACH WITH X AND Y TODO
class KernelCore(object):

    def __init__(self, place, size=0.5, parent=None):
        super(KernelCore, self).__init__()
        object.__init__(self)

        self.Core = parent
        self.Viewer = parent.Viewer
        # self.Ptolemy = parent.parent.parent
        print("KERNEL CORE : " + str(self.Core))
        print("KERNEL VIEWER : " + str(self.Viewer))
        # print("KERNEL PTOLEMY : " + str(self.Ptolemy))

        self.place = place
        self.size = size
        self.id = id(self)
        # Kernel Stats
        self.text = self.Viewer.cmdline("dmesg | tail -15")
        self.txt2img(self.text)

        self.image = Image.open("kerneltex.jpg")  # mcp-2.jpg")#MCP_3D_Graphic.jpg")#kerneltex.jpg")
        self.ix = self.image.size[0]
        self.iy = self.image.size[1]
        self.image = self.image.convert("RGBA").tobytes("raw", "RGBA")

        self.LoadTextures(self.image)

        self.build()

    # self.show(self, self.id)

    def build(self):
        # Kernel
        glColor3f(0.5, 0.5, 0.5)
        glScale(self.size, self.size, self.size)
        # apply texture
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        # glEnable(GL_TEXTURE_GEN_S)
        # glEnable(GL_TEXTURE_GEN_T)

        self.Viewer.gui.Cylinder(0, 0, 0, 2, 2, 8, 36, 36)
        # Cylinder(0, 0, 0, 1, 1, 1, 36, 36)
        # glTranslate(0, 0, 1)
        # Cylinder(0, 0, 0, 1, 0, 1, 36, 36)
        # glTranslate(0, 0, 1)
        # Cylinder(0, 0, 0, 0, 1, 1, 36, 36)
        # glTranslate(0, 0, 1)
        # Cylinder(0, 0, 0, 1, 1, 2, 36, 36)

        # arcCylinder(0, 0, 0, self.place, self.place + 1, 36, 36, 0, 360, 5, GLU_FILL)

        glPopMatrix()
        # glDisable(GL_TEXTURE_GEN_S)
        # glDisable(GL_TEXTURE_GEN_T)
        glDisable(GL_TEXTURE_2D)
        glutPostRedisplay()
        glScale(1 / self.size, 1 / self.size, 1 / self.size)

    def buildGUI(self):
        self.Viewer.gui.refresh2d()
        # glColor3f(1, 1, 1)
        # gui.partialdisk(70, 115, 0, 5, 36, 36, 0, 360)
        self.Viewer.gui.refresh3d()

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

        # # Create MipMapped Texture
        # glBindTexture(GL_TEXTURE_2D, int(textures[2]))
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST)
        # gluBuild2DMipmaps(GL_TEXTURE_2D, 3, self.ix, self.iy, GL_RGBA, GL_UNSIGNED_BYTE, image)

        # Create Linear Filtered Texture
        glBindTexture(GL_TEXTURE_2D, int(textures[1]))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, self.ix, self.iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)

    def loadimage(self, imagename):
        image = Image.open(imagename)  # mcp-2.jpg")#MCP_3D_Graphic.jpg")#kerneltex.jpg")
        self.ix = image.size[0]
        self.iy = image.size[1]
        image = image.convert("RGBA").tobytes("raw", "RGBA")

        return image

    def getdmesg(self):
        text = ""
        with open("/var/log/dmesg", "r") as f:
            text = f.read()

        return text

    def txt2img(self, text, rotate_angle=180):
        """Render label as image."""
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
        imgOut = Image.new("RGB", (20, 49), (0, 0, 0))

        # calculate space needed to render text
        draw = ImageDraw.Draw(imgOut)
        sizex, sizey = draw.textsize(str(text), font)

        imgOut = imgOut.resize((sizex, sizey))

        # render label into image draw area
        draw = ImageDraw.Draw(imgOut)
        # item = random.randrange(6)
        # print item
        # if item == 0: item = 1
        draw.text((0, 0), str(text), (255, 255, 255), font)
        # draw.text((0, 0), text, (colors[item + 1][0] * (254/item), colors[item + 1][1] * (254/item), colors[item + 1][2] * (254/item)), font)
        imgOut = imgOut.transpose(Image.FLIP_LEFT_RIGHT)
        if rotate_angle:
            imgOut = imgOut.rotate(rotate_angle)

        # imgOut.convert('RGB')
        imgOut.save('kerneltex.jpg')

    # return imgOut

    # def show(self, object, objid):
    #     Show.add(object, objid)

    # def hide(self):
    #     Show.remove(self.id)


class CPUCore(object):

    def __init__(self, place, size=0.5, parent=None):
        super(CPUCore, self).__init__()
        object.__init__(self)

        self.Core = parent
        self.Viewer = parent.Viewer

        self.place = (place + 1) * 0.5
        self.place0 = place
        self.size = size
        self.id = id(self)
        # CPU Stats
        self.cpuCount = psutil.cpu_count()
        self.cpuPercent = psutil.cpu_percent(None, True)
        self.cpuAngle = 360.0 / self.cpuCount

        self.build()

    # self.show(self, self.id)

    def build(self):  # ADD COLOR CHANGES FOR HEIGHT DEPENDENT SHAPES TODO
        # Build CPUs
        glScale(self.size, self.size, self.size)
        for i in range(self.cpuCount):
            glColor3f(self.Viewer.colors[i + 3][0], self.Viewer.colors[i + 3][1], self.Viewer.colors[i + 3][2])
            self.Viewer.gui.percentarc3d(0, 0, 0, self.place, (self.place + 0.5), (i * self.cpuAngle), self.cpuAngle, 2, 2,
                         self.cpuPercent[i])
        glutPostRedisplay()
        glScale(1 / self.size, 1 / self.size, 1 / self.size)

    def buildGUI(self):
        # Gui Setup
        self.Viewer.gui.refresh2d()
        for i in range(self.cpuCount):
            height = ((i + self.place0) * 25) + 15

            cpucolor = (self.Viewer.colors[i + 3][0] * 0.5, self.Viewer.colors[i + 3][1] * 0.5, self.Viewer.colors[i + 3][2] * 0.5)
            self.Viewer.gui.percentbar(g_Width - 210, g_Height - height, 200, 15, self.cpuPercent[i], cpucolor,
                           "CPU {}".format((i + 1)))

        self.Viewer.gui.refresh3d()
        glutPostRedisplay()

    def show(self, object, objid):
        Show.add(object, objid)


class RAMCore(object):

    def __init__(self, place, size=0.5, parent=None):
        super(RAMCore, self).__init__()
        object.__init__(self)

        self.Core = parent
        self.Viewer = parent.Viewer

        self.place = (place + 1) * 0.5
        self.place0 = place
        self.size = size
        self.id = id(self)
        # RAM Stats
        self.psMem = psutil.virtual_memory()
        self.memAngle = 360.0 * (self.psMem[2] / 100.)

        self.build()

    # self.show(self, self.id)

    def build(self):
        # Build RAM Memory
        glColor3f(0, 1, 0)
        glScale(self.size, self.size, self.size)
        self.Viewer.gui.percentarc3d(0, 0, 0, self.place, self.place + 0.5, 0, 360, 1, 0, self.psMem[2])
        glScale(1 / self.size, 1 / self.size, 1 / self.size)
        glutPostRedisplay()

    def buildGUI(self):
        height = ((self.place0 + psutil.cpu_count() - 1) * 25) + 15
        gui.refresh2d()
        glColor(0, 0.5, 0)
        gui.percentbar(g_Width - 210, g_Height - height, 200, 15, self.psMem[2], (0, 0.5, 0), "RAM")
        gui.refresh3d()
        glutPostRedisplay()

    def show(self, object):
        Show.add(object)


class VMEMCore(object):  # ADD PLATFORM IDENTIFICATION FOR PROPER CALLS TODO

    def __init__(self, place, size=0.5, parent=None):
        super(VMEMCore, self).__init__()
        object.__init__(self)

        self.Core = parent
        self.Viewer = parent.Viewer

        self.place = (place + 1) * 0.5
        self.place0 = place
        self.size = size
        self.id = id(self)
        # SWAP Stats
        self.psSwap = psutil.swap_memory()

        self.build()

    # self.show(self, self.id)

    def build(self):
        # Build SWAP/Virtual Memory
        glColor3f(1, 1, 0)
        glScale(self.size, self.size, self.size)

        self.Viewer.gui.percentarc3d(0, 0, 0, self.place, self.place + 0.5, 0, 360, 1, 0, self.psSwap[3])
        glScale(1 / self.size, 1 / self.size, 1 / self.size)

        glutPostRedisplay()

    def buildGUI(self):
        # Gui Setup
        height = ((self.place0 + psutil.cpu_count() - 1) * 25) + 15
        gui.refresh2d()
        gui.percentbar(g_Width - 210, g_Height - height, 200, 15, self.psSwap[3], (0.5, 0.5, 0), "VMEM/SWAP")
        gui.refresh3d()
        glutPostRedisplay()

    def show(self, object):
        Show.add(object)


class NETCore(object):  # FIX MARQUEE MONITOR FUNCTION, PUT FILE MONITORING INTO A WORKTHREAD. TODO

    def __init__(self, place, size=0.5, parent=None):
        super(NETCore, self).__init__()
        object.__init__(self)

        # print("Core: ", self)

        self.Core = parent
        self.Viewer = parent.Viewer

        self.place0 = place
        self.place = (place + 1) * 0.5
        self.size = size
        self.id = id(self)
        # NET Stats
        self.netIF = self.Viewer.cmdline(b'ls /sys/class/net/').split(b"\n")[:-1]
        self.netCount = len(self.netIF)
        self.netAngle = 360.0 / self.netCount
        self.netStatRate = {}
        # for i in self.netIF:
        #     self.netStatRate[i] = (0, 0)


        self.netThread = NETThread(self.netIF, self)
        self.netThread.start()

        self.build()

    def build(self):  # CREATE DUAL INPUT OPPOSING ARC TODO

        # Build Interfaces
        glScale(self.size, self.size, self.size)
        for i in range(len(self.netIF)):
            glColor3f(self.Viewer.colors[i + 3][0], self.Viewer.colors[i + 3][1], self.Viewer.colors[i + 3][2])

            self.Viewer.gui.arcCylinder(0, 0, 0, self.place, (self.place + 0.5), 36, 45, (i * self.netAngle), self.netAngle, 0,
                        GLU_SILHOUETTE)
            glColor3f(1, 1, 1)

            # netRate = self.rate(self.netIF[i])
            # self.rate(self.netIF[i])
            print("OUT OF THREAD", self.netStatRate)
            try:
                self.netRate = self.netStatRate[self.netIF[i]]
                print("NETRATE: ", self.netRate)

                if self.netRate[0] + self.netRate[1] > 0:
                    self.Viewer.gui.arcCylinder(0, 0, 0, self.place, (self.place + 0.5), 36, 36, (i * self.netAngle),
                                                self.netAngle, 1)

            except KeyError:
                pass



            # except IndexError:
            #     pass

        glScale(1 / self.size, 1 / self.size, 1 / self.size)
        glutPostRedisplay()

    def buildGUI(self):  # create marquee monitor TODO
        # Gui Setup
        gui.refresh2d()
        for i in range(len(self.netIF)):
            height = ((i + self.place0 + 1) * 25) + 15
            netcolor = (colors[i + 3][0] * 0.5, colors[i + 3][1] * 0.5, colors[i + 3][2] * 0.5)

            # netRate = self.rate()

            # marquee(g_Width - 210, g_Height - height + 15, 200, 15, input)

            gui.title(g_Width - 210, g_Height - height + 15, 200, "{}".format(self.netIF[i]))
            gui.rect(g_Width - 210, g_Height - height, 200, 15)

        gui.refresh3d()
        glutPostRedisplay()

    def returnRate(self, results):
        print("Return RATE: ", results)
        # self.netStatRate = resultsObj.result
        for i in results:
            self.netStatRate[i] = results[i]
        print(self.netStatRate)
        # print("RETURNING!")

    def rate(self, interface):

        # self.Rates = NETThread(self, 1, interface)
        # self.Rates.netStatFinished.connect(self.returnRate)
        # self.Rates.start()

        # netStats1 = psutil.net_io_counters(True)
        # # print(netStats1)
        # netTx = netStats1[interface.decode()][0]
        # netRx = netStats1[interface.decode()][1]
        # time.sleep(0.1)
        #
        # netStats2 = psutil.net_io_counters(True)
        # nextnetTx = netStats2[interface.decode()][0]
        # nextnetRx = netStats2[interface.decode()][1]
        #
        # inputTx = int(nextnetTx) - int(netTx)
        # inputRx = int(nextnetRx) - int(netRx)
        #
        # return (inputTx, inputRx)
        pass

    def show(self, object):
        Show.add(object)


class PROCCore(object):

    def __init__(self, place, size=0.5, parent=None):
        super(PROCCore, self).__init__()
        object.__init__(self)

        self.Core = parent
        self.Viewer = parent.Viewer

        self.place = (place + 1) * 0.5
        self.place0 = place
        self.size = size
        self.id = id(self)
        # Processes and percentages
        self.proc = psutil.process_iter()
        self.procList = []
        for i in self.proc:
            self.procList.append(i)
        self.procNum = len(self.procList)
        self.procAngle = 360.0 / self.procNum
        self.procColor = 0
        self.procSquare = ceil(sqrt(self.procNum))
        self.procNetNum = len(self.Viewer.cmdline(b'ls /sys/class/net/').split(b"\n")[:-1])

        # self.buildGUI()
        self.build()

    # self.show(self, self.id)

    def build(self):
        # Build Processes
        glScale(self.size, self.size, self.size)
        for i in range(self.procNum):
            try:
                procPercent = self.procList[i].cpu_percent()
                procStat = self.procList[i].status()
            except psutil.NoSuchProcess:
                pass
            else:
                if procStat == 'running':  # psutil.STATUS_RUNNING green 0
                    glColor3f(0, 1, 0)

                elif procStat == 'sleeping':  # psutil.STATUS_SLEEPING blue 1
                    glColor3f(0, 0.5, 0.5)

                elif procStat == 'stopped':  # psutil.STATUS_STOPPED red 2
                    glColor3f(1, 0, 0)

                elif procStat == 'zombie':  # psutil.STATUS_ZOMBIE grey 3
                    glColor3f(0.5, 0.5, 0.5)

                elif procStat == 'dead':  # psutil.STATUS_DEAD dark grey 4
                    glColor3f(0.1, 0.1, 0.1)

                elif procPercent > 0:
                    glColor3f(1, 1, 1)

                # Clock Version
                self.Viewer.gui.partialDisk(0, 0, 0, 0, (self.place + 0.5) * (procPercent / 100.0), 36, 36, i * self.procAngle,
                            self.procAngle, GLU_FILL)

                # Ring Version
                self.Viewer.gui.arcCylinder(0, 0, 0, self.place, (self.place + 0.5), 36, 36, i * self.procAngle, self.procAngle,
                            2 * (procPercent / 100.0), GLU_FILL)

                if procPercent > 0:
                    glColor3f(0, 1, 0)
                    self.Viewer.gui.partialDisk(0, 0, 1, self.place, (self.place + 0.5), 36, 36, i * self.procAngle, self.procAngle,
                                GLU_FILL)

                else:
                    glColor3f(0.5, 0.5, 0.5)
                    self.Viewer.gui.partialDisk(0, 0, 1, self.place, (self.place + 0.5), 36, 36, i * self.procAngle, self.procAngle,
                                GLU_SILHOUETTE)
        glScale(1 / self.size, 1 / self.size, 1 / self.size)
        glutPostRedisplay()

    def buildGUI(self):  # ADD COLORS FOR TYPE OF PROCESS (IE GREEN FOR ZOMBIE) TODO
        # height =
        gui.refresh2d()
        gui.title(g_Width - 210, g_Height - ((self.place0 + psutil.cpu_count() + self.procNetNum - 2) * 25), 200,
                  "Proc #{} ({})".format(self.procNum, self.procSquare))
        glColor3f(1, 1, 1)
        gui.rect(g_Width - 210, g_Height - ((self.place0 + psutil.cpu_count() + self.procNetNum - 2) * 25),
                 self.procSquare * 10 - 1, -self.procSquare * 10 - 1)

        count = self.procNum
        gridList = [(x, y) for x in range(int(self.procSquare)) for y in range(int(self.procSquare))]
        for i in range(len(self.procList)):
            try:
                procstat = self.procList[i].status()
                procpercent = self.procList[i].cpu_percent()
            except psutil.NoSuchProcess:
                pass
            else:

                if procstat == 'running':  # psutil.STATUS_RUNNING green 0
                    glColor3f(0, 1, 0)

                elif procstat == 'sleeping':  # psutil.STATUS_SLEEPING blue 1
                    glColor3f(0, 0, 1)

                elif procstat == 'stopped':  # psutil.STATUS_STOPPED red 2
                    glColor3f(1, 0, 0)

                elif procstat == 'zombie':  # psutil.STATUS_ZOMBIE grey 3
                    glColor3f(0.5, 0.5, 0.5)

                elif procstat == 'dead':  # psutil.STATUS_DEAD dark grey 4
                    glColor3f(0.1, 0.1, 0.1)

                elif procpercent > 0:
                    glColor3f(1, 1, 1)

                elif count <= 0:  # unused black 5
                    glColor3f(0, 0, 0)

                gui.rect(g_Width - 210 + (gridList[i][0] * 10),
                         g_Height - ((self.place0 + psutil.cpu_count() + self.procNetNum - 2) * 25) - (
                                     gridList[i][1] * 10), 8, -8)
                count -= 1

    def show(self, object, objid):
        Show.add(object, objid)


class GPUCore(object):  # TODO

    def __init__(self, place, size=0.5, parent=None):
        super(GPUCore, self).__init__()
        object.__init__(self)

        self.Core = parent
        self.Viewer = parent.Viewer

        self.place = (place + 1) * 0.5
        self.size = size
        self.id = id(self)
        # GPU Stats

        self.build()

    # self.show(self, self.id)

    def build(self):
        # Build GPU RAM
        glScale(self.size, self.size, self.size)
        gpuInfo = self.Viewer.cmdline("glxinfo | grep 'Video memory'")
        # code = "glxinfo | grep 'Video memory' > tmp.txt"
        # os.system(code)
        # f = open("tmp.txt", "r")
        # gpuInfo = f.read()
        gpuNum = []
        [gpuNum.append(i) for i in gpuInfo if i.isdigit()]
        gpuMem = "".join(gpuNum)
        code2 = "intel_gpu_top"
        glColor3f(0, 0, 0.5)
        self.Viewer.gui.arcCylinder(0, 0, 0, self.place, self.place + 0.5, 36, 36, 0, 360, 0, GLU_SILHOUETTE)
        glScale(1 / self.size, 1 / self.size, 1 / self.size)
        glutPostRedisplay()

    def buildGUI(self):
        pass

    def show(self, object):
        Show.add(object)


