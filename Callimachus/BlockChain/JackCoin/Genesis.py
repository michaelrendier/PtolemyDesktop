#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import os
from Config import *
import Utils
import Sync
import argparse

def mine_first_block():
	first_block = utils.create_new_block_from_prev(prev_block=None)