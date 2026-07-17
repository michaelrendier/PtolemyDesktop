#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import datetime as date

def next_block(last_block):
	this_index = last_block.index + 1
	this_timestamp = date.datetime.now()
	this_data = f"Hey, i'm block {this_index}"
	this_hash = last_block.hash
	return Block(this_index, this_timestamp, this_data, this_hash)
