#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import base64, os
from PyQt6.QtCore import QObject
from PIL import ExifTags, Image
from urllib.request import urlopen

print(os.getcwd())
class processImage(QObject):
	
	def __init__(self, parent=None):
		super(processImage, self).__init__(parent)
		QObject.__init__(self)
		
		
	def process(self, imagePath):
		
		# imageNT = self.imageNameType(imagePath)
		# self.imageTitle = imageNT[0]
		# self.imageType = imageNT[1]
		self.imageTitle, self.imageType = self.imageNameType(imagePath)
		
		if self.imageType == 'svg':
			
			self.imageString = self.svg2text(imagePath)
			
		else:
			
			self.imageString = self.image2text(imagePath)
			
		self.imageData = self.getImageData(imagePath)
		
		return [self.imageTitle, self.imageType, self.imageString, self.imageData]
	
	def imageNameType(self, imagePath):  # Add OS check for \ instead of / TODO
		
		self.imageTitle = imagePath.split('/')[-1].split('.')[0]
		self.imageType = imagePath.split('/')[-1].split('.')[-1]
		
		if 'math/render/svg' in imagePath and "." not in self.imageType:# Wikipedia math svg rendered formulas
			self.imageType = 'svg'
		
		if self.imageType == 'jpeg':
			self.imageType = 'jpg'
			
		return self.imageTitle, self.imageType
	
	def getImageData(self, imagePath):
		
		if imagePath.startswith('http://'):
			
			if self.imageType == 'svg':
				
				with urlopen(imagePath, 'rb') as image:
					svgString = image.read()
					svgData = svgString[: svgString.find(b'-->') + 3].replace(b'xml version', b'xml_version').replace(b'"', b'')
					self.exifDict = { i.split(b'=')[0]: i.split(b'=')[1] for i in svgData.split(b'\n')[0][2:-2].split() }
					svgTag = svgString[svgString.find(b'<svg'): svgString.find(b'>', svgString.find(b'<svg')) + 1]
					svgTagDict = { i.split(b'=')[0].replace(b' ', b''): i.split(b'=')[1].replace(b'"', b'') for i in svgTag.split(b'\n')[1:]}
					for i in svgTagDict:
						self.exifDict[i] = svgTagDict[i]
					self.exifDict['Data Type'] = 'SVG INFO'
		
			else:
				
				with Image.open(urlopen(imagePath), 'r') as image:
					if imagePath.lower().endswith('.jpg') or imagePath.lower().endswith('.jpeg'):
						self.exifDict = { ExifTags.TAGS[k]: v for k, v in image._getexif().items() if k in ExifTags.TAGS }
						self.exifDict['Data Type'] = 'JPG EXIF'
					else:
						self.exifDict = { k: v for k, v in image.info.items() }
						self.exifDict['Data Type'] = '{0} INFO'.format(self.imageType.upper())
					
					self.exifDict['bbox'] = image.getbbox()
					self.exifDict['bands'] = image.getbands()
					self.exifDict['extrema'] = image.getextrema()
					self.exifDict['palette'] = image.getpalette()
				
					image.close()
				
				
		else:
			if self.imageType == 'svg':
				
				with open(imagePath, 'rb') as image:
					svgString = image.read()
					svgData = svgString[: svgString.find(b'-->') + 3].replace(b'xml version', b'xml_version').replace(b'"', b'')
					self.exifDict = { i.split(b'=')[0]: i.split(b'=')[1] for i in svgData.split(b'\n')[0][2:-2].split() }
					svgTag = svgString[svgString.find(b'<svg'): svgString.find(b'>', svgString.find(b'<svg')) + 1]
					svgTagDict = { i.split(b'=')[0].replace(b' ', b''): i.split(b'=')[1].replace(b'"', b'') for i in svgTag.split(b'\n')[1:]}
					for i in svgTagDict:
						self.exifDict[i] = svgTagDict[i]
					self.exifDict['Data Type'] = 'SVG INFO'
				
			else:
				
				with Image.open(imagePath, 'r') as image:
					if imagePath.lower().endswith('.jpg') or imagePath.lower().endswith('.jpeg'):
						self.exifDict = { ExifTags.TAGS[k]: v for k, v in image._getexif().items() if k in ExifTags.TAGS }
						self.exifDict['Data Type'] = 'JPG EXIF'
					else:
						self.exifDict = { k: v for k, v in image.info.items() }
						self.exifDict['Data Type'] = '{0} INFO'.format(self.imageType.upper())
					
					self.exifDict['bbox'] = image.getbbox()
					self.exifDict['bands'] = image.getbands()
					self.exifDict['extrema'] = image.getextrema()
					self.exifDict['palette'] = image.getpalette()
					image.close()
		
		return self.exifDict
	
	def image2text(self, imagePath):
		
		if imagePath.startswith('http'):
				
			with urlopen(imagePath) as image:
				self.imageString = base64.b64encode(image.read())
				image.close()
			
		else:
					
			with open(imagePath, "rb") as image:
				self.imageString = base64.b64encode(image.read())
				image.close()

		# return 'data:image/{0};base64, {1}'.format(self.imageType, self.imageString.decode())
		return self.imageString.decode()
	
	def svg2text(self, imagePath):
	
		if imagePath.startswith('http'):
			
			with urlopen(imagePath) as image:
				svgString = image.read()
				self.imageString = svgString[svgString.find(b'<svg'): svgString.find(b'</svg>') + 6]
				image.close()
			
		else:
			with open(imagePath, 'rb') as image:
				svgString = image.read()
				self.imageString = svgString[svgString.find(b'<svg'): svgString.find(b'</svg>') + 6]
				image.close()
				
		return self.imageString

	
			
	def imageHtml(self, imageTitle, imageType, imageString):
		
		skeleton = open('viewimageskeleton.html', 'r').read()
		skeleton = skeleton.replace('{TITLE}', imageTitle)
		skeleton = skeleton.replace('{TYPE}', imageType)
		skeleton = skeleton.replace('{STRING}', imageString.decode())
		
		newfile = open(self.imageTitle + '.html', 'w')
		newfile.write(str(skeleton))
		newfile.close()
		
		
		
# url = "http://www.thewanderinggod.com/files/neworleans.jpg"
# url2 = "http://www.thewanderinggod.com/files/battleaxe.png"
# url3 = "http://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Pythagoras-proof-anim.svg/220px-Pythagoras-proof-anim.svg.png"
# file1 = "/home/rendier/Desktop/neworleans.jpg"
# file2 = "/home/rendier/Desktop/battleaxe.png"
# file3 = PTOL_ROOT + '/Callimachus/ptol.svg'

# IP = processImage()
# print(IP.process('ptol.svg'))
# print(IP.image2text(url3))
# print(IP.getExif(url), "\n\n")
# print(IP.getExif(url2), "\n\n")
# print(IP.getExif(file1), "\n\n")
# print(IP.getExif(file2), "\n\n")
# print("*" * 23)
# print(IP.image2text(url))
# print("*" * 23)
# print(IP.image2text(url2))
# print("*" * 23)
# print(IP.image2text(file1))
# print("*" * 23)
# print(IP.image2text(file2))
# print(IP.image2text(file3))