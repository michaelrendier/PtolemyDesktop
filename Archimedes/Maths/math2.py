#!/usr/bin/python
# -*- coding: utf-8 -*-

"""docstring for math2"""
import math
import decimal
import inspect
import sympy
import generators




class Constant():#separate into classes for each TODO
	
	def __init__(self, parent=None):
		super(constant, self).__init__()
		object.__init__(self)
		
		"""Constants"""
		self.pi = math.pi #Pi
		self.e = math.e #Natural Log
		self.tau = 2 * math.pi #2Pi
		self.phi = 1.0 * (1 + math.sqrt(5)) / 2 #Golden Ratio
		
		# (Constant, Uncertainty, Units, Name)
		self.c = (199792458, None, 'm / s', 'Speed of Light in a Vacuum')
		self.R = (8.3144621, 75, 'J / mol*K', 'Gas Constant')#9.1e-7
		self.k_B = (1.380688e-23, 13, 'J / K', 'Boltzmann Constant')#9.1e-7
		self.N_A = (6.02214129e-23, 27, '1 / mol', 'Avogadro Constant')#4.4e-8
		self.G = (6.67408e-11, 31, 'm**3 / kg * s**2')#1.2e-4
		self.h = (6.62607015e-34, None, 'J * s', "Plank's Constant")
		self.h_bar (1.0545718176461565e-34, None, 'J * s / rad', 'Dirac constant')#Plank Constant in J*s (29) 4.4e-8
		
		self.m_e = 9.10938356e-31, 11, 'kg', 'Mass of Electron') #Electron Mass in kg (40) 4.4e-8
		self.m_p = 1.672621777e-27 #Proton mass in kg (74) 4.4e-8
		self.m_u = 1.660538921e-27 #Atomic mass unit in kg (73) 4.4e-8
		self.F = 96485.3365 #Faraday constant in C/mol (21) 2.2e-8
		self.g_n = 9.8065 #Standard acceleration of gravity in m/s^2
		self.l_P = 1.616199e-35 #Plank length in m (97) ______
		self.m_P = 2.17651e-8 #Plank mass in kg (13) ______
		self.t_P = 5.39106e-44 #Plank time in s (32) ______
		self.q_P = 1.875545956e-18 #Plank charge in C (41) ______
		self.T_P = 1.416833e-32 #Plank temperature in K


		
		pass

class misc(object):
	"""Misc"""
	
	def __init__(self):
		super(misc, self).__init__()
		
	def countvar(self, parent=None):
		"""Count number of Variables in args"""
		# vc = 0
		# iv = 0
		# blist = []
		#
		# #~ print alist
		# #~ for i in alist:
		# 	#~ print i
		# 	#~ if type(i) == str:
		# 		#~ vc += 1
		# #~ print vc
		#
		# #blist = locals().values()
		# #print blist
		# alist = inspect.getfullargspec(method)
		# print(alist.args)
		# for i in range(len(alist.args)):
		# 	print('i =', i)
		# 	item = 'iv = '+ str(method.__module__) + '.' + str(method.__name__) + '.' + alist.args[i]
		# 	print(item)
		# 	exec(item)
		# 	blist.append(iv)
		# 	if type(iv) is str:
		# 		vc += 1
		# print(vc, blist)
		# return vc


		pass
		
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

	def earthcurve(self, distance, units='km'):
		
		pass
	
	def bin2dec(self, binary):
		n = 0
		
		for d in str(binary):
			n = n * 2 + int(d)

		return n
	
class unitcircle():
	"""Unit Circle"""
	pass

