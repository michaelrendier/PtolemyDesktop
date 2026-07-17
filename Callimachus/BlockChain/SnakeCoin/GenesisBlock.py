#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


import datetime as date

def create_genesis_block():
	#  Manually construct a block with
	#  index zero and arbitrary previous hash
	return Block(0, date.datetime.now, 'Genesis Block', '0')