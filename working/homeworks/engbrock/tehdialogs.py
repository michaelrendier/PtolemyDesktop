from tkinter import *
from tkinter.font import Font
from tkinter import Menu
from tkinter import filedialog
from tkinter import ttk


class main():
	
	def __init__(self, parent=None):
		self.window = Tk()
		# self.window.overrideredirect(True)
		self.window.geometry("700x500+150+150")
		# self.window.wm_attributes('-type', 'splash')
		
		
		# text=Text()#window.attributes('-fullscreen',True)
		self.text = Text(self.window, blockcursor=True, width=100, height=20, cursor="arrow", wrap=WORD)
		# self.text.pack()
		
		self.initUI()
		
		self.window.mainloop()
	
	def close(self):
		self.window.destroy()
	
	
	def hi(self):
		a = "hi"
		self.text.insert(INSERT, a)
	
	
	def Opener(self):
		# filedialog.Toplevel.wm_overrideredirect(self)
		# filedialog.Toplevel.wm_manage(self, self.window)
		self.window.filename = filedialog.askopenfilename(initialdir='/home/stevie/Python/diary', title="pick a file",)
		
		print(self.window.filename)
		try:
			with open(self.window.filename, 'r') as f:
				doc = f.read()
				self.text.insert(INSERT, doc)
		except:
			pass
	
	
	def initUI(self):
		
		myfont = Font(family="Ubuntu Mono Regular", size=15)
		menubar = Menu(self.window, background="gray11", foreground="blue", font=myfont)
		# menubar=Menu(window,font=myfont)
		
		filemenu = Menu(menubar, background="gray11", foreground="blue", font=myfont, tearoff=0)
		# filemenu=Menu(menubar,font=myfont,tearoff=0)
		
		filemenu.add_command(label="New", command=self.hi)
		filemenu.add_command(label="Open", command=self.Opener)
		filemenu.add_command(label="Save", command=self.hi)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.close)
		menubar.add_cascade(label="File", menu=filemenu)
		
		# self.window.attributes('-fullscreen', True)
		self.window.title('TifEdit 1000')
		
		self.window.config(background="gray11")
		
		self.window.option_add("*background", "black")
		self.window.option_add("*foreground", "blue")
		self.window.config(menu=menubar)
		
		mylist = Listbox(self.window)
		# print("WHAOAOAOAO", mylist['style'])
		print("TAICWHTSOE", mylist.)
		
		
		style = ttk.Style()
		print("THISONE", style.theme_names())
		style.configure("TLabel", foreground="blue")
		style.configure("TText", background="gray11", foreground="blue")
		style.configure("Text", background="black", foreground="blue")
		style.configure("Menu", background="gray11", foreground="blue")
		style.configure("TMenu", background="gray11", foreground="blue")
		style.configure("TEntry", background="gray11", foreground="blue")
		style.configure("TMenubutton", background="gray11", foreground="blue")
		style.configure("TButton", background="gray11", foreground="blue")
		style.configure("TFrame", background="black", foreground="blue")
		style.configure("Frame", background="gray11", foreground="blue")
		style.configure("Button", background="gray11", foreground="blue")
		style.configure("TScrollbar", background="#eee", foreground="blue")
		style.configure("TListbox", background="gray11", foreground="blue")
		style.configure("Listbox", background="gray11", foreground="blue")

		style.configure("TMessagebox", background="gray11", foreground="blue")
		style.configure("Messagebox", background="gray11", foreground="blue")
		style.configure("Entry", background="gray11", foreground="blue")
		style.configure("TDialogbox", background="gray11", foreground="blue")
		style.configure("TWidget", background="gray11", foreground="blue")
		style.configure("Widget", background="gray11", foreground="blue")
		style.configure("Commondialog", background="gray11", foreground="blue")
		style.configure("Dialogbox", background="gray11", foreground="blue")
		style.configure("TSpinbox", background="gray11", foreground="blue")
		style.configure("Spinbox", background="gray11", foreground="blue")
		style.configure("Tspinbox", background="gray11", foreground="blue")
		style.configure("Combobox", background="gray11", foreground="blue")
		style.configure("Tcombobox", background="gray11", foreground="blue")
		style.configure("TToplevel", background="gray11", foreground="blue")
		frame = Frame(self.window)
		frame.pack()
		
		myfont=Font(family="Ubuntu Mono Regular",size=15)
		
		text = Text(self.window, blockcursor=True, width=50, height=20, cursor="arrow")
		
		# text.configure(background="black",foreground="blue")
		text.configure(insertbackground="greenyellow")
		text.configure(font=myfont)
		
		# closebutton = Button(self.window, text="x", justify=RIGHT, command=self.close, compound=RIGHT)
		# closebutton.place(x=1320, y=650)

		text.pack()
		

# window.mainloop()
if __name__ == "__main__":
	main()