class fractions():
	"""Fractions"""
		
	def redux(self, x, y):
		"""x=numerator, y=denominator
		return reduced fraction"""
		d = misc.gcd(x, y)
		x = x/d
		y = y/d
		return x, y
		
	def add(self, a, b, x, y):
		"""a=numerator 1, b=denominator 1
		x=numerator 2, y=denominator 2
		return (a/b)+(x/y)"""
		l = misc.lcm(b, y)
		ff = l/b
		sf = l/y
		a = a*ff
		b = b*ff
		x = x*sf
		y = y*sf
		i = a+x
		j, k = fractions.redux(i, l)
		print(str(j) + '/' + str(k))
		return j, k
		
	def subtract(self, a, b, x, y):
		"""a=numerator 1, b=denominator 1
		x=numerator 2, y=denominator 2
		return (a/b)+(x/y)"""
		l = misc.lcm(b, y)
		ff = l/b
		sf = l/y
		a = a*ff
		b = b*ff
		x = x*sf
		y = y*sf
		i = a-x
		j, k = fractions.redux(i, l)
		print(str(j) + '/' + str(k))
		return j, k
		
	def multiply(self, a, b, x, y):
		"""a=numerator 1, b=denominator 1
		x=numberator 2, y=denominator 2
		return (a*x)/(b*y)"""
		i = a*x
		j = b*y
		k, l = fractions.redux(i, j)
		print(str(k) + '/' + str(l))
		return k, l
		
	def divide(self, a, b, x, y):
		"""a=numerator 1, b=denominator 1
		x=numberator 2, y=denominator 2
		return (a*y)/(b*x)"""
		i = a*y
		j = b*x
		k, l = fractions.redux(i, j)
		return k, l
		
	# class mixed():
	#
	# 	# @staticmethod
	# 	def add(a, b, c, x, y, z):
	# 		"""a=whole 1, b=numerator 1, c=denominator 1
	# 		x=whole 2, y=numerator 2, z=denominator 2
	# 		return  a b/c + x y/z"""
	# 		l = misc.lcm(c, z)
	# 		ff = l/c
	# 		sf = l/z
	# 		b = b*ff
	# 		c = c*ff
	# 		y = y*sf
	# 		z = z*sf
	# 		if b < y:
	# 			a = a-1
	# 			b = b+c
	# 		if a < 1:
	# 			b = b*-1
	# 		if x < 1:
	# 			y = y*-1
	# 		e = a+x
	# 		f = b+y
	# 		g, h = fractions.redux(f, l)
	# 		if g > h:
	# 			e = e+1
	# 			g = g-h
	# 		return e, g, h
	#
	# 	# @staticmethod
	# 	def subtract(a, b, c, x, y, z):####TODO
	# 		pass
	#
	# 	# @staticmethod
	# 	def multiply(a, b, c, x, y, z):
	# 		"""a=whole 1, b=numerator 1, c=denominator 1
	# 		x=whole 2, y=numerator 2, z=denominator 2
	# 		return  (a b/c) * (x y/z)"""
	# 		fi = (a*c)+b
	# 		si = (x*z)+y
	# 		i = fi*si
	# 		j = c*z
	# 		e = i/j
	# 		f = i%j
	# 		g = j
	# 		f, g = fractions.redux(f, g)
	# 		return fractions.tomixed(f, g)
	#
	# 	# @staticmethod
	# 	def divide(a, b, c, x, y, z):####Finish
	# 		"""a=whole 1, b=numerator 1, c=denominator 1
	# 		x=whole 2, y=numerator 2, z=denominator 2
	# 		return  mixed fraction"""
	# 		n1 = (a*c)+b
	# 		n2 = (x*z)+y
	# 		n = n1*z
	# 		d = c*n2
	# 		i, j = fractions.redux(n, d)
	# 		return fractions.tomixed(i, j)
			
	def tomixed(self, x, y):
		"""x=numerator, y=denominator
		return mixed fraction"""
		if not x > y:
			return x, y
		a = x/y
		b = x%y
		c = y
		print(str(a) + ' ' + str(b) + '/' + str(c))
		return a, b, c
		
	def toimproper(self, x, y, z):####FIX POZ/NEG
		"""x=whole #, y=numerator, z=denominator
		return ((x*z)+y)/z"""
		i = (x*z)+y
		print(str(i) + '/' + str(z))
		return i, z
		
	def tofrac(self, n):
		"""n=number
		return number as improper fraction"""
		p = abs(decimal.Decimal(str(n)).as_tuple().exponent)
		d = 10**p
		i, j = math.modf(n)
		x = int((j*d) + (i*d))
		if x <= d:
			print(str(x) + '/' + str(d))
			return x, d
		else:
			return fractions.tomixed(x, d)

