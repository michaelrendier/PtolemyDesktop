#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

CHAINDATA_DIR = 'chaindata/'
BROADCASTED_BLOCK_DIR = CHAINDATA_DIR + 'bblocks/'

#possible peers to start with
PEERS = [
          'http://localhost:5000/',
          'http://localhost:5001/',
          'http://localhost:5002/',
          'http://localhost:5003/',
        ]

NUM_ZEROS = 5 # difficulty, currently.

BLOCK_VAR_CONVERSIONS = {'index': int, 'nonce': int, 'hash': str, 'prev_hash': str, 'timestamp': str}
