#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from bs4 import BeautifulSoup


sub = u'\u2080 \u2081 \u2082 \u2083 \u2084 \u2085 \u2086 \u2087 \u2088 \u2089 \u208A \u208B'
superDict = {"0":u"\u2070", "1": u"\xb9", "2": u"\xb2", "3": u"\xb3", "4": u"\u2074", "5": u"\u2075", "6": u"\u2076", "7": u"\u2077", "8": u"\u2078", "9": u"\u2079", "+": u"\u207A", "-": u"\u207B", u'\u2212': u"\u207B", "=": u"\u207C", "(": u"\u207D", ")": u"\u207E", "n": u"\u207F" }

html = """<table class="wikitable">\n<tr>\n<th><a href="/wiki/Isotope" title="Isotope">iso</a></th>\n<th><a href="/wiki/Natural_abundance" title="Natural abundance">NA</a></th>\n<th><a href="/wiki/Half-life" title="Half-life">half-life</a></th>\n<th><a class="mw-redirect" href="/wiki/Decay_mode" title="Decay mode">DM</a></th>\n<th><a href="/wiki/Decay_energy" title="Decay energy">DE</a>\xc2\xa0<span><span>(<a href="/wiki/Electronvolt" title="Electronvolt">MeV</a>)</span></span></th>\n<th><a href="/wiki/Decay_product" title="Decay product">DP</a></th>\n</tr>\n<tr>\n<td><sup>78</sup>Kr</td>\n<td>0.35%</td>\n<td>&gt;1.1\xc3\x9710<sup>20</sup>\xc2\xa0y</td>\n<td>(<a href="/wiki/Double_beta_decay" title="Double beta decay">\xce\xb2<sup>+</sup>\xce\xb2<sup>+</sup></a>)</td>\n<td>2.846</td>\n<td><a class="mw-redirect" href="/wiki/Selenium-78" title="Selenium-78"><sup>78</sup>Se</a></td>\n</tr>\n<tr>\n<td rowspan="3"><sup>79</sup>Kr</td>\n<td rowspan="3"><a href="/wiki/Synthetic_radioisotope" title="Synthetic radioisotope">syn</a></td>\n<td rowspan="3">35.04\xc2\xa0h</td>\n<td><a href="/wiki/Electron_capture" title="Electron capture">\xce\xb5</a></td>\n<td>\xe2\x80\x93</td>\n<td><a class="mw-redirect" href="/wiki/Bromine-79" title="Bromine-79"><sup>79</sup>Br</a></td>\n</tr>\n<tr>\n<td><a href="/wiki/Positron_emission" title="Positron emission">\xce\xb2<sup>+</sup></a></td>\n<td>0.604</td>\n<td><sup>79</sup>Br</td>\n</tr>\n<tr>\n<td><a class="mw-redirect" href="/wiki/Gamma_radiation" title="Gamma radiation">\xce\xb3</a></td>\n<td>0.26, 0.39, 0.60</td>\n<td>\xe2\x80\x93</td>\n</tr>\n<tr>\n<td><sup>80</sup>Kr</td>\n<td>2.25%</td>\n<td colspan="4"><sup>80</sup>Kr is <a class="mw-redirect" href="/wiki/Stable_isotope" title="Stable isotope">stable</a> with 44 <a href="/wiki/Neutron" title="Neutron">neutrons</a></td>\n</tr>\n<tr>\n<td rowspan="2"><sup>81</sup>Kr</td>\n<td rowspan="2"><a href="/wiki/Trace_radioisotope" title="Trace radioisotope">trace</a></td>\n<td rowspan="2">2.29\xc3\x9710<sup>5</sup>\xc2\xa0y</td>\n<td>\xce\xb5</td>\n<td>\xe2\x80\x93</td>\n<td><a class="mw-redirect" href="/wiki/Bromine-81" title="Bromine-81"><sup>81</sup>Br</a></td>\n</tr>\n<tr>\n<td>\xce\xb3</td>\n<td>0.281</td>\n<td>\xe2\x80\x93</td>\n</tr>\n<tr>\n<td><sup>82</sup>Kr</td>\n<td>11.6%</td>\n<td colspan="4"><sup>82</sup>Kr is stable with 46 neutrons</td>\n</tr>\n<tr>\n<td><sup>83</sup>Kr</td>\n<td>11.5%</td>\n<td colspan="4"><sup>83</sup>Kr is stable with 47 neutrons</td>\n</tr>\n<tr>\n<td><sup>84</sup>Kr</td>\n<td>57.0%</td>\n<td colspan="4"><sup>84</sup>Kr is stable with 48 neutrons</td>\n</tr>\n<tr>\n<td><a href="/wiki/Krypton-85" title="Krypton-85"><sup>85</sup>Kr</a></td>\n<td>syn</td>\n<td>10.756\xc2\xa0y</td>\n<td><a class="mw-redirect" href="/wiki/Beta_emission" title="Beta emission">\xce\xb2<sup>\xe2\x88\x92</sup></a></td>\n<td>0.687</td>\n<td><a class="mw-redirect" href="/wiki/Rubidium-85" title="Rubidium-85"><sup>85</sup>Rb</a></td>\n</tr>\n<tr>\n<td><sup>86</sup>Kr</td>\n<td>17.3%</td>\n<td>\xe2\x80\x93</td>\n<td>(<a href="/wiki/Double_beta_decay" title="Double beta decay">\xce\xb2<sup>\xe2\x88\x92</sup>\xce\xb2<sup>\xe2\x88\x92</sup></a>)</td>\n<td>1.2556</td>\n<td><a class="mw-redirect" href="/wiki/Strontium-86" title="Strontium-86"><sup>86</sup>Sr</a></td>\n</tr>\n</table>"""
html2 = html