# class polynom():
# 	"""Polynom"""
#
# 	class p1():
# 		"""Power 1 Polynom"""
#
# 		# @staticmethod
# 		def p1solvex(a, b):
# 			"""ax + b = 0
# 			a=coefficient b=constant
# 			return x = -b/a"""
# 			x = (-b/float(a))
# 			i, j = fractions.redux(-b, a)
# 			if abs(i) > abs(j):
# 				if x < 0:
# 					print('x = -', fractions.tomixed(abs(i), abs(j)))
# 				else:
# 					print('x =', fractions.tomixed(abs(i), abs(j)))
# 			else:
# 				print('x = ' + str(i) + '/' + str(j))
# 			return x
#
# 		class dual():
# 			"""Dual Power 1 Polynom"""
# 			# @staticmethod
# 			def solvexequ(a, b, c, d):
# 				"""ax + b = cx + d
# 				a=coefficient 1, b=constant 1
# 				c=coefficient 2, d=constant 2
# 				return x = ?"""
# 				x = (d-b)/float(a-c)
# 				y = d-b
# 				z = a-c
# 				print(str(y) + '/' + str(z))
# 				i, j = fractions.redux(y, z)
# 				if abs(i) > abs(j):
# 					if x < 0:
# 						print('x = -', fractions.tomixed(abs(i), abs(j)))
# 					else:
# 						print('x =', fractions.tomixed(abs(i), abs(j)))
# 				else:
# 					print('x = ' + str(i) + '/' + str(j))
# 				return x
#
# 			def add(a, b, c, d):####TODO
# 				"""(ax + b) + (cx + d)"""
# 				pass
#
# 			# @staticmethod
# 			def subtract(a, b, c, d):####TODO
# 				"""(ax + b) - (cx + d)"""
# 				pass
#
# 			# @staticmethod
# 			def multiply(a, b, c, d):####TODO
# 				"""(ax + b) * (cx + d)"""
# 				pass
#
# 			# @staticmethod
# 			def divide(a, b, c, d):####TODO
# 				"""(ax + b) / (cx + d)"""
# 				pass
#
# 			# @staticmethod
# 			def angleadd(a, b, c, d, e, dr):
# 				"""(ax + b) + (cx + d) = e)
# 				a=coefficient 1, b=constant 1
# 				c=coefficient 2, d=constant 2
# 				e=angle total, dr=units in (d)egrees/(r)adians
# 				return angles in degrees and radians"""
# 				i = a+c
# 				j = (b+d)-e
# 				x = polynom.p1.sx(i, j)
# 				a1 = ((a*x)+b)
# 				a2 = ((c*c)+d)
# 				if dr != 'd' and dr != 'r':
# 					raise ValueError("Units must be 'd' or 'r'")
# 				if dr == 'd':
# 					print 'Angle One Deg:', a1
# 					print 'Angle Two Deg:', a2
# 					return a1, a2
# 				elif dr == 'r':
# 					print 'Angle One Rad:', math.radians(a1)
# 					print 'Angle Two Rad:', math.radians(a2)
# 					return math.radians(a1), math.radians(a2)
#
# 	class p2():####TODO
# 		"""Polynom Power 3"""
#
# 		# @staticmethod
# 		def solvex(a, b, c):####TODO
# 			pass
#
# 		class dual():
# 			"""Polynom Power 2 Dual"""
# 			# @staticmethod
# 			def solvexequ(a, b, c, d, e, f):####FINISH
# 				"""ax^2 + bx +c = dx^2 + ex + f
# 				a=coeff(x^2) 1, b=coeff(x) 1, c=constant 1
# 				d=coeff(x^2) 2, e=coeff(x) 2, f=constant 2
# 				return x = ?"""
# 				pass
#
# 			# @staticmethod
# 			def add(a, b, c, d, e, f):####TODO
# 				"""(ax^2 + bx +c) + (dx^2 + ex + f)"""
# 				pass
#
# 			# @staticmethod
# 			def subtract(a, b, c, d, e, f):####TODO
# 				"""(ax^2 + bx +c) - (dx^2 + ex + f)"""
# 				pass
#
# 			# @staticmethod
# 			def multiply(a, b, c, d, e, f):####TODO
# 				"""(ax^2 + bx +c) * (dx^2 + ex + f)"""
# 				pass
#
# 			# @staticmethod
# 			def divide(a, b, c, d):####TODO
# 				"""(ax^2 + bx +c) / (dx^2 + ex + f)"""
# 				pass
#
# 			# @staticmethod
# 			def angleadd(a, b, c, d, e, f, g, dr):####TODO
# 				"""(ax^2 + bx + c) + (dx^2 + ex + f) = g"""
# 				pass

