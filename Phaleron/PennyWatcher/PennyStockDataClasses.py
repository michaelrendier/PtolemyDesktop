#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from lxml import html
import requests
from time import sleep, asctime
from random import randint
from dataclasses import dataclass, field
from typing import List, Dict
from urllib.request import build_opener
from contextlib import closing
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


import time
import json
import argparse
import MySQLdb
import sqlite3
import os
import certifi
import sys
import csv

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWebKitWidgets import *
from PyQt6.QtSvg import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebKit import *
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

# stocks = {"AUY": "NYSE", "GERN": "NASDAQ", "INCY": "NASDAQ", "JNJ": "NYSE", "GNW": "NYSE", "GPL": "NYSEMKT"}

@dataclass
class ID:
    last_name: str
    first_name: str
    middle_name: str
    
    # Add Address, Phone etc.
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name}"


@dataclass
class Wallet:
    identity: List[ID]
    cash: float = 0.0
    
    # Add cards eventually
    
    def __post_init__(self):
        self.receipts = []
        self.separator = "-" * 16
    
    def __str__(self):
        return f"{self.identity}. ${self.cash:.2f}"
    
    def add_money(self, amount, symbol, volume):
        transaction = [symbol, self.cash, amount, self.cash + amount, volume]
        self.cash += amount
        self.add_receipt(transaction, "+")
    
    def spend_money(self, amount, symbol, volume):
        transaction = [symbol, self.cash, amount, self.cash - amount, volume]
        self.cash -= amount
        self.add_receipt(transaction, "-")
    
    def add_receipt(self, transaction, sign):
        timestr = asctime()
        symbol = transaction[0]
        previous = transaction[1]
        amount = transaction[2]
        balance = transaction[3]
        volume = transaction[4]
        
        self.receipt = Receipt(self.identity, timestr, symbol, previous, sign, amount, balance, volume)
        
        self.receipts.append(self.receipt)
        pass
    
    def z_print(self):#TODO
        pass


@dataclass
class Receipt:
    identity: List[ID]
    time_date: str
    symbol: str
    previous: float
    sign: str
    amount: float
    balance: float
    volume: int
    
    def __post_init__(self):
        self.separator = "-" * 16
        print("RECEIPT:\n", self)
    
    def __str__(self):
        return f"{self.time_date}\n{self.symbol}\n${self.previous:15.2f}\n{self.sign}{self.amount:15.2f}\n{self.separator}\n>{self.balance:15.2f}\nVolume:\n{self.volume:16}"


@dataclass
class Board:
    listing: dict


