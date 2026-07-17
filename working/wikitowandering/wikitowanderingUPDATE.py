from Tkinter import Tk
import urllib2
from BeautifulSoup import BeautifulSoup
import unicodedata

def wtw(searchterm):
	"""Retrieve wiki page and
	format for use on TWG.com"""
	
	###Gather page
	if ' ' in searchterm:
		searchterm = searchterm.replace(' ', '+')
	print searchterm
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		infile = opener.open('http://en.wikipedia.org/w/index.php?title=' + searchterm)
		page = infile.read()
		
		###Edit Page Styles
		page = page.replace('color: rgb(11, 0, 128);', 'color: rgb(0, 255, 255);')
		page = page.replace('color: rgb(170, 170, 170);', '')
		page = page.replace('rgb(170, 170, 170);', '')
		page = page.replace('background-color: rgb(255, 255, 255);', '')
		page = page.replace('color: rgb(0, 0, 0);', '')
		page = page.replace('color: black;', '')
		page = page.replace('color: rgb(249, 249, 249);', '')
		soup = BeautifulSoup(page)
		lesspage = soup.find('div', attrs={'id' : 'content', 'role' : 'main'})
		page = str(lesspage)
		soup = BeautifulSoup(page)
		
		###Latex Formula Tables w/white background
		imgs = soup.findAll('img', attrs={'class' : "tex"})
		for i in imgs:
			t = "<table border='0'><tr><td style='background-color: white;'>" + str(i) + "</td></tr></table>"
			page = page.replace(str(i), str(t))
			
		###Right Thumb Tables aligned right
		tright = soup.findAll('div', attrs={'class' : 'thumb tright'})
		for i in tright:
			t = "<table align='right' border='0'><tr><td>" + str(i) + "</td></tr></table>"
			page = page.replace(str(i), str(t))
 			
		###left Thumb Tables aligned left
		tleft = soup.findAll('div', attrs={'class' : 'thumb tleft'})
		for i in tleft:
			t = "<table align='left' border='0'><tr><td>" + str(i) + "</td></tr></table>"
			page = page.replace(str(i), str(t))
			
		###Thumb Images w/white background
		rimg = soup.findAll('img', attrs={'class' : 'thumbimage'})
		for i in rimg:
			t = "<table border='0'><tr><td style='background-color: white;'>" + str(i) + "</td></tr></table>"
			page = page.replace(str(i), str(t))
			
		###Align Infobox Vcard
		aivcd = soup.findAll('table', attrs={'class' : 'infobox vcard'})
		for i in aivcd:
			t = "<table align='right' border='0'><tr><td>" + str(i) + "</td></tr></table>"
			page = page.replace(str(i), str(t))
			
		###Align Infobox
		aifb = soup.findAll('table', attrs={'class' : 'infobox bordered'})
		for i in aifb:
			t = "<table align='right' border='0'><tr><td>" + str(i) + "</td></tr></table>"
			page = page.replace(str(i), str(t))
			
		###Remove Content Edit
		redit = soup.findAll('span', attrs={'class' : 'mw-editsection'})
		for i in redit:
			page = page.replace(str(i), '')
			
		###Remove firstHeading
		rhead = soup.findAll('h1', attrs={'id' : 'firstHeading'})
		for i in rhead:
			page = page.replace(str(i), '')
			
		###Remove siteSub
		rssub = soup.findAll('div', attrs={'id' : 'siteSub'})
		for i in rssub:
			page = page.replace(str(i), '')
			
		###Remove contentSub
		rcsub = soup.findAll('div', attrs={'id' : 'contentSub'})
		for i in rcsub:
			page = page.replace(str(i), '')
			
		###Remove Table of Contents
		rtoc = soup.findAll('table', attrs={'class' : 'toc'})
		for i in rtoc:
			page = page.replace(str(i), '')
			
		###Remove Navbox
		rnav = soup.findAll('table', attrs={'class' : 'navbox'})
		rvnib = soup.findAll('table', attrs={'class' : 'vertical-navbox nowraplinks infobox bordered'})
		rnpnav = soup.findAll('table', attrs={'class' : 'noprint navbox'})
		for i in rnav:
			page = page.replace(str(i), '')
		for i in rvnib:
			page = page.replace(str(i), '')
		for i in rnpnav:
			page = page.replace(str(i), '')
			
		###Remove vert navbox
		rvnav = soup.findAll('table', attrs={'class' : 'vertical-navbox nowraplinks hlist'})
		rvnav2 = soup.findAll('table', attrs={'class' : 'vertical-navbox nowraplinks'})
		for i in rvnav:
			page = page.replace(str(i), '')
		for i in rvnav2:
			page = page.replace(str(i), '')
			
		###Remove Jump To
		rjt = soup.findAll('div', attrs={'id' : 'jump-to-nav'})
		for i in rjt:
			page = page.replace(str(i), '')
			
		###Remove tright portal
		rtrp = soup.findAll('div', attrs={'class' : 'noprint tright portal'})
		for i in rtrp:
			page = page.replace(str(i), '')
			
		###Remove more footnotes
		rmf = soup.findAll('table', attrs={'class' : 'metadata plainlinks ambox ambox-style ambox-More_footnotes'})
		for i in rmf:
			page = page.replace(str(i), '')
			
		###Remove dablink
		rdabl = soup.findAll('div', attrs={'class' : 'dablink'})
		for i in rdabl:
			page = page.replace(str(i), '')
			
		###Remove mbox-small
		rmbsm = soup.findAll('table', attrs={'class' : 'metadata plainlinks mbox-small'})
		for i in rmbsm:
			page = page.replace(str(i), '')
		
		###Remove Move Box
		rmb = soup.findAll('table', attrs={'class' : 'metadata plainlinks ambox ambox-move'})
		for i in rmb:
			page = page.replace(str(i), '')
			
		###Remove Other Wiki Boxes
		rowb = soup.findAll('table', attrs={'class' : 'metadata mbox-small plainlinks'})
		for i in rowb:
			page = page.replace(str(i), '')
		
		page = page + "<p><img alt='' src='http://96.47.239.139/onerendier/images/sitegraphix/fleurdelis.png' style='width: 100px; height: 100px; float: right;' /></p>"
		
		###Copy page to clipboard
		r = Tk()
		r.withdraw()
		r.clipboard_clear()
		r.clipboard_append(page)
		r.destroy()
		
		print '\n\nCopied to clipboard'
		raw_input('Press enter to exit')
		
	except urllib2.HTTPError:
		print 'Page Not Found'
wtw("List of equations")
