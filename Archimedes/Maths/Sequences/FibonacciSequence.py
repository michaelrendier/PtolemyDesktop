#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from math import sqrt

def fibonacci_number(n):
    """
    Return the nth fibonacci number
    :param n:
    :return:
    """
    a = 1
    b = 1
    fib = 0
    for i in range(n - 2):
        fib = a + b
        a = b
        b = fib

    return fib

def fibonacci_series(n):
    """
    Return a sequence of length n of
    Fibonacci numbers
    :param n:
    :return:
    """
    a = 1
    b = 1
    fib = 0
    fibList = [a, b]
    for i in range(n - 2):
        fib = a + b
        fibList.append(fib)
        a = b
        b = fib

    return fibList


def explicit_formula_fibonacci_number(n):
    """
    Explicit formula for the nth
    Fibonacci Number
    :param n: 
    :return: nth Fibonacci Number
    """
    return int(((1 + sqrt(5))**n - (1 - sqrt(5))**n)/(2**n*sqrt(5)))

if __name__ == '__main__':
    for i in range(10000):
        print("!", i, "FIB", f"{explicit_formula_fibonacci_number(i)}")


def fibonacci_music(fib, modulus): #TODO
    """
    Pisano Period.  Divide all numbers of the fibonacci
    sequence by a modulus, take the remainder (fib % 7)
    and use those as notes.
    :param fib: fibonacci number
    :param modulus: number to divide by for remainder
    :return: fib % modulus
    """


    pass