class stats():####Make Sample Stats Modular
	"""Stats"""

	def mean(self, slist):
		"""return mean/average of slist"""
		x = sum(slist)
		y = float(x)/float((len(slist)))
		return y
	
	def median(self, slist):
		"""return median of slist"""
		sort = sorted(slist)
		if len(slist) % 2 == 0:
			x = (float(sort[(len(slist)/2) - 1]) + float(sort[(len(slist)/2)]))/2
		else:
			x = sort[(len(slist))/2]
		return x
	
	def mode(self, slist):####fix for more than one mode
		"""return mode of slist"""
		d = {}
		for i in slist:
			try:
				d[i] += 1
			except KeyError:
				d[i] = 1
		x = max(d, key=d.get)
		if x == 1: return 'No Mode'
		if x != 1: return x

	def range(self, slist):
		"""return range of slist"""
		sort = sorted(slist)
		x = sort[-1] - sort[0]
		return x
	
	def midrange(self, slist):
		"""return midrange of slist"""
		sort = sorted(slist)
		x = (sort[0] + sort[-1])/2
		return x

	def zscore(self, m, sd, x):
		"""m=mean, sd=standard deviation, x=score
		return z-score"""
		y = (float(x) - float(m)) / float(sd)
		return y
	
	def zscores(self, m, sd, x, y):
		"""m=mean, sd=standard deviation, x=score 1, y=score2
		return z-scores"""
		i = (float(x) - float(m)) / float(sd)
		j = (float(y) - float(m)) / float(sd)
		return i, j
	
	def dev(self, slist):
		"""Sample Deviation"""
		sdv = []
		for i in slist:
			li = (float(i) - float(m))
			sdv.append(li)
		return sdv
		
	def devmean(self, slist):
		"""Sample Deviation Mean"""
		s3 = float(sum(dev(slist))) / len(dev(slist))
		return s3
		
	def devsqr(self, slist):
		"""Sample Deviation Squares"""
		sqdv = []
		for i in slist:
			li = (float(i) - float(mean(slist))) * (float(i) - float(mean(slist)))
			sqdv.append(li)
		return sqdv
		
	def samplevar(self, slist):
		"""Sample Variance"""
		s1 = sum(devsqr(slist))
		s2 = float(s1) / len(devsqr(slist))
		return s2
		
	def samplestandev(self, slist):
		"""Sample Standard Deviation"""
		x = samplevar(slist)
		return math.sqrt(x)
		
	def estsamplevar(self, slist):
		"""Estimated Sample Variance"""
		s2u = float(sum(devsqr(slist))) / (len(devsqr(slist)) - 1)
		return s2u
		
	def estsamplestandev(self, slist):
		"""Estimated Sample Standard Deviation"""
		x = estsamplevar(slist)
		return math.sqrt(x)
		
	def sample(self, slist):
		"""Print:
		Table: Sample, Deviation, Deviation Squares
		
		Sample mean, 
		Sample Deviation Mean, 
		Sample Deviation Squares Mean,
		
		Sample Variance,
		Sample Variance Deviation,
		
		Estimated Sample Variance,
		Estimated Sample Sample Variance Deviation"""
		print '%08s	%08s	%08s' % ('Sample  ', 'Deviation', 'SquareDev'), '\n' + '-'*35
		for i in range(len(slist)):
			print '%06f	%06f	%06f' % (slist[i], round((stats.dev(slist))[i], 5), round((stats.devsqr(slist))[i], 5))
		print '\n'
		print 'Sample Mean =', stats.mean(slist)
		print 'Deviation Mean =', stats.devmean(slist)
		print 'Deviation Square Mean =', sum(stats.devsqr(slist)), '\n'
		print 'Sample Variance =', stats.samplevar(slist)
		print 'Sample Standard Deviation =', math.sqrt(stats.samplevar(slist)), '\n'
		print 'Est. Sample Variance =', stats.estsamplevar(slist)
		print 'Est. Sample Standard Deviation =', math.sqrt(stats.estsamplevar(slist)), '\n'
	
	def boxplot(self, slist):####ADD DRAW BOXPLOT
		"""return minimum, q1, mean, q3, maxium 
		for box and whisker plot"""
		sort = sorted(slist)
		if len(slist) % 2 == 0:
			a, b = misc.splitlist(sort, 2)
			q3 = stats.median(b)
			q1 = stats.median(a)
		else:
			a, b = misc.splitlist(sort, 2)
			b.pop(0)
			q3 = stats.median(b)
			q1 = stats.median(a)
		q2 = stats.median(sort)
		m2 = sort.pop(-1)
		m1 = sort.pop(0)
		return m1, q1, q2, q3, m2

