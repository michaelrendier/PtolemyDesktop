#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'
import math
from decimal import Decimal
import inspect

class Classical(object):
	
	def __init__(self, parent=None):
		super(Classical, self).__init__()
		object.__init__(self)
		
		# (Constant, Uncertainty, UVal, Units, Base SI Units, Name)
		self.constants = {
			"R": [Decimal(8.3144621), Decimal(9.1e-7), 75, [['J'], ['mol', 'K', 's'], []], [['J'], ['mol', 'K', 's'], []], 'Gas Constant'],
			"k_B": [Decimal(1.380688e-23), Decimal(9.1e-7), 13, [['J'], ['K'], []], [['kg', 'm^2'], ['K'], []], 'Boltzmann Constant'],
			"N_A": [6.02214129e-23, 4.4e-8, 27, '1 / mol', '', 'Avogadro Constant']
		}
	
	# Gases
	def boyleslaw(self, p=None, V=None, k=None):
		"""pV = k
		p=pressure Pa, V=volume m^3, k=constant
		Given two values, return third"""
		# ~ vc = 0
		# ~ for i in locals().values():
		# ~ if i is None:
		# ~ vc += 1
		# ~ if vc > 1:
		# ~ raise ValueError('Too Many Variables')
		# countvar(boyleslaw)
		
		print('These =' + str(locals()))
		print('Are These =' + str(locals().values()))
		
		if p is None:
			return 1.0 * k / V
		elif V is None:
			return 1.0 * k / p
		elif k is None:
			return 1.0 * p * V
	
	def charleslaw(self, V=None, T=None, k=None):
		"""V/T = k
		V=volume m^3, T=temperature K, k=constant
		Given two values, return third"""
		assert (V is None) + (T is None) + (k is None) == 1, 'exactly 2 of V, T, k must be given'
		
		if V is None:
			return 1.0 * k * T
		elif T is None:
			return 1.0 * V * k
		elif k is None:
			return 1.0 * V / T
	
	def gaylussacslaw(self, p=None, T=None, k=None):
		"""p/T = k
		p=pressure Pa, T=temperature K, k=constant
		Given two values, return third"""
		assert (p is None) + (T is None) + (k is None) == 1, 'exactly 2 of p, T, k must be given'
		
		if p is None:
			return 1.0 * k * T
		elif T is None:
			return 1.0 * p / k
		elif k is None:
			return 1.0 * p / T
	
	def combinedgaslaw(self, p=None, V=None, T=None, k=None):
		"""(pV)/T = k
		p=pressure Pa, V=volume m^3,
		T=temperature K, k=constant
		Given three values, return fourth"""
		assert (p is None) + (V is None) + (T is None) + (
			k is None) == 1, 'exactly three of p, V, T, k must be given'
		
		if p is None:
			return 1.0 * (k * T) / V
		elif V is None:
			return 1.0 * (k * T) / p
		elif T is None:
			return 1.0 * (p * V) / k
		elif k is None:
			return 1.0 * (p * V) / T
	
	def idealgaslaw(self, p=None, V=None, n=None, R=None, T=None):
		"""pV = nRT
		p=pressure Pa, V=volume m^3,
		n=# of particles mol, R=Gas Constant,
		T=temperature K
		Given four values, return fifth"""
		R = self.constants['R'][0]
		assert (p is None) + (V is None) + (n is None) + (R is None) + (
			T is None) == 1, 'exactly four of p, V, n, R, T must be given'
		
		if p is None:
			return 1.0 * (n * R * T) / V
		elif V is None:
			return 1.0 * (n * R * T) / p
		elif n is None:
			return 1.0 * (p * V) / (R * T)
		elif R is None:
			return 1.0 * (p * V) / (n * T)
		elif T is None:
			return 1.0 * (p * V) / (n * R)