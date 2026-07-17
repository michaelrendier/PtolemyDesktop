# !/usr/bin/env python3
# import sys; # you don't need ; in python
import sys
import os
print(os.getcwd())
print(sys.version)
import xml.etree.ElementTree as ET
import csv


tree = ET.parse("def.xml")
root = tree.getroot()

# open a file for writing
DEF_data = open('def.csv', 'w')

# create the csv writer object
csvwriter = csv.writer(DEF_data)
def_head = []

count = 0
for index in root.findall('BSR'):
	bsr = []
if count == 0:
	verb = index.find('BSR').tag
	def_head.append(verb)
	noun = index.find('NOUN').tag
	def_head.append(noun)
	revision = index.find('REVISION').tag
	def_head.append(revision)
	csv.writer.writerow(def_head).tag
	count = count + 1
	
	verb = index.find('BSR').text
	bsr.append(verb)
	noun = index.find('NOUN').text
	bsr.append(noun)
	revision = index.find('REVISION').text
	bsr.append(revision)
	csvwriter.writerow(bsr)

DEF_data.close()