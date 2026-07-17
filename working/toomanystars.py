from tkinter import *
import sys
 
old=sys.stdout
 
window=Tk()
 
class Re:
    def __init__(self,txtob):
        self.text=txtob
        self.old=sys.stdout
        sys.stdout=self.text
       
       
    def write(self,strg):
        self.strg=strg+'\n'
     
        self.text.insert(INSERT,self.strg)
        self.old.flush()
        self.text.pack()
   
txt=Text(window)
re=Re(txt)
sys.stdout=re
 
 
enter=Entry(window)
 
 
def GetterDone(event=None):
    x=enter.get()
    print(x)
   
enter.pack()   
enter.bind('<Return>',GetterDone)  
 
window.mainloop()
