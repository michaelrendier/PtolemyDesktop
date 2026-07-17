#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import math
from decimal import Decimal
import inspect
from PyQt6.QtCore import QObject

class Statistics(object):  ####Make Sample Stats Modular
	"""Stats"""
	
	def __init__(self, parent=None):
		super(Statistics, self).__init__()
		# QObject.__init__(self)
		# print "PARENT", parent
		self.parent = parent
		# print 'PARENT\n', parent
		# self.Ptolemy = self.parent.parent
		# self.output = self.Ptolemy.Philadelphos.setoutput
	
	def splitlist(self, data, items_per_chunk):
		"""split list into chunks of chosen length. does not fill uneven chunks."""
		for start_index in range(0, len(data), items_per_chunk):
			end_index = start_index + items_per_chunk
			yield data[start_index:end_index]
	
	def mean(self, input_list):
		"""return mean/average of input_list"""
		x = sum(input_list)
		y = float(x) / float((len(input_list)))
		return y
	
	def median(self, input_list):
		"""return median of input_list"""
		sort = sorted(input_list)
		if len(input_list) % 2 == 0:
			x = (float(sort[(int(len(input_list) / 2) - 1)]) + float(sort[(int(len(input_list) / 2))])) / 2
		else:
			x = sort[int((len(input_list)) / 2)]
		return x
	
	####fix for more than one mode todo
	def mode(self, input_list):
		"""return mode of input_list"""
		d = {}
		for i in input_list:
			try:
				d[i] += 1
			except KeyError:
				d[i] = 1
		x = max(d, key=d.get)
		if x == 1: return 'No Mode'
		if x != 1: return x
	
	def quartiles(self, input_list):
		
		self.quartile_2 = self.median(input_list)
		if len(input_list) % 2 == 0:
			self.quartile_1 = self.median(input_list[:int(len(input_list)/2) - 1])
			self.quartile_3 = self.median(input_list[int(len(input_list)/2) + 1:])
		else:
			self.quartile_1 = self.median(input_list[:int(len(input_list)/2)])
			self.quartile_3 = self.median(input_list[int(len(input_list)/2) + 1:])
		
		return self.quartile_1, self.quartile_2, self.quartile_3
		
	
	def range(self, input_list):
		"""return range of input_list"""
		sort = sorted(input_list)
		x = sort[-1] - sort[0]
		return x
	
	def midrange(self, input_list):
		"""return midrange of input_list"""
		sort = sorted(input_list)
		x = (sort[0] + sort[-1]) / 2
		return x
	
	def zscore(self, mean, stan_dev, x):
		"""m=mean, sd=standard deviation, x=score
		return z-score"""
		y = (float(x) - float(mean)) / float(stan_dev)
		return y
	
	def zscores(self, mean, stan_dev, x, y):
		"""m=mean, sd=standard deviation, x=score 1, y=score2
		return z-scores"""
		i = (float(x) - float(mean)) / float(stan_dev)
		j = (float(y) - float(mean)) / float(stan_dev)
		return i, j
	
	def dev(self, input_list):
		"""Sample Deviation"""
		sample = []
		for i in input_list:
			li = (float(i) - float(self.mean(input_list)))
			sample.append(li)
		return sample
	
	def devmean(self, input_list):
		"""Sample Deviation Mean"""
		deviation_mean = float(sum(self.dev(input_list))) / len(self.dev(input_list))
		return deviation_mean
	
	def devsqr(self, input_list):
		"""Sample Deviation Squares"""
		square_deviation = []
		for i in input_list:
			li = (float(i) - float(self.mean(input_list))) * (float(i) - float(self.mean(input_list)))
			square_deviation.append(li)
		return square_deviation
	
	def samplevar(self, input_list):
		"""Sample Variance"""
		s1 = sum(self.devsqr(input_list))
		s2 = float(s1) / len(self.devsqr(input_list))
		return s2
	
	def samplestandev(self, input_list):
		"""Sample Standard Deviation"""
		x = self.samplevar(input_list)
		return math.sqrt(x)
	
	def estsamplevar(self, input_list):
		"""Estimated Sample Variance"""
		s2u = float(sum(self.devsqr(input_list))) / (len(self.devsqr(input_list)) - 1)
		return s2u
	
	def estsamplestandev(self, input_list):
		"""Estimated Sample Standard Deviation"""
		x = self.estsamplevar(input_list)
		return math.sqrt(x)
	
	def sample(self, input_list):
		"""Print:
		Table: Sample, Deviation, Deviation Squares

		Sample mean,
		Sample Deviation Mean,
		Sample Deviation Squares Mean,

		Sample Variance,
		Sample Variance Deviation,

		Estimated Sample Variance,
		Estimated Sample Sample Variance Deviation"""
		print('%08s	%08s	%08s' % ('Sample  ', 'Deviation', 'SquareDev'), '\n' + '-' * 35)
		
		for i in range(len(input_list)):
			print('%06f	%06f	%06f' % (input_list[i], round((self.dev(input_list))[i], 5), round((self.devsqr(input_list))[i], 5)))
		print('\n')
		# print 'Sample Mean =', self.mean(input_list)
		self.output('Sample Mean =' + str(self.mean(input_list)) + "\n", 'blue')
		# print 'Deviation Mean =', self.devmean(input_list)
		self.output(('Deviation Mean =' + str(self.devmean(input_list)) + "\n"), 'green')
		print('Deviation Square Mean =', sum(self.devsqr(input_list)), '\n')
		print('Sample Variance =', self.samplevar(input_list))
		print('Sample Standard Deviation =', math.sqrt(self.samplevar(input_list)), '\n')
		print('Est. Sample Variance =', self.estsamplevar(input_list))
		print('Est. Sample Standard Deviation =', math.sqrt(self.estsamplevar(input_list)), '\n')
	
	def boxplot_data(self, input_list):  ####ADD DRAW BOXPLOT TODO
		"""return minimum, q1, median, q3, maxium
		for box and whisker plot"""
		sort = sorted(input_list)
		q1, q2, q3 = self.quartiles(sort)
		m2 = sort.pop(-1)
		m1 = sort.pop(0)
		return [m1, q1, q2, q3, m2]