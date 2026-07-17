#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from bs4 import BeautifulSoup

soup = None

loclist = []

with open('/home/rendier/Dropbox/Public/google/myplaces.kml', 'r') as newfile:
	soup = BeautifulSoup(newfile, 'lxml')
	
for i in soup.findAll('placemark'):
	name = i.find('name').text
	coord = i.find('coordinates').text.split(',')[:2]
	loclist.append([name, coord[0], coord[1]])

#  Add path plotter as well TODO

# print loclist

with open('locations.txt', 'w') as file:
	file.write(str(loclist))
