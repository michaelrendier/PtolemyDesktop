#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from lxml import html
import requests
from requests.exceptions import ConnectionError
from datetime import date
import json
import os
import sys
import csv
from dataclasses import dataclass, field
from typing import List, Dict


from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *

from PyQt6.QtSvgWidgets import *
from PyQt6.QtWidgets import *

from PyQt6.QtMultimedia import *

# example = {
# 	'close_date': 'Jan. 8, 2019',
# 	'close_price': '$\xa0150.75',
# 	'company_name': 'Apple Inc. Common Stock (AAPL) Quote & Summary Data',
# 	'key_stock_data': {
# 		'1 Year Target': '198',
# 		'50 Day Avg. Daily Volume': '46,822,949',
# 		'52 Week High / Low': '$ 233.47 / $ 142',
# 		'Annualized Dividend': '$ 2.92',
# 		'Best Bid / Ask': 'N/A / N/A',
# 		'Beta': '1.02',
# 		'Current Yield': '1.97 %',
# 		'Dividend Payment Date': '11/15/2018',
# 		'Earnings Per Share (EPS)': '$ 11.87',
# 		'Ex Dividend Date': '11/8/2018',
# 		'Forward P/E (1y)': '12.20',
# 		'Market Cap': '715,368,748,500',
# 		'P/E Ratio': '12.7',
# 		'Previous Close': '$ 147.93',
# 		'Share Volume': '41,025,314',
# 		"Today's High / Low": '$ 151.82 / $ 148.52'
# 	},
# 	'open price': '$\xa0149.74',
# 	'open_date': 'Jan. 8, 2019',
# 	'ticker': 'AAPL',
# 	'url': 'http://www.nasdaq.com/symbol/AAPL'
# }


class PennyWatch(QMainWindow):#Mainwindow TODO

	def __init__(self, parent=None):
		super(PennyWatch, self).__init__(parent)
		QMainWindow.__init__(self)
  # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
		self.setWindowIcon(QIcon(PTOL_ROOT + "/images/ptol.svg"))
		self.setWindowTitle("Phaleron - PennyWatcher")
		
		self.parent = parent
		
		self.exchanges = [
			"AMEX",
			"NYSE",
			"Nasdaq"
		]
		self.headings = [
			'Name',
			'Symbol',
			'Open',
			'High',
			'Low',
			'Close',
			'Net Chg',
			'% Chg',
			'Volume',
			'52 Wk High',
			'52 Wk Low',
			'Div',
			'Yield',
			'P/E',
			'YTD % Chg'
		]
		self.TheBoards = {}
		
		print("CWD:", os.getcwd())
		
		self.update_stock_data()
		

	def initUI(self):
		
		self.widget = QWidget(self)
		
		self.table = QTableWidget(self.widget)
		# self.table.setRowCount()
		self.table.setColumnCount(15)
		
		
		pass
	
	def update_stock_data(self):
		
		self.NYSE = {}
		self.AMEX = {}
		self.Nasdaq = {}
		
		filedate = date.today().strftime("%y%m%d")

		if not os.path.isfile(f'{filedate}-TheBoards.json'):
			for board in self.exchanges:
				print(f"Updating {board} Data\n")
				
				url = f"http://www.wsj.com/public/resources/documents/{board}.csv"
				
				try:
					file = requests.get(url)# Insert Try Except here TODO
					
				except ConnectionError:
					print("There is no connection to the internet available.\nPlease try again after a connection is established")
					break
				
				page = file.text
				
				lines = page.split("\n")
		
				lines = lines[4:-1]
				
				rows = []
				
				for line in lines:
					start = line.find('"')
					stop = line.rfind('"') + 1
					changethis = line[start: stop]
					tothis = changethis.replace(",", "").replace('"', '')
					rows.append(line.replace(changethis, tothis).split(","))
				
				for row in rows:
					entry = dict(zip(self.headings, row))
					for item in entry:
						value = entry[item]
						try:
							entry[item] = float(value)
						except ValueError:
							pass
						
					code = f"self.{board}[row[1]] = entry"
					exec(code)
					
				code = f"self.TheBoards['{board}'] = self.{board}"
				exec(code)
			
			with open(f"{filedate}-TheBoards.json", 'w') as file:
				file.write(json.dumps(self.Theboards))
				file.close()
		
		else:
			print(f"The data for {filedate} has already been uppdated.")
			
			
			
			
		
		
		pass
	
	def load_data(self):
		
		pass
	
	

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setApplicationName('Ptolemy II')

	Watcher = PennyWatch()
	
 # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
	Watcher.setWindowIcon(QIcon(PTOL_ROOT + '/images/ptol.svg'))

	Watcher.show()

	sys.exit(app.exec())
	
# 	argparser = argparse.ArgumentParser()
# 	argparser.add_argument('ticker', help='Company stock symbol')
# 	args = argparser.parse_args()
# 	ticker = args.ticker
# 	print("Fetching data for %s" % (ticker))
# 	scraped_data = parse_finance_page(ticker)
# 	print("Writing scraped data to output file")
#
# 	with open('%s-summary.json' % (ticker), 'w') as fp:
# 		json.dump(scraped_data, fp, indent=4, ensure_ascii=False)

# print(parse_finance_page("AAPL"))
finance = PennyWatch()