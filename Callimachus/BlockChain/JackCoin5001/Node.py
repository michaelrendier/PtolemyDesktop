#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from Block import Block
from flask import Flask
import Sync

import os
import json
import sys

node = Flask(__name__)

node_blocks = Sync.Sync() # initial blocks that are synced

@node.route('/blockchain.json', methods=['GET'])
def BlockChain():
	'''
	  Shoots back the blockchain, which in our case, is a json list of hashes
	  with the block information which is:
	  index
	  timestamp
	  data
	  hash
	  prev_hash
	  '''
	node_blocks = Sync.Sync() # Regrab the nodes if they've changed
	# Convert our blocks into dictionaries
	# so we can send them as json objects later
	python_blocks = []
	for block in node_blocks:
		# '''
		#     block_index = str(block.index)
		#     block_timestamp = str(block.timestamp)
		#     block_data = str(block.data)
		#     block_hash = block.hash
		#     block = {
		#       "index": block.index,
		#       "timestamp": block.timestamp,
		#       "data": block.data,
		#       "hash": block.hash,
		#       "prev_hash": block.prev_hash
		#     }
		#     '''
		python_blocks.append(block.__dict__())
	json_blocks = json.dumps(python_blocks)
	return json_blocks

if __name__ == "__main__":
	if len(sys.argv) >= 2:
		port = sys.argv[1]
	else:
  # TODO:SETTINGS — hardcoded port → Tesla/settings tab
		port = 5000
		
	node.run(host='127.0.0.1', port=port)