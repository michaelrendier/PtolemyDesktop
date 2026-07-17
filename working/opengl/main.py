import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.uic import *

from Alexandria.Earth import Earth
from Musaeum.GLGUI import GUI

from subprocess import PIPE, Popen

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


class mainWindow(QMainWindow):
	
	def __init__(self, center=(0, 0, 0), size=1.5, parent=None):
		super(mainWindow, self).__init__(parent)
		QMainWindow.__init__(self)
		# loadUi('minimal.ui', self)
		
		self.Ptolemy = parent
		print("PYQTOPENGL PARENT: ", self.Ptolemy)
		
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
		
		self.gui = GUI(parent=self)
		
		
		
		# self.citylist = []
		# self.cx = center[0]
		# self.cy = center[1]
		# self.cz = center[2]
		# self.size = size
		# self.id = id(self)
		# self.live = ["Eureka"]
		# self.livedin = ["Bishop", "Eureka", "Brea", "Los Angeles", "Seattle", "Murfreesboro", "New Orleans",
		# 				"Pensacola", "Atlanta", "Orlando", "Redding", "Gardnerville", "Carson City", "Lawton",
		# 				"Colorado Springs", "El Paso"]
		#
		# os.system("python /home/rendier/Ptolemy/Alexandria/GoogleEarth.py")
		# print('Places Updated')
		#
		# with open('/home/rendier/Ptolemy/Alexandria/citylist.txt', 'r') as f:
		# 	self.citylist = ast.literal_eval(f.read())
		#
		# with open('/home/rendier/Ptolemy/Alexandria/locations.txt', 'r') as nf:
		# 	self.locations = ast.literal_eval(nf.read())
		#
		# # self.show(self, self.id)
		# self.build()
	
	def __del__(self):
		return
	
	def setupUI(self):
		
		self.setGeometry(0, 0, 800, 600)
		
		self.widget = QWidget()
		
		self.setCentralWidget(self.widget)
		
		self.verticalLayout = QVBoxLayout(self.widget)
		
		self.openGLWidget = QOpenGLWidget()
		self.openGLWidget.initializeGL()
		self.openGLWidget.resizeGL(651, 551)
		self.openGLWidget.paintGL = self.paintGL
		
		self.verticalLayout.addWidget(self.openGLWidget)
		self.widget.setLayout(self.verticalLayout)
		
		timer = QTimer(self)
		timer.timeout.connect(self.openGLWidget.update)
		timer.start(1000)
	
	def paintGL(self):
		glClear(GL_COLOR_BUFFER_BIT)
		glutInit()
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
		
		self.init()
		
		# Register callbacks
		# glutReshapeFunc(self.reshape)
		# glutDisplayFunc(self.display)
		# glutMouseFunc(self.mouse)
		# glutMotionFunc(self.motion)
		# glutKeyboardFunc(self.keyboard)
		# glutIdleFunc(self.timerEvent)
		# glutCloseFunc(self.__del__)
		
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
		# self.polarView()
		
		self.Earth = Earth(parent=self)
		
		# glRotate(20, 0, 1, 0)
		# glColor3f(1, 0, 0);
		# glBegin(GL_TRIANGLES);
		# glVertex3f(-0.5, -0.5, 0);
		# glVertex3f(0.5, -0.5, 0);
		# glVertex3f(0.0, 0.5, 0);
		# glEnd()
		
		# gluPerspective(45, 651 / 551, 0.1, 50.0)
		# glTranslatef(0.0, 0.0, -5)
	
	def cmdline(self, command):
		process = Popen(
			args=command,
			stdout=PIPE,
			stderr=PIPE,
			shell=True
		)
		return process.communicate()[0]
	
	def resetView(self):
		# global zoom, xRotate, yRotate, zRotate, xTrans, yTrans
		self.zoom = 65.
		self.xRotate = 0.
		self.yRotate = 0.
		self.zRotate = 0.
		self.xTrans = 0.
		self.yTrans = 0.
		# glutPostRedisplay()
	
	def polarView(self):
		glTranslatef(self.yTrans / 100., 0.0, 0.0)
		glTranslatef(0.0, -self.xTrans / 100., 0.0)
		glRotatef(-self.zRotate, 0.0, 0.0, 1.0)
		glRotatef(-self.xRotate, 1.0, 0.0, 0.0)
		glRotatef(-self.yRotate, 0.0, 1.0, 0.0)
	
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
	
	def reshape(self, width, height):
		# global g_Width, g_Height
		self.g_Width = width
		self.g_Height = height
		glViewport(0, 0, self.g_Width, self.g_Height)
	
	def keyboard(self, key, x, y):
		print("KEYBOARD PRESS: ")
		global zTr, yTr, xTr
		if (key == 'r'): self.resetView()
		# if (key == 'o'): self.Kernel.hide()
		if (key == 'q'): exit(0)
		# glutPostRedisplay()
	
	def mouse(self, button, state, x, y):
		print("MOUSE PRESS: ")
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
		# glutPostRedisplay()
	
	def timerEvent(self):
		print("timerEvent")
		glRotate(20, 0, 1, 0)
	# glutPostRedisplay()


app = QApplication(sys.argv)
window = mainWindow()
window.setupUI()
window.show()
sys.exit(app.exec_())