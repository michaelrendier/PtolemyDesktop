#!/usr/bin/python3

import sys, os
print(sys.version)
print(os.getcwd())
from tkinter import *

class fe(object):
	def __init__(self,master):
		self.b=Button(master,justify = LEFT)
		photo=PhotoImage(file="neworleans.jpg")
		self.b.config(image=photo,width="10",height="10")
		self.b.pack(side=LEFT)
root = Tk()
front_end=fe(root)
root.mainloop()
