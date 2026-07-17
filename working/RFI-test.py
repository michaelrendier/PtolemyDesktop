from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType

import os
from os import path  # to access the directory path in windows
import sys  # this is for system

import pymysql

FROM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "Main_rfi-design2.ui"))
FROM_CLASS2, _ = loadUiType(path.join(path.dirname(__file__), "login_rfi.ui"))

class Login(QMainWindow, FROM_CLASS2):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        QMainWindow.__init__(self)
        
        self.parent = parent

        self.setupUi(self)
        self.btn_login.clicked.connect(self.handel_login)
        self.window2 = None

    def handel_login(self):
        self.db = pymysql.connect(host="localhost", user="root", passwd="", db="standard_co")
        self.cur = self.db.cursor()

        self.user_name = self.lineEdit.text()
        self.password = self.lineEdit_16.text()

        sql = '''SELECT user_name FROM users'''
        self.cur.execute(sql)
        users = self.cur.fetchall()
        users = [i for sub in users for i in sub]  # another way to convert to list from tuple
        print('User Names= ', users)

        sql2 = '''SELECT pass FROM users'''
        self.cur.execute(sql2)
        pass1 = self.cur.fetchall()
        pass1 = [i for sub in pass1 for i in sub]  # another way to convert to list from tuple
        print('Pass= ', pass1)
        if self.user_name in users:
            user_index = users.index(self.user_name)
            if self.password == pass1[user_index]:
                self.window2 = Main()
                # self.window2 = Main(Login.return_username())
                self.close()
                self.window2.show()
            else:
                self.label.setText('Please check User Name or Password...')
        else:
            self.label.setText('User name dose not exist...')
            print('Current user is: ' + self.user_name)
            # return self.user_name
            
            ## you can use self.parent here to directly change the variable
            ## self.user_name in Main() like this.  You must define self.user_name in Main() first to do this.
            self.parent.user_name = self.user_name
            
    def return_username(self):
        return self.user_name

class Main(QMainWindow, FROM_CLASS):

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        QMainWindow.__init__(self)
        # this is stored in the UI file to setup:
        self.setupUi(self)
        
        ## by adding a blank user_name here, will allow you to modify it
        ## from within Login by using self.parent.user_name = 'user_name'
        self.user_name = ""

        # To start applaying functions:
        self.initUI()
        self.handel_button()
        self.standard_combo_box()
        # self.handel_db_connection()
        
        ## Put Login Here and pass self to login window as parent
        login = Login(parent=self)
        login.show()
        
        ## Since you are calling Login() from here,
        ## you can access the return_username() function to assign it to
        ## the class variable self.user_name
        self.user_name = login.return_username()

def main():
    app = QApplication(sys.argv)
    
    ## Change your first window to Main() instead of Login()
    ## If the login fails, have a 'login failed' screen for mainwindow to show and quit
    ## window = Login()
    window = Main()
    window.show()  # to show the window
    app.exec()  # infinte (App loop) loop to maintain the window open


if __name__ == '__main__':
    main()
