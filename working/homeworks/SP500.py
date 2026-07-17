#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import itertools as it
from collections import namedtuple
import csv
from datetime import datetime


class DataPoint(namedtuple('DataPoint', ['date', 'value'])):
	__slots__ = ()

	def __le__(self, other):
		return self.value <= other.value

	def __lt__(self, other):
		return self.value < other.value

	def __gt__(self, other):
		return self.value > other.value


def read_prices(csvfile, _strptime=datetime.strptime):
    with open(csvfile) as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            yield DataPoint(date=_strptime(row['Date'], '%Y-%m-%d').date(),
                            value=float(row['Adj Close']))

prices = tuple(read_prices('SP500.csv'))
# ~ for i in prices: print(i)

gains = tuple(DataPoint(day.date, 100*(day.value/prev_day.value - 1.))
                for day, prev_day in zip(prices[1:], prices))

# ~ for i in gains: print(i)

for i in zip(prices, gains): print(i)


