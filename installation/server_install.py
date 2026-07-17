#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import MySQLdb


installist = []
downloadlist = []

#connect to database
db = MySQLdb.connect(host="localhost", user="phpmyadmin", passwd="SriLanka65", db="PTOLdb")
cur = db.cursor()

# Fetch apt-get install list
cur.execute("SELECT `name` FROM `SERVER_dependencies` WHERE `type` != 'web'")
for i in cur.fetchall():
	i = str(i).replace(",", "").replace("(", "").replace(")", "").replace("\'", "")
	installist.append(i)

# Build apt-get command
repos = "sudo apt-get install " + ' '.join(installist)
print("\n\n" + str(repos))

#Fetch Install instructions for download packages
cur.execute("SELECT `install` FROM `SERVER_dependencies` WHERE `type` = 'web'")
for i in cur.fetchall():
	i = str(i).replace(",","").replace("(", "").replace(")", "").replace("\'", "")
	downloadlist.append(i)

#Build Download and Install command
webdl = """ && """.join(downloadlist)
print("\n\n" + webdl)

#~ #Install Repositories
#~ os.system(repos)

#Create Directories
#~ os.system("mkdir /home/rendier/Projects && mkdir /home/rendier/Programs")

#Download and Install web packages
# try:
# 	os.system(webdl)
#
# except error:
# 	pass

