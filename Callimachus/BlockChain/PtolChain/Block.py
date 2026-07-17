#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from Config import *

import hashlib
import os
import json
import datetime as date

class Block(object):
	
	def __init__(self, dictionary):
		'''
		      We're looking for index, timestamp, data, prev_hash, nonce
		'''
		
		for key, value in dictionary.items():
			print("THESE", key, value)
			if key in BLOCK_VAR_CONVERSIONS:
				setattr(self, key, BLOCK_VAR_CONVERSIONS[key](value))
			else:
				setattr(self, key, value)
		
		if not hasattr(self, 'nonce'):
			# We're throwin this in for generation
			self.nonce = 'None'
			
		
		if not hasattr(self, 'hash'):  # in creating first block. remove in future
			self.hash = self.create_self_hash()
		
		print(self.__dict__())
		
	
	def header_string(self):
		return str(self.index) + self.prev_hash + self.data + str(self.timestamp) + str(self.nonce)
	
	def create_self_hash(self):
		sha = hashlib.sha256()
		sha.update(self.header_string().encode('utf-8'))
		return sha.hexdigest()
	
	def self_save(self):
		"""
		Want to be able to save easily
		"""
		index_string = str(self.index).zfill(6)  # front of zeros so they stay in numerical order
		filename = f"{CHAINDATA_DIR}/{index_string}.json"
		with open(filename, 'w') as block_file:
			json.dump(self.__dict__(), block_file)
	
	def is_valid(self):
		"""
		Current validity is only that the hash begins with at least NUM_ZEROS
		"""
		self.update_self_hash()
		if str(self.hash[0:NUM_ZEROS]) == "0" * NUM_ZEROS:
			return True
		else:
			return False
		
	def __eq__(self, other):
		return (self.index == other.index and
				self.timestamp == other.timestamp and
		        self.prev_hash == other.prev_hash and
		        self.hash == other.hash and
		        self.data == other.data and
		        self.nonce == other.nonce)
	
	def __ne__(self, other):
		return not self.__eq__(other)
		
	def __dict__(self):
		info = {}
		info['index'] = self.index
		info['timestamp'] = str(self.timestamp)
		info['prev_hash'] = self.prev_hash
		info['hash'] = self.hash
		info['data'] = self.data
		return info
		
	def __str__(self):
		return f"{self.__class__.__name__}({self.__dict__['index']}, {self.timestamp}, {self.prev_hash}, {self.hash}, {self.data})"
	
	def __repr__(self):
		return f"{self.__class__.__name__}(index={self.index}, timestamp={self.timestamp}, prev_hash={self.prev_hash}, hash={self.hash}, data={self.data})"
	

def create_first_block():
	# index zero and arbitrary previous hash
	block_data = {}
	block_data['index'] = 0
	block_data['timestamp'] = str(date.datetime.now())
	block_data['data'] = 'First Block Data'
	block_data['prev_hash'] = '0'
	genesis_block = Block(block_data)
	
	return genesis_block



if __name__ == "__main__":
	# check if chaindata folder exists
	# directory = input("Which blockchain would you like to use? ") Todo
	
	chaindata_dir = 'chaindata'
	
	if not os.path.exists(chaindata_dir):
		# make directory
		os.mkdir(chaindata_dir)
	
	# check if dir is empty from just creation or empty before
	if os.listdir(chaindata_dir) == []:
		# create and save first block
		first_block = create_first_block()
		first_block.self_save()