#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import itertools as it



def Shuffle(strinput):
	combos = list(it.permutations(strinput, len(strinput)))
	for i in combos: print(i)

def bills2100(list=[20, 20, 20, 10, 10, 5, 5, 1, 1, 1, 1], total=100):
	# How many ways to make $100 with the bills in your pocket
	# Input list of bills
	makes_100 = [combo for n in range(1, len(list) + 1) for combo in it.combinations(list, n) if sum(combo) == total]
	if makes_100:
		return set(makes_100)
	else:
		return "Less than $100 in bills"


def all2100(list=[50, 20, 10, 5, 1], total=100):
	# How may ways to make $100 out of bills
	makes_100 = [combo for n in range(1, len(list) + 1) for combo in it.combinations_with_replacement(list, n) if sum(combo) == total ]
	return set(makes_100)


def first_order(p, q, initial_val):
	"""Return sequence defined by s(n) = p * s(n-1) + q."""
	return it.accumulate(it.repeat(initial_val), lambda s, _: p*s + q)

def second_order(p, q, r, initial_values):
	"""Return sequence defined by s(n) = p * s(n-1) + q * s(n-2) + r."""
	intermediate = it.accumulate(
		it.repeat(initial_values),
		lambda s, _: (s[1], p*s[1] + q*s[0] + r)
	)
	return map(lambda x: x[0], intermediate)

fibinacci_numbers = second_order(p=1, q=1, r=0, initial_values=(0, 1))
list(next(fibinacci_numbers) for _ in range(8))

pell_numbers = second_order(p=2, q=1, r=0, initial_values=(0, 1))
list(next(pell_numbers) for _ in range(6))

lucas_numbers = second_order(p=1, q=1, r=0, initial_values=(2, 1))
list(next(lucas_numbers) for _ in range(6))