soup = BeautifulSoup(html)
# print str(soup)

cols = len(soup.findAll('th'))
rows = len(soup.findAll('tr'))
cells = len(soup.findAll('td'))

print "{0} x {1} with {2} cells".format(cols, rows, cells)

cellList = []

for i in soup.findAll('td'):
	cellList.append(i.text)

ths = []
for i in soup.findAll('th'):
	ths.append(i.text)

print ths
rowspan = 0
rowspanleft = 0
rowspanx = 0
trs = []
for i in soup.findAll('tr')[1:]:
	# print 'this string', str(i)
	if 'rowspan' in str(i):
		for j in i.findAll('td'):
			if 'rowspan' in str(j):
				rowspanx += 1
				rowspan = int(j.attrs['rowspan'])
				rowspanleft = int(j.attrs['rowspan'])

	if len(i.findAll('td')) < cols:
		print "\nLESS THAN"
		# rowspanleft -= 1
		# print 'rowspan', rowspan, 'rowspanleft', rowspanleft, 'rowspanx', rowspanx
		newtag = soup.new_tag('td')
		if rowspan:
			if 'colspan' in str(i):
				pass
			else:
				print '\nFixing'
				# print 'HELLO', i
				new = "<tr>" + rowspanx*"<td></td>" + str(i)[4:]
				html2 = html2.replace(str(i), str(new))
				rowspanleft -= 1
				if rowspanleft == 1:
					print "RESETTING"
					rowspanx = 0
					rowspanleft = 0
					rowspan = 0

soup = BeautifulSoup(html2)

# print html2

for i in soup.findAll('sup'):
	# print i
	letters = ""
	for letter in i.text:
		letters = letters + superDict[letter]
	# print letters
	i.string = letters
	# print i.text
# print 'changed to this', soup
# print soup

trs = []
for i in soup.findAll('tr'):
	trs.append(str(i))
# print trs



tds = []
for i in soup.findAll('td'):
	print 'i.attrs', i.attrs, 'keys', i.attrs.keys()
	tds.append([i.text, ({i.attrs.keys()[0]: int(i.attrs.values()[0])} if ('colspan' or 'rowspan') in i.attrs.keys() else None)])

# print tds
# print len(tds)


