from tkinter import *
from tkinter.font import Font
from tkinter import Menu
from tkinter import filedialog
from tkinter import ttk
import subprocess
import textwrap
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
import smtplib


window=Tk()
style=ttk.Style(window)


 
tabcon=ttk.Notebook(window)


class Tab:
    num=0
  

def color1():
    col=['lawn green','red','deep sky blue','yellow','blue','deep pink','magenta2','spring green','slate blue']    
    Color=random.choice(col)
    return Color

def Name(x=0):
    x=int(x)
    col=color1()
    x=x+1

    x=str(x)
    color=['green','red','blue','yellow','blue']
    Name=['Bob','Joe','Jen','Stacy','Jill','Lisa','Suzy','Tony','Katie','Larry','Tom','Billy']
    name=x     #random.choice(Name) 
   
   
    style.configure("TNotebook",background="gray11");
    style.map("TNotebook.Tab",background=[("selected",col)],foreground=[("selected","black")]);
    style.configure("TNotebook.Tab",background="gray11",foreground="cyan")  
    
  


scrollbar=Scrollbar(window)
scrollbar.pack(side=RIGHT,fill=Y)


def TabMaker(event=None):

   tabnum=Tab.num+1
   Tab.num=Tab.num+1  
   str(tabnum)
    
   name=Name()  
  
   tab2=ttk.Frame(tabcon)
  
   tabcon.add(tab2,text=tabnum,padding=4)



   tabcon.pack(expand=True,fill='both')	
  
 
  # window.bind("<Alt-r>",Remember)
            
   txt=Text(tab2,blockcursor=True,width=75,height=30,wrap="word",undo=True,maxundo=500,cursor="arrow",yscrollcommand=scrollbar.set)
        
   cursorpostext=Text(tab2,width=10,height=1,wrap=CHAR)# text=text.index("end-1c linestart"))
   cursorpostext.configure(background="black",foreground="greenyellow")
   
   parameters=Entry(tab2,width=64,text='parameters')
   parameters.configure(background="black",foreground="cyan")
   commander=Entry(tab2,width=64,text='commands')
   commander.configure(background="gray7",foreground="yellow")
   paraLabel=Label(tab2,text="args")
   paraLabel.configure(background="black",foreground="blue")
   commandLabel=Label(tab2,text="cmd")
   commander.configure(background="black",foreground="blue")



 
   def Finder(event=None):


        

    def Lister(event=None):

        start='1.0'

		
        while 1:
         #Searchbox=Entry(popup,width=75)
            search=Searchbox.get()
            C=len(search)
            C=str(C)


            pos=txt.search(search,start,stopindex=END,nocase=True,count=C)
            txt.tag_add("search",str(start)+" "+"wordstart",str(start)+" "+"wordend")
        #scrch=pos.get()
            if not pos:
                break
            listbox.insert(END,pos)
            start=pos+"+1c"
            listbox.pack()
        
	
    def Link(event=None):
         c=listbox.get(ACTIVE)
         txt.see(c)



    def destroyer(event=None):
        

        popup.destroy()

    

    myfont=Font(size=18)
    labelfont=Font(size=15)
    popup=Toplevel(window)
    popup.title("Search Results")
    popup.attributes('-fullscreen',True)
    popup.bind('<Alt-z>',destroyer)
    SearchLabel=Label(popup,text='input search')
    SearchLabel.configure(background="black",foreground="cyan",font=labelfont)
    SearchLabel.pack()
    Searchbox=Entry(popup,width=75,font=myfont)
    Searchbox.configure(background="black",foreground="cyan")
    Searchbox.pack()
    Searchbox.bind('<Return>',Lister)
    
        
    listbox=Listbox(popup,height=40,width=75,font=myfont)
    listbox.configure(background="black",foreground="cyan")
    listbox.bind('<Return>',Link)


   
      
   def Eclient(rcvr='',sbjt="",att='no'):

         def EGetter(event=None):
            me='stevieengbrock@zoho.com'
            msgtxt=txt.get(1.0,END+"-1c")
            sub=subEnt.get()
            rcvr=rcvrEnt.get()
            attachment=attEnt.get()
            msg=MIMEMultipart()
            if attachment=="y":
               filename=filedialog.askopenfilename(initialdir='/home/stevie/Python/diary',title="pick a file",filetypes=(("python","*.py"),("plain txt","*.txt"),("any","*.*")))
               try:
                   with open(filename,'r') as f:
                       attachment=MIMEText(f.read())
                   attachment.add_header('Content-Disposition','attachment',filename=filename)
                   msg.attach(attachment)
               except:
                   pass 
           # else:
             #   pass
        
            if sub=="":
                pass 
    
    
            if rcvr=='mom':
                rcvr='thereseengbrock@zoho.com'
            if rcvr=='julie':
                rcvr='greimer123@yahoo.com'
            if rcvr=='brent gmail':
                rcvr='georgesonbrent@gmail.com'
            if rcvr=='txt brent' or rcvr=='text brent':
                rcvr='3166805312@vtext.com'
            if rcvr=='me gmail':
                rcvr='stevieengbrock@gmail.com'
            if rcvr=='me zoho' or rcvr=='me':
                rcvr='stevieengbrock@zoho.com'
            if rcvr=='txt me' or rcvr=='text me':
                rcvr="3165702643@vtext.com"
            if rcvr=="kindle" or rcvr=="book":
                rcvr="stevieengbrock@kindle.com"
    
    
            msg.attach(MIMEText(msgtxt))
           # mess=str(msg.attach(MIMEText(msgtxt)))
           # msg.attach(attachment)
            msg['Subject']=sub
            msg['From']=me
            msg['To']=rcvr
            server = smtplib.SMTP_SSL('smtp.zoho.com',465)
            server.login('stevieengbrock@zoho.com','spiritlove777')
            server.sendmail(me,[rcvr],msg.as_string())#mess
            server.quit
            pop.destroy()

    
        
         myfont=Font(size=18)
         labelfont=Font(size=15)
   
        
        
         pop=Toplevel(window)
         pop.title("Email Info")
    
    
         def destroy(event=None):
            pop.destroy()  
   



         pop.bind('<Alt-z>',destroy)
         sublabel=Label(pop,text="Enter Subject",foreground="cyan",font=labelfont )
         sublabel.pack()
    
         subEnt=Entry(pop,foreground="cyan",font=myfont)
         subEnt.pack()
    

    

      
         
    
    
         rcvrlabel=Label(pop,text="Email Address",foreground="cyan",font=labelfont)
         rcvrlabel.pack()
       
    
         rcvrEnt=Entry(pop,foreground="cyan",font=myfont)
         rcvrEnt.pack()
    
    
   #rcvr=rcvrEnt.get()

       

         attlabel=Label(pop,text="Got Attachment",foreground="cyan",font=labelfont)
         attlabel.pack()
       
         attEnt=Entry(pop,foreground="cyan",font=myfont)
         attEnt.pack()
    
         send=Button(pop,text="Send",command=EGetter)
         send.pack()


    

    
   def AlmostFullScreen(event):
        
      
        paraLabel.place_forget()
        parameters.place_forget()
        commander.place_forget()
        commandLabel.place_forget()
        myfont=Font(size=15)
        txt["width"]="120"
        txt["height"]="40"
        txt["font"]=myfont


   def PrintSize(event):
       
        commander.place(x=335,y=633)
        commandLabel.place(x=290,y=633)
        parameters.place(x=335,y=663)
        paraLabel.place(x=290,y=663)
        myfont=Font(size=10)
        txt["width"]="75"
        txt["height"]="30"
        txt["font"]=myfont

    
   def cursorpos():
        pos=txt.index(INSERT)#"end-1c linestart")
        cursorpostext.delete(1.0,END)
        cursorpostext.insert(INSERT,pos)
        cursorpostext.after(100,cursorpos)    


   cursorpostext.pack()

   txt.configure(insertbackground="red")
   txt.configure(foreground='cyan')
   txt.pack()
     

   cursorpostext.after(100,cursorpos)
  


    
   def GoTo():
       goer=parameters.get()
       goer=goer+".1"
       txt.see(goer) 


   def Commander(event=None):
       command=commander.get()
    
       if command=='go to':
           GoTo()


   def UnDo(event=None):
       try:
           text.edit_undo()
       except:
            pass


   def ReDo(event=None):
        try:
            txt.edit_redo()
        except:
            pass


     
	
   def Opener(event=None):
       txt.delete(1.0,END)
       tab2.filename=filedialog.askopenfilename(initialdir='/home/stevie/Python/diary',title="pick a file",filetypes=(("python","*.py"),("plain txt","*.txt"),("any","*.*")))
       print(tab2.filename)
       try:
            with open(tab2.filename,'r') as f:
                doc=f.read()
                txt.insert(INSERT,doc)
                
       except:
            pass


   def TermPrint(event=None):
       subprocess.call('clear')
       doc=txt.get(1.0,END+"-1c")
	
       print(doc)


   def Printer(event=None):
        doc=txt.get(1.0,END+"-1c")
    
	
        name="temp.txt"
        path="/home/stevie/Python/diary"
        file=name
        with open(file,'w') as f:
            f.write(doc)
    #docbytearray=bytearray(doc,'ascii',errors='ignore')
        subprocess.call('cd /home/stevie/Python/diary',shell=True)
        subprocess.call("cat "+file+"| pr -w 67 -t"+"| lpr",shell=True)



    #lpr =  subprocess.Popen("/usr/bin/lpr", stdin=subprocess.PIPE)
    #lpr.stdin.write(docbytearray)
    #lpr.communicate()[0]




   
   def close(event=None):
       window.destroy()

   window.bind("<Alt-z>",close)

   def MightyFileSaver(event=None):
        tab2.filename=filedialog.asksaveasfilename(initialdir='/home/stevie/Python/diary',title="MightyFileSaver")
        doc=txt.get(1.0,END)
        print(tab2.filename)
        try:
           with open(tab2.filename,'w') as f:
           
               f.write(doc)
        except:
            pass





   def Saver(event=None):
       doc=txt.get(1.0,END)
       try:
           with open(tab2.filename,'w') as f:
			  
                f.write(doc)
       except:
           MightyFileSaver()

   def TabCloser(event=None):
       tabcon.forget(tabcon.select())
       Tab.num=Tab.num-1       
       
  # def TabChecker(even=None):
    #   num=tabcon.index("end")
   #if num>43:
     #  pass
  # else:
    #   TabMaker()

   txt.bind("<Control-s>",Saver)
   txt.bind("<F11>",PrintSize)
   txt.bind("<F12>",AlmostFullScreen)
   txt.bind("<F3>",Finder)
   txt.bind_all("<Alt-o>",Opener)
   txt.bind("<Alt-p>",Printer)
   txt.bind('<Alt-s>',MightyFileSaver)
   txt.bind('<Alt-t>',TermPrint)
   txt.bind_all("<Control-w>",TabCloser)

   cursorpostext.after(100,cursorpos)
  
   window.bind("<Return>",Commander)
   window.bind("<Alt-e>",Eclient)


   
	

   menubar=Menu(window,background="gray11",activebackground="gray29",activeforeground="cyan",foreground="blue")


   filemenu=Menu(menubar,background="gray11",activebackground="gray29",foreground="blue",activeforeground="cyan",tearoff=0)

   #filemenu=Menu(menubar,font=myfont,tearoff=0)

   # filemenu.add_command(label="New",command=New)
   filemenu.add_command(label="Open",command=Opener)
   filemenu.add_command(label="Save",command=Saver)
   filemenu.add_command(label="Save As",command=MightyFileSaver)
   filemenu.add_separator()
   filemenu.add_command(label="Print",command=Printer)
   filemenu.add_separator()
   filemenu.add_command(label="Exit",command=close)
   menubar.add_cascade(label="File",menu=filemenu)


   printmenu=Menu(menubar,background="gray11",activebackground="gray29",foreground="blue",activeforeground="cyan",tearoff=0)

   printmenu.add_command(label="Print",command=Printer)
   printmenu.add_command(label="Term Print",command=TermPrint)
   menubar.add_cascade(label="Print",menu=printmenu)

   window.config(menu=menubar)

   commander.place(x=335,y=633)
