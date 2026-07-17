#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import getpass

getpass.unix_getpass()

import math, decimal, inspect, generators


class cheatSheet(object):

	def __init__(self):
		super(cheatSheet, self).__init__(self)

	def miscCountVar(self, method):
		"""Count number of Variables in args"""
		vc = 0
		iv = 0
		blist = []

		#~ print alist
		#~ for i in alist:
			#~ print i
			#~ if type(i) == str:
				#~ vc += 1
		#~ print vc

		#blist = locals().values()
		#print blist
		alist = inspect.getargspec(method)
		print(alist.args)

		return vc

	def splitlist(self, slist, wp):
		length = len(slist)
		return [ slist[i*length // wp: (i+1)*length // wp] for i in range(wp) ]

	def matrixindex(self, Term, Matrix):
		"""Returning indecies of search term in 2D matrix
		Assign variables: x, y = matrixindex(Term, Matrix)"""
		for i in range(len(Matrix)):
			try:
				return [i, Matrix[i].index(Term)]
			except ValueError:
				pass

	def factor(self, n):
		"""n=number
		return sorted composite factors"""
		factors = set()
		n = abs(n)
		for x in range(1, int(math.sqrt(n)) + 1):
			if n % x == 0:
				factors.add(x)
				factors.add(n//x)
		return sorted(factors)

	def isprime(self, n):
		"""return if a number is prime"""
		plist = generators.primes(n * 10)
		if n in plist:
			return True
		else:
			return False

	def pfactor(self, num):
		"""num=number
		return sorted prime factors"""
		powers = []
		limit = (num/2)+1
		i = 2
		while i <= limit:
			while num % i == 0: # ie, i is a factor of num
				powers.append(i)
				num = num/i
			i += 1
			if num == 1: break  # ie, all factors have been found
		if len(powers) == 0: powers.append(num)  # num is prime
		return powers

	def factors(self, slist):
		"""return all composite factors for each element in slist"""
		matrix = [ [] for h in range(len(slist))]
		for i in slist:
			matrix[slist.index(i)].append(misc.factor(i))
		return matrix

	def pfactors(self, slist):
		"""return all prime factors for each element in slist"""
		matrix = [ [] for h in range(len(slist))]
		for i in slist:
			matrix[slist.index(i)].append(misc.pfactor(i))
		return matrix

	def lcm(self, x, y):
		"""x=first #, y= second #
		return Least Common Multiple"""
		xlist = []
		ylist = []
		for i in range(1, 101):
			xlist.append(x*i)
			ylist.append(y*i)
		for i in xlist:
			if i in ylist:
				return i
				break

	def gcd(self, x, y):
		"""x=first #, y=second #
		return Greatest Common Devisor"""
		dlist = []
		xlist = misc.factor(x)
		ylist = misc.factor(y)
		for i in xlist:
			if i in ylist:
				dlist.append(i)
		return dlist[-1]
	
	def :
# misc = misc()