###################################################################################################

	def isosTable(self, soup):
		print "\nISOS TABLE"
		# soup = BeautifulSoup(html)
		html2 = str(soup)
		print str(soup)

		cols = len(soup.findAll('th'))
		rows = len(soup.findAll('tr'))
		cells = len(soup.findAll('td'))

		print "{0} x {1} with {2} cells".format(cols, rows, cells)

		# cellList = []

		# for i in soup.findAll('a'):
		# 	i.replace_with(i.text)
		# print "NO LINKS HTML", str(soup)

		for i in soup.findAll('sup'):
			# print i
			letters = ""
			for letter in i.text:
				letters = letters + self.superDict[letter]
			# print letters
			i.string = letters
			# print i.text
		# print 'changed to this', soup
		# print soup

		# for i in soup.findAll('td'):
		# 	cellList.append(i.text)

		rowspan = 0
		rowspanleft = 0
		rowspanx = 0
		for i in soup.findAll('tr')[1:]:
			# print 'this string', str(i)
			if 'rowspan' in str(i):
				for j in i.findAll('td'):
					if 'rowspan' in str(j):
						rowspanx += 1
						rowspan = int(j.attrs['rowspan'])
						rowspanleft = int(j.attrs['rowspan'])

			if len(i.findAll('td')) < cols:
				# print "\nLESS THAN"
				# rowspanleft -= 1
				# print 'rowspan', rowspan, 'rowspanleft', rowspanleft, 'rowspanx', rowspanx
				newtag = soup.new_tag('td')
				if rowspan:
					if 'colspan' in str(i):
						pass
					else:
						# print '\nFixing'
						# print 'HELLO', i
						new = "<tr>" + rowspanx*"<td></td>" + str(i)[4:]
						html2 = html2.replace(str(i), str(new))
						rowspanleft -= 1
						if rowspanleft == 1:
							# print "RESETTING"
							rowspanx = 0
							rowspanleft = 0
							rowspan = 0

		soup = BeautifulSoup(html2)

		print "HTML2", html2

		# for i in soup.findAll('a'):
		# 	i.replace_with(i.contents)
		# print "NO LINKS HTML", str(soup)

		for i in soup.findAll('sup'):
			# print i
			letters = ""
			for letter in i.text:
				letters = letters + self.superDict[letter]
			# print letters
			i.string = letters
			# print i.text
		# print 'changed to this', soup
		# print soup

		trs = []
		for i in soup.findAll('tr'):
			trs.append(str(i))
		# print trs

		ths = []
		for i in soup.findAll('th'):
			ths.append(i.text)

		# print ths

		tds = []
		for i in soup.findAll('td'):
			# print 'i.text', i.text, 'i.attrs', i.attrs
			tds.append([i.text, ({i.attrs.keys()[0]: int(i.attrs.values()[0])} if ('colspan' or 'rowspan') in i.attrs.keys() else None)])

		# print tds
		# print len(tds)


		cols = len(ths)
		self.rows = len(trs)
		self.cellIsos = QtGui.QTableWidget(rows-1, cols)
		self.cellIsos.setStyleSheet("QTableWidget { background-color: white; color: black }")
		# self.cellIsos.setFont(QtGui.QFont('DejaVu Sans'))
		self.cellIsos.setHorizontalHeaderLabels(ths)
		self.cellIsos.verticalHeader().hide()

		y = 0
		x = 0
		colspan = 0
		rowspan = 0
		rowspanx = 0
		colspanx = 0

		for i in tds:

			if colspan:
				# print 'if colspan', colspan
				if x + colspanx > len(ths):
					x = 0
					y += 1
					colspan = 0

			newitem = QtGui.QTableWidgetItem(i[0])
			if not i[1]:
				# print 'No Attrs'
				self.cellIsos.setItem(y, x, newitem)
				x += 1
				# print x
				if x > len(ths)-1:
					x = 0
					y += 1

			else:
				# print 'Attrs'
				self.cellIsos.setItem(y, x, newitem)
				# print i[1].keys()
				if i[1].keys() == ['colspan']:
					# print 'colspan'
					self.cellIsos.setSpan(y, x, 1, i[1]['colspan'])
					colspan = 1
					colspanx = i[1]['colspan']
					# print 'colspan', colspan, 'colspanx', colspanx



				elif i[1].keys() == ['rowspan']:
					# print 'rowspan', i
					self.cellIsos.setSpan(y, x, i[1]['rowspan'], 1)
					rowspan = 1
					rowspanx = i[1]['rowspan']
				# print 'rowspan', rowspan, 'rowspanx', rowspanx
				x += 1
				if x > len(ths)-1:
					x = 0
					y += 1
		pass


