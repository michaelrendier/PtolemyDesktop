#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)
from ast import literal_eval
import datetime

class Dialogs(QObject):

	def __init__(self, parent=None):
		super(Dialogs, self).__init__(parent)
		QObject.__init__(self)

		self.parent = parent
		if self.parent:
			self.Ptolemy = parent.parentWidget()
		else:
			self.Ptolemy = None

		print("DIALOGS PARENT: ", self.parent, self.Ptolemy)
		
		if self.Ptolemy:
			self.database = self.Ptolemy.db
			
		else:
			from Callimachus.Database import Database
			self.database = Database(self)

	def infoBox(self, content):

		QMessageBox.information(self.Ptolemy, content[0], content[1])

	def overwriteBox(self):

		pass

	def addNoteBox(self, event=None):
		
		try:
			self.noteRe = self.Ptolemy.research.tabs.currentWidget().page().title() + " " + self.Ptolemy.research.urlEdit.text()
		except AttributeError:
			self.noteRe = 'New Note'
		
		dataList = [('Note Name', ''), ('Note', '\n\n\n\n\n'), ('Note Date', str(datetime.datetime.now().date())), ('Note Regarding', self.noteRe), ('Note Group', ''), ('Note Favorite', False)]
		title = "Add Note"
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.icon = QIcon(PTOL_ROOT + '/images/ptol.svg')
		results = fedit(dataList, title, icon=self.icon)

		if results == None:
			pass
		
		else:
			
			if results[5] == False:
				self.fav = 0
			
			else:
				self.fav = 1
			print(results, self.fav)
			
			sql = "INSERT INTO `PTOLdb`.`data_notes` (`id`, `noteName`, `noteText`, `noteDate`, `noteRegarding`, `noteGroup`, `noteFavorite`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
			args = [None, results[0], results[1], results[2], results[3], results[4], self.fav]

			self.database.dbExecute(sql, args)
			self.infoBox(['Database Updated', 'Added new Note {0}'.format(results[0])])
			pass

	def addSectionBox(self, event=None):

		sql = "SELECT * FROM `PTOLdb`.`data_sectionsCategories`"
		rows = self.database.dbReturnFA(sql)
		sectionList = [0]
		for i in rows:
			sectionList.append(i[1])

		dataList = [('New Section', ''), ('New Section Categories\n[str, str]', '')]
		title = "Add New Section with Categories"
		results = fedit(dataList, title)
		print(results)

		if results == None:
			pass

		else:
			if results[0] in sectionList:
				self.infoBox(['Section Exists', "Section already exists"])
				pass

			else:

				sql = "INSERT INTO `PTOLdb`.`data_sectionsCategories` (`id`, `sectionName`, `sectionCategories`) VALUES (%s, %s, %s)"
				args = [None, results[0], results[1]]

				self.database.dbExecute(sql, args)

				self.infoBox(['Database Updated', "Added new Section:\n{0}\nwith new Categories\n{1}".format(results[0], results[1])])

				pass

	def addCategoryBox(self, event=None):

		sql = "SELECT * FROM `PTOLdb`.`data_sectionsCategories`"
		rows = self.database.dbReturnFA(sql)
		sectionList = [0]
		for i in rows:
			sectionList.append(i[1])


		dataList = [('Which Section', sectionList), ('New Category', "")]
		title = "Add New Category"
		results = fedit(dataList, title)

		if not results:
			pass

		else:
			print(sectionList[results[0] + 1])
			
			sectionName = sectionList[results[0] + 1]
			
			sql = "SELECT * FROM `PTOLdb`.`data_sectionsCategories` WHERE `sectionName` = '{0}'".format(str(sectionName))
			row = self.database.dbReturnF1(sql)

			categoryList = literal_eval(row[2])



			if results[1] in categoryList:
				self.infoBox(['Category Exists', "Category already exists in {0}".format(sectionName)])

				pass

			else:
				categoryList.append(str(results[1]))
				print(str(categoryList))
				sql = """UPDATE `PTOLdb`.`data_sectionsCategories` SET `sectionCategories` = "{0}" WHERE `sectionName` = '{1}'  """.format(str(categoryList), str(sectionName))
				self.database.dbExecute(sql)

				self.infoBox(['Database Updated', "Added new category to\n'{0}'".format(sectionName)])

	def addPtolDependencyBox(self, event=None):
		
		
		
		datalist = [('Type', 'python3'), ('Name', ''), ('Info', ''), ('Install Instructions', '\n\n\n\n\n')]
		title = 'Add Ptolemy Dependency'
		comment = 'Types [python3, os, web (for web include install instaructions)]'
		results = fedit(datalist, title, comment)
		
		if results:
			
			dependencyCheck = []
			
			sql = "SELECT * FROM `PTOLdb`.`PTOLEMY_dependencies`"
			
			rows = self.database.dbReturnFA(sql)
			
			for i in rows:
				dependencyCheck.append(i[2])
				
			if results[1] not in dependencyCheck:
				
				sql = "INSERT INTO `PTOLdb`.`PTOLEMY_dependencies` (`id`, `type`, `name`, `info`, `install`) VALUES (%s, %s, %s, %s, %s)"
				if results[0] == 'web':
					args = [None, str(results[0]), str(results[1]), str(results[2]), str(results[3]).rstrip()]
				
				else:
					args = [None, str(results[0]), str(results[1]), str(results[2]), None]
	
				self.database.dbExecute(sql, args)
				
				self.infoBox(['Database Updated', 'Added new dependency to Ptolemy'])
				
			else:
				self.infoBox(['Dependency Exists', 'The dependency {0} already exists.'.format(results[1])])
			
		else:
			pass
		
		
		pass
		
	def addServerDependencyBox(self, event=None):
		
		datalist = [('Type', 'os'), ('Name', ''), ('Info', ''), ('Install Instructions', '\n\n\n\n\n')]
		title = 'Add Server Dependency'
		comment = 'Types [python3, os, web (for web include install instaructions)]'
		results = fedit(datalist, title, comment)
		
		if results:
			
			dependencyCheck = []
			
			sql = "SELECT * FROM `PTOLdb`.`SERVER_dependencies`"
			
			rows = self.database.dbReturnFA(sql)
			
			for i in rows:
				dependencyCheck.append(i[2])
				
			if results[1] not in dependencyCheck:
				
				sql = "INSERT INTO `PTOLdb`.`SERVER_dependencies` (`id`, `type`, `name`, `info`, `install`) VALUES (%s, %s, %s, %s, %s)"
				if results[0] == 'web':
					args = [None, str(results[0]), str(results[1]), str(results[2]), str(results[3]).rstrip()]
				
				else:
					args = [None, str(results[0]), str(results[1]), str(results[2]), None]
				
				self.database.dbExecute(sql, args)
				
				self.infoBox(['Database Updated', 'Added new dependency for Server'])
				
			else:
				self.infoBox(['Dependency Exists', 'The dependency {0} already exists.'.format(results[1])])
				
		
		else:
			pass
		
		pass
	
	def addTableBox(self, event=None):
		
		pass
	
	def addNoteGroup(self, event=None):
		
		pass
		
	def addRecipe(self, event=None):
		
		datalist = [('Recipe Name', ''), ('Recipe Count', ''), ('Ingredients List', '\n\n\n\n\n'), ('Instructions', '\n\n\n\n\n')]
		title = 'Add Recipe to Database'
		comment = 'Add ingredients like so:\nSugar 1 cup'
		results = fedit(datalist, title, comment)
		
		if results:
			
			recipeCheck = []
			
			sql = "SELECT * FROM `PTOLdb`.`data_recipes`"
			
			rows = self.database.dbReturnFA(sql)
			
			for i in rows:
				recipeCheck.append(i[1])
				
			if results[0] not in recipeCheck:
				
				sql = "INSERT INTO `PTOLdb`.`data_recipes` (`id`, `recipeName`, `recipeCount`, `recipeIngredients`, `recipeInstructions`) VALUES (%s, %s, %s, %s, %s)"
				args = [None, str(results[0]), str(results[1]), str(results[2]).rstrip(), str(results[3]).rstrip()]
				
				self.database.dbExecute(sql, args)
				
				self.infoBox(['Database Updated', 'Added {0} Recipe'.format(str(results[0]))])
				
			else:
				self.infoBox(['Recipe Exists', 'A recipe with the same name already exists'])
				
		else:
			pass
		
		pass
	
	def archiveArticle(self, event=None):
		
		
		
		pass
	
	def addCode(self, event=None):
		#id scriptsFileName scriptsDescription scriptsFileContents scriptsFileLocation
		
		datalist = [('Script Name', ''), ('Script Description', '\n'), ('Script', '\n\n\n\n\n'), ('File Location', '/home/rendier/')]
		title = 'Add Script to Database'
		comment = 'Unless otherwise needed,\nfiles should go in /home/rendier/'
		results = fedit(datalist, title, comment)
		
		if results:
			
			codeCheck = []
			
			sql = 'SELECT * FROM `PTOLdb`.`data_scripts`'
			
			rows = self.database.dbReturnFA(sql)
			
			for i in rows:
				codeCheck.append(i[1])
				
			if results[0] not in codeCheck:
			
				sql = 'INSERT INTO `PTOLdb`.`data_scripts` (`id`, `scriptsFileName`, `scriptsDescription`, `scriptsFileContents`, `scriptsFileLocation`) VALUES (%s, %s, %s, %s, %s)'
				args = [None, str(results[0]), str(results[1]).rstrip(), str(results[2]).rstrip(), results[3]]
				
				self.database.dbExecute(sql, args)
				
				self.infoBox(['Database Updated', 'Added {0} to database'.format(str(results[0]))])
				
			else:
				self.infoBox(['Script Exists', 'A script with the same name already exists'])
			
		else:
			
			pass
		
		pass