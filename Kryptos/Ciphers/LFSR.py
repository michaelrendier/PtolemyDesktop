#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Linear Feedback Shift Register
shift bits to the right, xor the last bits of old and new and use as first bit of shifted number.
Can be used as unsecure random number generator.
"""

state = (1 << 127) | 1
while True:
    print(state & 1, end = "")
    newbit = (state ^ (state >> 1) ^ (state >> 2) ^ ( state >> 7))
    state = (state >> 1) | (newbit << 127)