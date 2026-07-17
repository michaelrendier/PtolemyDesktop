#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import os, time

from PyQt6.QtCore import QTimer
from subprocess import Popen, PIPE
from datetime import datetime, timedelta, timezone


def cmdline(command):
	process = Popen(
		args=command,
		stdout=PIPE,
		stderr=PIPE,
		shell=True
	)
	return process.communicate()[0]


def sysDate():

	return "{0}.{1}.{2}".format(
		"%02d" % time.localtime()[2],
		"%02d" % time.localtime()[1],
		str(time.localtime()[0])[2:]
	)


def sysTime():

	return "{0}:{1}:{2}".format(
		"%02d" % time.localtime()[3],
		"%02d" % time.localtime()[4],
		"%02d" % time.localtime()[5]
	)


def sysYear():

	return "{0}.{1}.{2}".format(
		time.localtime()[6],
		time.localtime()[7],
		time.localtime()[8]
	)


def timeStamp():

	return [sysDate(), sysTime(), sysYear()]


def cronJob(interval, job):

	cron = QTimer()
	cron.setInterval(interval)
	try:
		cron.timeout.connect(job)

	except TypeError:
		pass
	cron.start()

def dbprint(text, client):
	if client.DEBUGPRINT == 1:

		if client.Ptolemy:
			father = client.Ptolemy
		elif client.Phaleron:
			father = client.Phaleron


		if text in father.DEBUGLIST[-1:-20:-1]:
			pass
		else:
			father.DEBUGLIST.append(text)
			print(text)

def getDateAfter(date_format="%d %B %Y", add_days=120, date=None):
	if not date:
		date_n_days_after = datetime.now() + timedelta(days=add_days)
	
	else:
		date_n_days_after = date + timedelta(days=add_days)
		
	return date_n_days_after.strftime(date_format)

def getDateBefore(date_format="%d %B %Y", days_before=120, date=None):
	if not date:
		date_n_days_ago = datetime.now() - timedelta(days=days_before)
		
	else:
		date_n_days_ago = date - timedelta(days=days_before)
		
	return date_n_days_ago.strftime(date_format)


def splitlist(data, items_per_chunk, auto_fill=False, fill_value=None):
	"""
	Split data into lists of a specific length, ie:
	splitting the list of Unicode characters into rows of 16
	
	splitlist([chr(i) for i in range(1114111)], 16)
	:param data: single list iterable
	:param items_per_chunk: how many
	:param auto_fill: if len(data) % items_per_chunk != 0
	:param fill_value: String to fill with
	:param fill_int: Boolean turn fill_value into integer
	:return:
	"""
	chunks = [data[x:x + items_per_chunk] for x in range(0, len(data), items_per_chunk)]
	if auto_fill:
		for i in range(items_per_chunk - len(chunks[-1])):
			chunks[-1].append(fill_value)

	return chunks

