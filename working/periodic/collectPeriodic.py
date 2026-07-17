#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from bs4 import BeautifulSoup
import urllib2, MySQLdb, prettytable
from lxml.html.clean import clean_html

periodicTable = {}
pList = ['Hydrogen', 'Helium', 'Lithium', 'Beryllium', 'Boron', 'Carbon', 'Nitrogen', 'Oxygen', 'Fluorine', 'Neon', 'Sodium', 'Magnesium', 'Aluminium', 'Silicon', 'Phosphorus', 'Sulfur', 'Chlorine', 'Argon', 'Potassium', 'Calcium', 'Scandium', 'Titanium', 'Vanadium', 'Chromium', 'Manganese', 'Iron', 'Cobalt', 'Nickel', 'Copper', 'Zinc', 'Gallium', 'Germanium', 'Arsenic', 'Selenium', 'Bromine', 'Krypton', 'Rubidium', 'Strontium', 'Yttrium', 'Zirconium', 'Niobium', 'Molybdenum', 'Technetium', 'Ruthenium', 'Rhodium', 'Palladium', 'Silver', 'Cadmium', 'Indium', 'Tin', 'Antimony', 'Tellurium', 'Iodine', 'Xenon', 'Caesium', 'Barium', 'Lanthanum', 'Cerium', 'Praseodymium', 'Neodymium', 'Promethium', 'Samarium', 'Europium', 'Gadolinium', 'Terbium', 'Dysprosium', 'Holmium', 'Erbium', 'Thulium', 'Ytterbium', 'Lutetium', 'Hafnium', 'Tantalum', 'Tungsten', 'Rhenium', 'Osmium', 'Iridium', 'Platinum', 'Gold', 'Mercury_(element)', 'Thallium', 'Lead', 'Bismuth', 'Polonium', 'Astatine', 'Radon', 'Francium', 'Radium', 'Actinium', 'Thorium', 'Protactinium', 'Uranium', 'Neptunium', 'Plutonium', 'Americium', 'Curium', 'Berkelium', 'Californium', 'Einsteinium', 'Fermium', 'Mendelevium', 'Nobelium', 'Lawrencium', 'Rutherfordium', 'Dubnium', 'Seaborgium', 'Bohrium', 'Hassium', 'Meitnerium', 'Darmstadtium', 'Roentgenium', 'Copernicium', 'Ununtrium', 'Flerovium', 'Ununpentium', 'Livermorium', 'Ununseptium', 'Ununoctium']
# pList = ['Carbon']


#Connect Securly to Database
ssl = {'cert': '/etc/mysql-ssl/client-cert.pem', 'key': '/etc/mysql-ssl/client-key.pem'}
db = MySQLdb.connect(host='localhost', user='ssl-JARVIS', passwd='jarvisup', db='TESTdb', ssl=ssl, charset='utf8', use_unicode=True)# Test DB
#~ db = MySQLdb.connect(host='localhost', user='ssl-JARVIS', passwd='jarvisup', db='JARVISdb', ssl=ssl)# Test DB
cur = db.cursor()
cur.execute("""SHOW STATUS like 'Ssl_cipher'""")
print "Connected to database with " + str(cur.fetchone())

# Enforce UTF-8 for the connection.
cur.execute('SET NAMES utf8mb4')
cur.execute("SET CHARACTER SET utf8mb4")
cur.execute("SET character_set_connection=utf8mb4")


opener = urllib2.build_opener()
opener.addheaders = [("User-agent", "Mozilla/5.0")]
# termSet = {'1', '2'}
for term in pList:
	print "Mining {0} {1}".format(term, pList.index(term))
	url = "http://en.wikipedia.org/w/index.php?title={0}&printable=yes".format(term)

	try:
		infile = opener.open(url)
		page = infile.read()
		soup = BeautifulSoup(page)

		info = soup.findAll('table', attrs={'class': 'infobox'})

		soup = BeautifulSoup(str(info))

		# print "\nExtract Tables"
		vape = "No Vapor Pressure Table"
		isos = "No Stable Isotopes Table"
		for i in soup.findAll('table', attrs={'class': 'wikitable'}):
			if r"(K)" in str(i):
				vape = i.extract()
				# print vape

			elif 'half-life' in str(i):
				isos = i.extract()
				# print isos
			else:
				i.extract()

		# for i in soup.findAll('span'):


		rows = []
		edict = {}
		# print "\nExtracting"
		cs = 1
		for row in soup.findAll('tr'):
			try:
				if row.th.text:
					if row.td.text:
						# print 'row.td.table =', row.td.table
						# rows.append(str(row.th.text).replace("\n", ""))
						header = (row.th.text.replace(u'\u000A', u' '))
						data = (row.td.text.replace(u'\u000A', u' '))

						if header == u"Element category":
									data = data[2:]
						if header == " per shell ":
							header = 'Per shell'
						if header == "Crystal structure":
							if cs == 1:
								header = "Crystal structure I"
								cs = 2
								pass
							elif cs == 2:
								header = "Crystal structure II"
								cs = 1
						# print "these =", header, data
						rows.append(header)
						# print "Appended", row.th.text
						# termSet.add(row.th.text)
						# print "termSet =", termSet, "\n", len(termSet)
						edict[header] = data
			except AttributeError:
				pass



		# print "\nIsos", str(isos), "edict\n", str(edict)
		periodicTable[term] = [rows, edict, unicode(vape), unicode(isos)]
		# final = "{0}\n\n{1}\n\n{2}\n\n{3}".format(rows, edict, vape, isos)
		print len(rows), len(edict)

		# answer = open('periodic{0}.txt'.format(term), 'wb')
		# answer.write(final)
		# answer.close()
		# print "final =", final
	except urllib2.HTTPError:
		print "Page Not Found"

	except urllib2.URLError:
		print "No Connection Found"

# print str(periodicTable)

output = open('periodicDict.txt', 'wb')
output.write(str(periodicTable))
output.close()

sql = "UPDATE `TESTdb`.`JARVIS_searchDicts` SET `searchDict` = %s WHERE `searchName` LIKE 'periodicTable'"
args = [str(periodicTable)]
cur.execute(sql, args)
db.commit()
db.close