#y is up and down x is right and left
   commandLabel.place(x=290,y=633)
   parameters.place(x=335,y=663)
   paraLabel.place(x=290,y=663)


	
#myfont=Font(family="Ubuntu Mono Regular",size=12)
menubar=Menu(window,background="gray11",activebackground="gray29",activeforeground="cyan",foreground="blue")


filemenu=Menu(menubar,background="gray11",activebackground="gray29",foreground="blue",activeforeground="cyan",tearoff=0)

#filemenu=Menu(menubar,font=myfont,tearoff=0)


window.attributes('-fullscreen',True)


def TabChecker(even=None):
    num=tabcon.index("end")
    if num>43:
        pass
    else:
        TabMaker()






window.title('TifEdit 1000')

window.bind("<Control-t>",TabChecker)

window.config(background="gray11")


window.option_add("*background","black")
window.option_add("*foreground","blue")

window.config(menu=menubar)    






style.configure("TLabel",background="gray11",foreground="blue")
style.configure("TText",background="gray11",foreground="blue")
style.configure("Text",background="black",foreground="blue")
style.configure("Menu",background="gray11",foreground="blue")
style.configure("TMenu",background="gray11",foreground="blue")
style.configure("TEntry",background="gray11",foreground="blue")
style.configure("TMenubutton",background="gray11",foreground="blue")
style.configure("TButton",background="gray11",foreground="blue")
style.configure("TFrame",background="gray29",foreground="blue")
style.configure("Frame",background="gray11",foreground="blue")
style.configure("Button",background="gray11",foreground="blue")
style.configure("TScrollbar",background="gray11",foreground="blue")
style.configure("TListbox",background="gray11",foreground="blue")
style.configure("TMessagebox",background="gray11",foreground="blue")
style.configure("Messagebox",background="gray11",foreground="blue")
style.configure("Entry",background="gray11",foreground="blue")
style.configure("TDialogbox",background="gray11",foreground="blue")
style.configure("TWidget",background="gray11",foreground="blue")
style.configure("Widget",background="gray11",foreground="blue")
style.configure("Commondialog",background="gray11",foreground="blue")
style.configure("Dialogbox",background="gray11",foreground="blue")
style.configure("TSpinbox",background="gray11",foreground="blue")
style.configure("Spinbox",background="gray11",foreground="blue")
style.configure("Tspinbox",background="gray11",foreground="blue")
style.configure("Combobox",background="gray11",foreground="blue")
style.configure("Tcombobox",background="gray11",foreground="blue")
style.configure("TToplevel",background="gray11",foreground="blue")
frame=Frame(window)
frame.pack()



tabcon.pack(expand=True,fill="both")	
#tabcon.pack_propagate(0)



TabMaker()
window.mainloop()

 	
 












































