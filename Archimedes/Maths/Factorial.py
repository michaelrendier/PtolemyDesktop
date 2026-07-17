#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
from math import sqrt, pi, e

class Factorial(object):

    def __init__(self):
        super()

    def factorial(self, n):

        for i in list(range(1, n + 1))[-2::-1]:
            n *= i

        return n

    def doubleFactorial(self, n):
        df = n

        for i in list(range(n, 0, -2))[1:]:
            df *= i

        return df

    def subFactorial(self, n):
        sign = -1
        summation = [1]

        for i in list(range(1, n + 1)):
            summation.append(sign * (1 / self.factorial(i)))
            sign *= -1

        aSum = 0
        for i in summation:
            aSum += i

        sf = self.factorial(n) * aSum

        return sf

    def sloaneSF(self, n):
        sf = 1

        for i in [self.factorial(i) for i in list(range(1, n + 1))]:
            sf *= i

        return sf

    def pickoverSF(self, n):
        fact = self.factorial(n)
        sf = fact

        for i in list([fact] * fact)[1:]:
            sf = sf ** i

        return sf

    def expFact(self, n):
        ef = n

        for i in list(range(n, 0, -1))[1:]:
            ef = ef ** i

        return ef

    def hyperFact(self, n):
        hf = n ** n

        for i in list(range(n, 0, -1))[1:]:
            hf *= i ** i

        return hf

    def stirlingApprox(self, n):
        aFact = sqrt(2 * pi * n) * (n / e) ** n

        return aFact