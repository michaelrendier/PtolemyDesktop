#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import sympy as sp



class Calculus():

	def __init__(self, parent=None):
		super(Calculus, self).__init__(parent)
		
		self.parent = parent
		self.sign_list = {"+": [], "-": []}
		

	def partial_derivative(self, function):
		
		pass
	
	def non_sympy_derivative(self, function): # without sympy
		terms = []
		print("Function:", function)
		function = function.split()
		
		for i in function:
			# print("This Term:", i)
			if "**" in i and "x" in i:
				# print("Inside **")
				term = function[function.index(i)].split("**")
				# print("** Term:", term)
				if "*" in term[0]:
					# print("Inside *")
					term[0] = term[0].split("*")
					# print("* ** Term 2:", term)
					term[0][0] = int(term[0][0]) * int(term[1])
					term[1] = int(term[1]) - 1
					# print("* ** Term 3:", term)
					newterm = f"{int(term[0][0])}*{term[0][1]}**{int(term[1])}"
				# print("New ** Term:", newterm)
				
				else:
					# print("Inside no *")
					newterm = f"{term[1]}{term[0]}**{int(term[1]) - 1}"
				# print("ELSE NEWTERM:", newterm)
				if "**1" in newterm:
					newterm = newterm.replace("**1", "")
				
				terms.append(newterm)
			# print("New Term Final:", newterm)
			elif "*" in i and "**" not in i:
				# print("Inside * not **")
				# print("MultiTerm", i)
				new_multiterm = i.split("*")[0]
				# print("new Multiterm:", new_multiterm)
				terms.append(new_multiterm)
			elif "+" in i or "-" in i:
				# print("Inside +-")
				terms.append(i)
				derivative = " ".join(terms[:-3])
		print("Derivative:", derivative)
		
	def derivative(self, function, derivative_number):
		
		pass