@dataclass
class Stock:
    board: str
    symbol: str
    volume: int
    NYSE: dict
    AMEX: dict
    Nasdaq: dict
    
    stock_data: dict = None
    name: str = ""
    closing_price: float = 0.0
    closing_date: str = ""
    volume_price: float = 0.0
    
    def __post_init__(self):
        if self.board.lower() == 'nasdaq':
            self.update_nasdaq_data()
    
    def __str__(self):
        return f"{self.board.upper()} Stock: {self.symbol}\n{self.name}\n{self.closing_date}\nClose: {self.closing_price}\nVolume: {self.volume}\nVolume Price: {self.volume_price}"
    
    
    
    def update_nasdaq_data(self):
        
        os.system(f"wget http://www.wsj.com/public/resources/documents/AMEX.csv")
        self.stock_data = self.parse_nasdaq_stock(self.symbol)
        print("Finished Parsing")
        self.name = self.stock_data['company_name']
        self.closing_price = float(self.stock_data['close_price'].replace("$", "").replace(" ", ""))
        self.closing_date = self.stock_data['close_date']
        print("CLOSINGPRICE:", self.closing_price)
        print("VOLUME:", self.volume)
        self.volume_price = self.volume * self.closing_price
    
    def parse_nasdaq_stock(self, ticker):
        """
        Grab financial data from NASDAQ page

        Args:
          ticker (str): Stock symbol

        Returns:
          dict: Scraped data
        """
        key_stock_dict = {}
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
            "Connection": "keep-alive",
            "Host": "www.nasdaq.com",
            "Referer": "http://www.nasdaq.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36"
        }
        
        headers2 = [
            ("User-agent", "Mozilla/5.0 (X11; Linux x86_64)"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"),
            ("Accept_encoding", "gzip, deflate, br"), ("Accept_language", "en-US,en;q=0.9"),
            ("Upgrade_insecure_requests", "1")
        ]
        
        # Retrying for failed request
        for retries in range(5):
            try:
                url = "http://www.nasdaq.com/symbol/%s" % (ticker)
                response = requests.get(url, headers=headers, verify=True)
                
                if response.status_code != 200:
                    raise ValueError("Invalid Response Received From Webserver")
                
                print("Parsing %s" % (url))
                # Adding random delay
                sleep(randint(1, 3))
                parser = html.fromstring(response.text)
                xpath_exchange = '//*[@id="qbar_exchangeLabel"]/text()'
                xpath_head = "//div[@id='qwidget_pageheader']//h1//text()"
                xpath_key_stock_table = '//div[@class="row overview-results relativeP"]//div[contains(@class, "table-table")]/div'
                xpath_open_price = '//b[contains(text(), "Open Price:")]/following-sibling::span/text()'
                xpath_open_date = '//b[contains(text(), "Open Date:")]/following-sibling::span/text()'
                xpath_close_price = '//b[contains(text(), "Close Price:")]/following-sibling::span/text()'
                xpath_close_date = '//b[contains(text(), "Close Date:")]/following-sibling::span/text()'
                xpath_key = './/div[@class="table-cell"]/b/text()'
                xpath_value = './/div[@class="table-cell"]/text()'
                
                exchange = parser.xpath(xpath_exchange)
                raw_name = parser.xpath(xpath_head)
                key_stock_table = parser.xpath(xpath_key_stock_table)
                raw_open_price = parser.xpath(xpath_open_price)
                raw_open_date = parser.xpath(xpath_open_date)
                raw_close_price = parser.xpath(xpath_close_price)
                raw_close_date = parser.xpath(xpath_close_date)
                
                company_name = raw_name[0].replace("Common Stock ", "").replace(" Quote & Summary Data", "").strip() if raw_name else ''
                open_price = raw_open_price[0].strip() if raw_open_price else None
                open_date = raw_open_date[0].strip() if raw_open_date else None
                close_price = raw_close_price[0].strip() if raw_close_price else None
                close_date = raw_close_date[0].strip() if raw_close_date else None
                
                # Grabbing ans cleaning keystock data
                for i in key_stock_table:
                    key = i.xpath(xpath_key)
                    value = i.xpath(xpath_value)
                    key = ''.join(key).strip()
                    value = ' '.join(''.join(value).split())
                    key_stock_dict[key] = value
                
                nasdaq_data = {
                    
                    "company_name": company_name,
                    "ticker": ticker,
                    "url": url,
                    "open price": open_price,
                    "open_date": open_date,
                    "close_price": close_price,
                    "close_date": close_date,
                    "key_stock_data": key_stock_dict
                }
                return nasdaq_data
            
            except Exception as e:
                print("Failed to process the request, Exception:%s" % (e))
                
    def update_nyse_data(self):
        
        
        
        self.process_csv(page)
        
        
        
        
        pass
    
    def parse_nyse_stock(self, ticker):
        
        for retries in range(5):
            try:
                url = f"http://www.nyse.com/quote/{ticker.upper()}"
                options = Options()
                options.add_argument('--headless')
                browser = webdriver.Firefox(options=options)
                browser.get(url)
                page = browser.page_source
                browser.quit()
                
                root = html.fromstring(page)

                xpath_name = '//div[@class="d-dquote-symbol"]/span/text()'
                xpath_last = '//span[contains(text(), "Last:")]/following-sibling::span/text()'
                xpath_change = '//span[contains(text(), "Change:")]/following-sibling::span/text()'
                xpath_pct_change = '//span[contains(text(), "% Change:")]/following-sibling::span/text()'
                xpath_volume = '//span[contains(text(), "Volume:")]/following-sibling::span/text()'
                xpath_tradesize = '//span[contains(text(), "Tradesize:")]/following-sibling::span/text()'
                xpath_bid_ask = '//span[contains(text(), "Bid-Ask:")]/following-sibling::span/text()'
                xpath_bsizexasize = '//span[contains(text(), "BSizeXASize:")]/following-sibling::span/text()'
                xpath_previous = '//span[contains(text(), "PrevPrice:")]/following-sibling::span/text()'
                xpath_open_price = '//span[contains(text(), "Open:")]/following-sibling::span/text()'
                xpath_high = '//span[contains(text(), "High:")]/following-sibling::span/text()'
                xpath_low = '//span[contains(text(), "Low:")]/following-sibling::span/text()'
                xpath_52wkhi = '//span[contains(text(), "52wkhi:")]/following-sibling::span/text()'
                xpath_52wkhiDate = '//span[contains(text(), "52wkhiDate:")]/following-sibling::span/text()'
                xpath_52wklo = '//span[contains(text(), "52wklo:")]/following-sibling::span/text()'
                xpath_52wkloDate = '//span[contains(text(), "52wkloDate:")]/following-sibling::span/text()'
                xpath_beta = '//span[contains(text(), "BETA:")]/following-sibling::span/text()'
                xpath_exchange = '//span[contains(text(), "Exchange:")]/following-sibling::span/text()'
                
                company_name = root.xpath(xpath_name)[0].strip()
                symbol = root.xpath(xpath_name)[1].strip().replace("(", "").replace(")", "")
                last_price = root.xpath(xpath_last)[0].strip()
                price_change = root.xpath(xpath_change)[0].strip()
                percent_change = root.xpath(xpath_pct_change)[0].strip()
                volume = root.xpath(xpath_volume)[0].strip()
                tradesize = root.xpath(xpath_tradesize)[0].strip()
                bid_ask = root.xpath(xpath_bid_ask)[0].strip()
                bsizexasize = root.xpath(xpath_bsizexasize)[0].strip()
                previous_price = root.xpath(xpath_previous)[0].strip()
                open_price = root.xpath(xpath_open_price)[0].strip()
                high_price = root.xpath(xpath_high)[0].strip()
                low_price = root.xpath(xpath_low)[0].strip()
                year_high = root.xpath(xpath_52wkhi)[0].strip()
                year_high_date = root.xpath(xpath_52wkhiDate)[0].strip()
                year_low = root.xpath(xpath_52wklo)[0].strip()
                year_low_date = root.xpath(xpath_52wkloDate)[0].strip()
                beta = root.xpath(xpath_beta)[0].strip()
                exchange = root.xpath(xpath_exchange)[0].strip()
                
                nyse_data = {
                    'company_name': company_name,
                    'symbol': symbol,
                    'last_price': last_price,
                    'price_change': price_change,
                    'percent_change': percent_change,
                    'volume': volume,
                    'tradesize': tradesize,
                    'bid_ask': bid_ask,
                    'bsizexasize': bsizexasize,
                    'previous_price': previous_price,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'year_high': year_high,
                    'year_high_date': year_high_date,
                    'year_low': year_low,
                    'year_low_date': year_low_date,
                    'beta': beta,
                    'exchange': exchange
                }
                
                return nyse_data
                
            except Exception as e:
                print("Failed to process the request, Exception:%s" % (e))
                

        pass


@dataclass
class Portfolio:
    identity: List[ID]
    wallet: List[Wallet]
    nasdaqstocks: list = None  # {stock: # of shares}
    nysestocks: list = None
    amexstocks: list = None
    
    def __post_init__(self):
        self.nasdaqstocks = []
        self.nysestocks = []
        self.amexstocks = []
        pass
    
    def __str__(self):
        return f"{self.identity}\n{self.wallet.cash}\nNASDAQ:\n{self.nasdaqstocks}"
    
    def add_nasdaq(self, symbol, volume):
        
        code = f"{symbol.upper()} = Stock('nasdaq', '{symbol}', {volume})"
        # print("Add Nasdaq Code 1:", code)
        # print(AAPL)
        exec(code)
        
        code = f"self.nasdaqstocks.append({symbol})"
        # print("Add Nasdaq Code 2:", code)
        exec(code)
        
        pass
    
    def add_nyse(self, symbol, volume):
        
        code = f"{symbol.upper()} = Stock('nyse', '{symbol}', {volume})"
        exec(code)
        
        code = f"self.nysestocks.append({symbol})"
        exec(code)
        
        pass


class PennyWatcher(QMainWindow):
    
    def __init__(self, parent=None):
        super(PennyWatcher, self).__init__(parent)
        QMainWindow.__init__(self)
        
        pass
    
    def initUI(self):
        
        
        
        pass
    

xpath_date = "//span[@class='p12']/text()"


'//*[@id="column0"]/table[5]/tbody/tr[1]/td[1]/b'
'//*[@id="column0"]/table[5]/tbody/tr[2]/td[1]/b'