# class area():
# 	"""Area"""
#
# 	def square(self, a):
# 		"""a=side 1
# 		return a*a"""
# 		x = a * a
# 		return x
#
# 	def rectangle(a, b):
# 		"""a=side 1, b=side 2
# 		return a*b"""
# 		x = a * b
# 		return x
#
# 	def parallelogram(b, h):
# 		"""b=base, h=height
# 		return b*h"""
# 		x = b * h
# 		return x
#
# 	def trapezoid(b1, b2, h):
# 		"""b1=base 1, b2=base 2, h=height
# 		return (h/2)*(b1+b2)"""
# 		x = (h / 2)*(b1 + b2)
# 		return x
#
# 	def circle(r):
# 		"""r=radius
# 		return pi*(r*r)"""
# 		x = constant.pi * (r * r)
# 		return x
#
# 	def ellipse(r1, r2):
# 		"""r1=long radius, r2=short radius
# 		return pi*r1*r2"""
# 		x = constant.pi * r1 * r2
# 		return x
#
# 	def triangle(b, h):
# 		"""b=base, h=height
# 		return (1/2)*b*h"""
# 		x = (1/2) * b * h
# 		return x
#
# 	def equilateral(a):
# 		"""a=side
# 		return (sqrt(3)/4)*(a*a)"""
# 		x = (math.sqrt(3)/4) * (a * a)
# 		return x
#
# class volume():
# 	"""Volume"""
# 	# @staticmethod
# 	def cube(a):
# 		"""a=side
# 		return a * a*a"""
# 		x = a * a * a
# 		return x
#
# 	# @staticmethod
# 	def rectprism(a, b, c):
# 		"""a=side 1, b=side 2, c=side 3
# 		return a*b*c"""
# 		x = a * b * c
# 		return x
#
# 	# @staticmethod
# 	def irrprism(b, h):
# 		"""b=base area, h=height
# 		return b*h"""
# 		x = b * h
# 		return x
#
# 	# @staticmethod
# 	def cylinder(r, h):
# 		"""r=radius, h=height
# 		return pi*(r*r)*h"""
# 		x = con.pi * (r * r) * h
# 		return x
#
# 	# @staticmethod
# 	def pyramid(b, h):
# 		"""b=base area, h=height
# 		return (1/3)*b*h"""
# 		x = (1/3) * b * h
# 		return x
#
# 	# @staticmethod
# 	def cone(r, h):
# 		"""r=radius, h=height
# 		return (1/3)*pi*(r*r)*h"""
# 		x = (1/3) * con.pi * (r * r) * h
# 		return x
#
# 	# @staticmethod
# 	def sphere(r):
# 		"""r=radius
# 		return (4/3)*con.pi*(r*r*r)"""
# 		x = (4/3) * con.pi * (r * r * r)
# 		return x
#
# 	# @staticmethod
# 	def ellipsoid(r1, r2, r3):
# 		"""r1=radius 1, r2=radius 2, r3=radius 3
# 		return (4/3)*pi*(r1*r2*r3)"""
# 		x = (4/3) * con.pi * (r1 * r2 * r3)
# 		return x
#
# class surfacearea():
# 	"""Surface Area"""
# 	# @staticmethod
# 	def cube(a):
# 		"""a=side
# 		return 6*(a*a)"""
# 		x = 6 * (a * a)
# 		return x
#
# 	# @staticmethod
# 	def rectprism(a, b, c):
# 		"""a=side 1, b=side 2, c=side 3
# 		return (2*a*b) + (2*a*c) + (2*b*c)"""
# 		x = (2 * a * b) + (2 * a * c) + (2 * b * c)
# 		return x
#
# 	# @staticmethod
# 	def irrprism(p, h, b):
# 		"""p=perimiter, h=height, b=base area
# 		return (p*h) + (2*b)"""
# 		x = (p*h) + (2*b)
# 		return x
#
# 	# @staticmethod
# 	def sphere(r):
# 		"""r=radius
# 		return 4*pi*(r*r)"""
# 		x = 4*con.pi*(r*r)
# 		return x
#
# 	# @staticmethod
# 	def cylinder(r, h):
# 		"""r=radius, h=height
# 		return (2*pi*(r*r))+(2*pi*r*h)"""
# 		x = (2*con.pi*(r*r))+(2*con.pi*r*h)
# 		return x
#
# 	# @staticmethod
# 	def pyramid3(b, h):
# 		"""b=base, h=height
# 		return ((1/2)*((((1/2)*b)*((1/2)*b))+(h*h))*b*3)+((sqrt(3)/4)*(b*b))"""
# 		x = ((1/2)*((((1/2)*b)*((1/2)*b))+(h*h))*b*3)+((math.sqrt(3)/4)*(b*b))
# 		return x
#
# 	# @staticmethod
# 	def pyramid4(b, h):
# 		"""b=base, h=height
# 		return ((1/2)*((((1/2)*b)*((1/2)*b))+(h*h))*b*4)+(b*b)"""
# 		x= ((1/2)*((((1/2)*b)*((1/2)*b))+(h*h))*b*4)+(b*b)
# 		return x
#
# class perimeter():####TODO
# 	"""Perimeter"""
# 	pass
#
# class generators():
# 	"""Generators"""
# 	# @staticmethod
# 	def primes(n):
# 		"""return primes up to n"""
# 		if n==2: return [2]
# 		elif n<2: return []
# 		s=range(3,n+1,2)
# 		mroot = n ** 0.5
# 		half=(n+1)/2-1
# 		i=0
# 		m=3
# 		while m <= mroot:
# 			if s[i]:
# 				j=(m*m-3)/2
# 				s[j]=0
# 				while j<half:
# 					s[j]=0
# 					j+=m
# 			i=i+1
# 			m=2*i+3
# 		return [2]+[x for x in s if x]
#
# 	# @staticmethod
# 	def fib(n):
# 		"""return Fibonacci series up to n"""
# 		fiblist = []
# 		a, b = 0, 1
# 		while b < n:
# 			fiblist.append(b)
# 			a, b = b, a+b
# 		return fiblist
#
# class fractals():####TODO
# 	"""Fractals"""
# 	pass
#
# class unitconversion():####TODO
# 	"""Unit Conversion"""
# 	pass
#
# class gases():
# 	"""Gases"""
# 	# @staticmethod
# 	def boyleslaw(p=None, V=None, k=None):
# 		"""pV = k
# 		p=pressure Pa, V=volume m^3, k=constant
# 		Given two values, return third"""
# 		#~ vc = 0
# 		#~ for i in locals().values():
# 			#~ if i is None:
# 				#~ vc += 1
# 		#~ if vc > 1:
# 			#~ raise ValueError('Too Many Variables')
# 		# countvar(boyleslaw)
#
# 		print 'These =' + str(locals())
# 		print 'Are These =' + str(locals().values())
#
# 		if p is None:
# 			return 1.0 * k / V
# 		elif V is None:
# 			return 1.0 * k / p
# 		elif k is None:
# 			return 1.0 * p * V
#
# 	# @staticmethod
# 	def charleslaw(V=None, T=None, k=None):
# 		"""V/T = k
# 		V=volume m^3, T=temperature K, k=constant
# 		Given two values, return third"""
# 		assert (V is None) + (T is None) + (k is None) == 1, 'exactly 2 of V, T, k must be given'
#
# 		if V is None:
# 			return 1.0 * k * T
# 		elif T is None:
# 			return 1.0 * V * k
# 		elif k is None:
# 			return 1.0 * V / T
#
# 	# @staticmethod
# 	def gaylussacslaw(p=None, T=None, k=None):
# 		"""p/T = k
# 		p=pressure Pa, T=temperature K, k=constant
# 		Given two values, return third"""
# 		assert (p is None) + (T is None) + (k is None) == 1, 'exactly 2 of p, T, k must be given'
#
# 		if p is None:
# 			return 1.0 * k * T
# 		elif T is None:
# 			return 1.0 * p / k
# 		elif k is None:
# 			return 1.0 * p / T
#
# 	# @staticmethod
# 	def combinedgaslaw(p=None, V=None, T=None, k=None):
# 		"""(pV)/T = k
# 		p=pressure Pa, V=volume m^3,
# 		T=temperature K, k=constant
# 		Given three values, return fourth"""
# 		assert (p is None) + (V is None) + (T is None) + (k is None) == 1, 'exactly three of p, V, T, k must be given'
#
# 		if p is None:
# 			return 1.0 * (k * T) / V
# 		elif V is None:
# 			return 1.0 * (k * T) / p
# 		elif T is None:
# 			return 1.0 * (p * V) / k
# 		elif k is None:
# 			return 1.0 * (p * V) / T
#
# 	# @staticmethod
# 	def idealgaslaw(p=None, V=None, n=None, R=con.R, T=None):
# 		"""pV = nRT
# 		p=pressure Pa, V=volume m^3,
# 		n=# of particles mol, R=Gas Constant,
# 		T=temperature K
# 		Given four values, return fifth"""
# 		assert (p is None) + (V is None) + (n is None) + (R is None) + (T is None) == 1, 'exactly four of p, V, n, R, T must be given'
#
# 		if p is None:
# 			return 1.0 * (n * R * T) / V
# 		elif V is None:
# 			return 1.0 * (n * R * T) / p
# 		elif n is None:
# 			return 1.0 * (p * V) / (R * T)
# 		elif R is None:
# 			return 1.0 * (p * V) / (n * T)
# 		elif T is None:
# 			return 1.0 * (p * V) / (n * R)
#
# class electromag():####TODO
# 	"""Electromag"""
#
# 	def coulombslaw():####TODO
# 		""" """
# 		pass
#
# 	def ohmslaw(P, I, R):####TODO
# 		""" """
# 		pass


class Mechanics(object):
	
	def __init__(self):
		super(Mechanics, self).__init__()
		object.__init__(self)
		
		
