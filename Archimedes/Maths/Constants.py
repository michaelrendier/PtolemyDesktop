#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import math
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Constant:  # separate into classes for each TODO

		def add_constant(self, constant):
		"""Constants"""
		pi = math.pi  # Pi
		e = math.e  # Natural Log
		tau = 2 * math.pi  # 2Pi
		phi = 1.0 * (1 + math.sqrt(5)) / 2  # Golden Ratio
		
		# (Constant, Uncertainty, Units, Name)
		# Constant: [Value, Uncertainty, UVal, Units, Base SI Units, Name]
		
		c = [299792458,
		     None,
		     None,
		     [['m'], ['s'], []],
		     [['m'], ['s'], []],
		     'Speed of Light in a Vacuum']
		G = [Decimal(6.67384e-11),
		     Decimal(4.7e-5),
		     31,
		     [['m^3'], ['kg', 's'], []],
		     [['m^3'], ['kg', 's'], []],
		     'Newtonian Gravity Constant']

		
		k_B = (1.380688e-23, 13, 'J / K', 'Boltzmann Constant')  # 9.1e-7
		N_A = (6.02214129e-23, 27, '1 / mol', 'Avogadro Constant')  # 4.4e-8
		N_A = 6.02214129e+23
		G = 6.67384e-11  # Newtonian constant of gravitation in m^3/kg*s (80) 1.2e-4
		h = 6.62606957e-34  # Plank Constant in J*s (29) 4.4e-8
		m_e = 9.10938291e-31  # Electron Mass in kg (40) 4.4e-8
		m_p = 1.672621777e-27  # Proton mass in kg (74) 4.4e-8
		m_u = 1.660538921e-27  # Atomic mass unit in kg (73) 4.4e-8
		F = 96485.3365  # Faraday constant in C/mol (21) 2.2e-8
		g_n = 9.8065  # Standard acceleration of gravity in m/s^2
		l_P = 1.616199e-35  # Plank length in m (97) ______
		m_P = 2.17651e-8  # Plank mass in kg (13) ______
		t_P = 5.39106e-44  # Plank time in s (32) ______
		q_P = 1.875545956e-18  # Plank charge in C (41) ______
		T_P = 1.416833e-32  # Plank temperature in K
		
		pass