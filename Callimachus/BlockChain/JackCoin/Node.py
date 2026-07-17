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

node_blocks = Sync.Sync(save=True) # want to sync and save the overall "best" blockchain from peers

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
	local_chain = Sync.sync_local() # update if they've changed
	# Convert our blocks into dictionaries
	# so we can send them as json objects later
	json_blocks = json.dumps(local_chain.block_list_dict())
	return json_blocks
	

if __name__ == "__main__":
	if len(sys.argv) >= 2:
		port = sys.argv[1]
	else:
  # TODO:SETTINGS — hardcoded port → Tesla/settings tab
		port = 5000
		
	node.run(host='127.0.0.1', port=port)