#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import os, sys, urllib, inspect

try:
    from PyQt6.QtCore import QObject
    _QT = True
except ImportError:
    class QObject: pass  # fallback stub
    _QT = False

try:
    import MySQLdb
    _MYSQL = True
except ImportError:
    MySQLdb = None
    _MYSQL = False

try:
    from PIL import Image
    from PIL import ExifTags as Exif
    _PIL = True
except ImportError:
    Image = None; Exif = None
    _PIL = False

try:
    from formlayout import fedit
except ImportError:
    fedit = None



class Database(QObject):

	def __init__(self, parent=None):
		super(Database, self).__init__(parent)
		QObject.__init__(self)

		self.Ptolemy = parent
		print("DATABASE PARENT: ", self.Ptolemy, self.Ptolemy.__module__, str(self.Ptolemy.__class__.__bases__), self.Ptolemy.__class__.__name__)


	# TODO
	def __del__(self):

		pass

	def dbOpen(self):

		# Connect Securly to Database
		# self.ssl = {'cert': '/etc/mysql-ssl/client-cert.pem', 'key': '/etc/mysql-ssl/client-key.pem'}
		# self.db = MySQLdb.connect(host='localhost', user='ssl-JARVIS', passwd='jarvisup', db='TESTdb', ssl=self.ssl, use_unicode=True)# Test DB
		self.db = MySQLdb.connect(host='localhost',
								  user='phpmyadmin',
								  passwd='SriLanka65',
								  db='PTOLdb',
								  use_unicode=True)  # Test DB

		self.cur = self.db.cursor()
		# self.cur.execute("""SHOW STATUS like 'Ssl_cipher'""")
		# print "Connected to database with " + str(self.cur.fetchone())
		# print self.cur

		# Enforce UTF-8 for the connection.
		self.cur.execute('SET NAMES utf8mb4')
		self.cur.execute("SET CHARACTER SET utf8mb4")
		self.cur.execute("SET character_set_connection=utf8mb4")

	# print "Encoding set to utf8mb4"

	def dbClose(self):

		self.db.close()

	def dbExecute(self, sql, args=None):

		self.dbOpen()
		self.cur.execute(sql, args)
		self.db.commit()
		self.dbClose()

	def dbReturnFA(self, sql, args=None):

		self.dbOpen()
		self.cur.execute(sql, args)
		rows = self.cur.fetchall()
		self.dbClose()
		return rows

	def dbReturnF1(self, sql, args=None):

		self.dbOpen()
		self.cur.execute(sql, args)
		row = self.cur.fetchone()
		self.dbClose()
		return row

	def downImages(self, url, insec, incat):

		nextId = None
		imageHostname = None
		# print "imageHostname = " + str(imageHostname)
		sanitize = "abcdefghijklmnopqrstuvwxyz0123456789.-_()"

		# Process URL
		url = urllib.request.unquote(url)
		splitUrl = url.rsplit('/', (url.count('/') - 1))[1:url.count('/')]
		# print "splitUrl = " + str(splitUrl)
		imageDomain = splitUrl.pop(0)
		# print "imageDomain = " + str(imageDomain)
		imageName = str(splitUrl.pop(-1))
		# print "imageName = " + imageName
		imageType = imageName.rsplit('.', -1)[1].lower()
		if imageType == 'jpeg':
			imageType = 'jpg'
		# print "imageType = " + imageType
		imagePath = "/{0}/".format("/".join(splitUrl))
		# print "imagePath = " + imagePath
		imageLocalPath = "/home/rendier/JARVIS/media/images/downloads/{0}".format(imageDomain)
		# print "imageLocalPath = " + imageLocalPath
		imageLocalName = "{0}.{1}".format(
			"".join([i for i in str(imageName.rsplit('.', 1)[0]).lower() if i in sanitize]), imageType)
		# print "imageLocalName = " + imageLocalName
		imageFullPath = "{0}/{1}".format(imageLocalPath, imageLocalName)
		# print "imageFullPath = " + imageFullPath
		imageSection = str(insec)
		# print "imageSection = " + imageSection
		imageCategory = str(incat)
		# print "imageCategory = " + imageCategory

		# Create directory if not exist
		# print "imageLocalPath = " + imageLocalPath
		if os.path.isdir(imageLocalPath) == True:
			# print "TRUE"
			pass
		else:
			code = "mkdir {0}".format(imageLocalPath)
			# print "Directory Code = \n" + code
			os.system(code)

		# Fetch image if not exists
		if os.path.isfile(imageFullPath) == True:
			print("File Exists Already")
			self.Ptolemy.dialogs.infoBox(['File Already Exists', 'DO SOMETHING HERE'])
			pass

		else:
			code = "cd {0} && wget -q {1}".format(imageLocalPath, url)
			os.system(code)

			# if file extension is .jpeg, rename file to .jpg
			if str(url[len(url) - 4:len(url)]).lower() == 'jpeg':
				code = "cd {0} && mv {1} {2}".format(imageLocalPath, imageName, imageLocalName)
				os.system(code)

			# Make 100x100 Thumbnail of image
			# print imageFullPath
			code = "convert -sample 100x100 {0} {1}thumb.png".format(imageFullPath, imageFullPath[0:-4])
			# print "Convert Code = " + code
			os.system(code)

			imageThumbnail = "{0}thumb.png".format(imageFullPath[0:-4])
			# print "imageThumbnail = " + str(imageThumbnail)

			# Get image size, width, height
			img = Image.open(imageFullPath)
			imageWidth, imageHeight = img.size
			imageWidth = str(imageWidth) + "px"
			imageHeight = str(imageHeight) + "px"
			imageSize = os.stat(imageFullPath).st_size
			imageSize = str(imageSize) + " bytes"

			# Get EXIF Data
			# print "Getting EXIF Data"
			img = Image.open(imageFullPath, 'rb')
			# imageExifData = str(exifread.process_file(img))

			imageExifData = {
				Exif.TAGS[k]: v
				for k, v in img._getexif().items()
				if k in Exif.TAGS
			}
			# print "imageExifData = " + imageExifData

			# Insert into database only if not exists
			sql = """INSERT INTO `TESTdb`.`data_images` (`id`, `imageDomain`, `imageHostname`, `imagePath`, `imageName`, `imageType`, `imageExifData`, `imageSize`, `imageWidth`, `imageHeight`, `imageLocalPath`, `imageLocalName`, `imageThumbnail`, `imageSection`, `imageCategory`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
			# print sql
			args = [nextId, imageDomain, imageHostname, imagePath, imageName, imageType, imageExifData, imageSize,
					imageWidth, imageHeight, imageLocalPath, imageLocalName, imageThumbnail, imageSection,
					imageCategory]
			# print args
			self.dbExecute(sql, args)
			return "{0}/{1}".format(imageLocalPath, imageLocalName)

	def upImages(self, fname, insec, incat):

		nextId = None
		imageDomain = None
		sanitize = "abcdefghijklmnopqrstuvwxyz0123456789.-_()"
		# print "imageDomain = " + str(imageDomain)

		# Process fname
		# print fname
		# print urllib2.unquote(fname)
		fname = urllib.request.unquote(fname).replace("(", "").replace(")", "")
		fnameSplit = [fname.split("/")][0]
		fnameSplit[0] = str(fnameSplit[0]).replace("/", "")
		fnameSplit[-1] = fnameSplit[-1]
		# print "fnameSplit = " + str(fnameSplit)
		imageHostname = gethostname()
		# print "imageHostname = " + str(imageHostname)
		imageName = urllib.request.unquote(fnameSplit.pop(-1).replace("?", "").replace("=", ""))
		# print "imageName = " + imageName
		imageType = [imageName.rsplit('.', -1)[1].lower() if "." in imageName else "FIXTHIS"][0]
		if imageType == 'jpeg':
			imageType = 'jpg'
		# print "imageType = " + imageType
		imagePath = "/" + '/'.join(fnameSplit) + "/"
		# print "imagePath = " + imagePath
		imageLocalPath = "{0}media/images/uploads/{1}".format(self.homeDir, str(imageHostname))
		# print "imageLocalPath = " + imageLocalPath
		imageLocalName = "{0}.{1}".format(
			"".join([i for i in str(imageName.rsplit('.', 1)[0]).lower() if i in sanitize]), str(imageType))
		# print "imageLocalName = " + imageLocalName
		imageFullPath = urllib.request.unquote("{0}/{1}".format(imageLocalPath, imageLocalName))
		# print "imageFullPath = " + imageFullPath
		imageSection = str(insec)
		# print "imageSection = " + imageSection
		imageCategory = str(incat)
		# print "imageCategory = " + imageCategory

		# Create directory if not exist
		if os.path.isdir(imageLocalPath) == True:
			pass
		else:
			code = "mkdir {0}".format(imageLocalPath)
			# print "Code = " + code
			os.system(code)

		# Fetch image if not exists
		if os.path.isfile(imageFullPath) == True:
			print("File Exists Already")
			self.Ptolemy.dialogs.infoBox(['File Exists Already', 'DO SOMETHING HERE'])

			pass
		else:
			# print "\nfname =", fname
			# print "imageFullPath =", imageFullPath
			code = "cp {0} {1}".format(fname, imageFullPath)
			# print "code =", code
			# code = "cd {0} && cp {2} {3}".format(imageLocalPath, imagePath, imageName, imageFullPath)
			# code = "cd " + imageLocalPath + " && cp " + imagePath + "/" + imageName + " " + imageFullPath
			os.system(code)

			# Make 100x Thumbnail of image
			code = "convert -sample 100x100 {0} {1}thumb.png".format(imageFullPath, imageFullPath[:-4])
			# code = "convert -sample 100x100 " + imageFullPath + " " + imageFullPath[0:-4] + "thumb.png"
			# print "Convert Code = " + code
			os.system(code)

			imageThumbnail = "{0} {1}.png".format(imageFullPath, imageFullPath[0:-4])
			# print "imageThumbnail = " + imageThumbnail

			# If file extension is .jpeg, rename file to .jpg
			if str(imageName[len(imageName) - 4:len(imageName)]).lower() == 'jpeg':
				code = "cd {0} && mv {1} {2}".format(imageLocalPath, imageName, imageLocalName)
				# code = "cd " + imageLocalPath + " && mv " + imageName + " " + imageLocalName
				# print "Rename Code = " + code
				os.system(code)

			# Get image size, width, height
			# print "imageFullPath"
			img = Image.open(imageFullPath)
			imageWidth, imageHeight = img.size
			imageWidth = str(imageWidth) + "px"
			# print "imageWidth = " + imageWidth
			imageHeight = str(imageHeight) + "px"
			# print "imageHeight = " + imageHeight
			imageSize = os.stat(imageFullPath).st_size
			imageSize = str(imageSize) + " bytes"
			# print "imageSize = " + imageSize

			# Get EXIF Data
			# print "Getting EXIF Data"
			img = Image.open(imageFullPath, 'rb')
			# imageExifData = str(exifread.process_file(img))

			imageExifData = {
				Exif.TAGS[k]: v
				for k, v in img._getexif().items()
				if k in Exif.TAGS
			}

			# print "imageExifData = " + imageExifData

			# Insert into database only if not exists
			sql = """INSERT INTO `TESTdb`.`data_images` (`id`, `imageDomain`, `imageHostname`, `imagePath`, `imageName`, `imageType`, `imageExifData`, `imageSize`, `imageWidth`, `imageHeight`, `imageLocalPath`, `imageLocalName`, `imageThumbnail`, `imageSection`, `imageCategory`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
			# print "sql = " + sql
			args = [nextId, imageDomain, imageHostname, imagePath, imageName, imageType, imageExifData, imageSize,
					imageWidth, imageHeight, imageLocalPath, imageLocalName, imageThumbnail, imageSection,
					imageCategory]
			# print "args =" + str(args)
			self.dbExecute(sql, args)

			# print "iLP =", imageLocalPath
			# print "iLN =", imageLocalName
			return "{0}/{1}".format(imageLocalPath, imageLocalName)

	def addToSearchDict(self):

		sql = "SELECT `searchName` FROM `TESTdb`.`JARVIS_searchDicts`"
		rows = self.dbReturnFA(sql)
		dList = []
		for i in rows:
			dList.append(i[0])

		dataList = [('Dictionary Name', dList), ('New Entry', '\n')]
		title = "Choose Dictionary"
		comment = "Which Dictionary is to be modified?"
		result = fedit(dataList, title, comment)
		dictName = result[0]
		dictEntry = literal_eval(result[1])

		searchDict = {}
		# Access Database
		# print "Retrieving Dictionary"
		sql = "SELECT * FROM `TESTdb`.`JARVIS_searchDicts` WHERE `searchName` LIKE '{0}'".format(dictName)
		row = self.dbReturnF1(sql)
		searchDict = literal_eval(row[2])

		# Check if entry exists & update database
		# print "Check if exists?"
		if dictEntry.keys()[0] in searchDict.keys():  # FIND OUT HOW TO USE ONLY OK BUTTON
			result = fedit([('Overwrite', False)], "Entry Exists",
						   "Entry already exists in {0}\nDo you want to overwrite?".format(dictName))
			if result == None or False:
				print("Entry already exists...Halting.")
				self.Ptolemy.dialogs.infoBox(["Entry Exists", "This entry exists...Halting"])
				pass
			else:
				print("Overwriting Database")
				searchDict[dictEntry.keys()[0]] = dictEntry.values()[0]
				sql = "UPDATE `TESTdb`.`JARVIS_searchDicts` SET `searchDict` = %s WHERE `JARVIS_searchDicts`.`searchName` = %s"
				args = [str(searchDict), dictName]
				self.dbExecute(sql, args)
		else:
			print("Updating Database")
			searchDict[dictEntry.keys()[0]] = dictEntry.values()[0]
			sql = "UPDATE `TESTdb`.`JARVIS_searchDicts` SET `searchDict` = %s WHERE `JARVIS_searchDicts`.`searchName` = %s"
			args = [str(searchDict), dictName]
			self.dbExecute(sql, args)

	def addDependency(self, depType=None, depName=None, depInfo=None, depInstall=None):  # ADD STRAIGHT TODO

		if depType and depName and depInfo and depInstall:
			sql = """INSERT INTO `TESTdb`.`dependencies` (`type`, `name`, `info`, `install`) VALUES (%s, %s, %s, %s)"""
			args = [depType, depName, depInfo, (depInstall if depInstall else None)]
			self.dbExecute(sql, args)

		elif not depType and not depName and not depInfo and not depInstall:
			dataList = [('Type', ''), ('Name', ''), ('Info', '\n'), ('Install Code', '\n'), ('Remove', False)]
			title = "Add/Remove JARVIS Dependency"
			comment = "Fill out to add new dependency"
			result = fedit(dataList, title, comment)
			# print "this is the result:", result
			if result[4] == True:
				sql = "DELETE FROM `TESTdb`.`JARVIS_dependencies` WHERE `type` = '{0}' AND `name` = '{1}'".format(
					result[0], result[1])
				self.dbExecute(sql)
				pass
			else:
				sql = "INSERT INTO `TESTdb`.`JARVIS_dependencies` (`type`, `name`, `info`, `install`) VALUES (%s, %s, %s, %s)"
				args = [result[0], result[1], result[2], (result[3] if result[3] else None)]
				self.dbExecute(sql, args)

		else:
			self.Ptolemy.dialogs.infoBox(['Not Enough Args', 'Not enough Valid arguments'])

	def addNote(self, noteType=None, noteName=None, noteNote=None, notePriority=None):
		if noteType and noteName and noteNote and notePriority:
			sql = "INSERT INTO `TESTdb`.`JARVIS_notes` (`noteType`, `noteName` `noteNote`, `notePriority`) VALUES (%s, %s, %s, %s)"
			args = [noteType, noteName, noteNote, notePriority]
			self.dbExecute(sql, args)
			pass

		elif not noteType and not noteName and not noteNote and not notePriority:
			dataList = [('Type', ''), ('Name', ''), ('Note', "\n"), ('Priority 0(L)-10(h)', 0), ("Remove", False)]
			title = "Add JARVIS Note"
			comment = "Fill out to add note"
			result = fedit(dataList, title, comment)
			if result[4] == True:
				sql = "DELETE FROM `TESTdb`.`JARVIS_notes` WHERE `noteType` = '{0}' AND `noteName` = '{1}'".format(
					result[0], result[1])
				self.dbExecute(sql)
			else:
				sql = "INSERT INTO `TESTdb`.`JARVIS_notes` (`noteType`, `noteName`, `noteNote`, `notePriority`) VALUES (%s, %s, %s, %s)"
				args = [result[0], result[1], result[2], result[3]]
				self.dbExecute(sql, args)

		else:
			self.Ptolemy.dialogs.infoBox(["Not Enough Args", 'Not enough Valid arguments'])

	def addRemoveSection(self):

		dataList = [('Section', ''), ('Remove', False)]
		title = "Add Ptolemy Section"
		comment = "Add New Section"
		result = fedit(dataList, title, comment)
		if result[1] == True:
			sql = "DELETE FROM `PTOLdb`.`data_sectionsCategories` WHERE `sectionName` = '{0}'".format(result[0])
			self.dbExecute(sql)

		else:
			sql = "SELECT * from `PTOLdb`.`data_sectionsCategories` WHERE `sectionName` = '{0}'".format(result[0])
			row = self.dbReturnF1(sql)
			if row:
				self.Ptolemy.dialogs.infoBox(['Section Already Exists', 'Please choose another name'])

				pass

			else:
				sql = "INSERT INTO `PTOLdb`.`data_sectionsCategories` (`sectionName`) VALUES (%s)"
				args = [result[0]]
				self.dbExecute(sql, args)

		# sql = "SELECT * FROM `TESTdb`.`data_books` WHERE `bookName` = '{0}'".format(self.book)


