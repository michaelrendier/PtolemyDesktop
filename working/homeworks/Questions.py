#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

# 1 ********************
"""Could anyone please explain this code??"""

i = 1
for k in (range(1, 21)):
	print("k:", k)
	if i % k > 0:
		for j in range(1, 21):
			if (i*j) % k == 0:
				i *= j
				print("j:", j, "i:",  i)
				break

print(i)

"""How would we write this code...in a single line? In functional style?"""
for i in (i * j for k in range(1, 21) for j in range(1, 21) if i % k > 0 and (i * j) % k == 0): print(i)

# 2 ********************

"""Sum of all integers from 1-250 that are evenly divisible by 9"""
sum = sum([i for i in range(1, 251) if i % 9 == 0])

		
# 3 ********************

"""Spiral of Theodorus in Python?"""

