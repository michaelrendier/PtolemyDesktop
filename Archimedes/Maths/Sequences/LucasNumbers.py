#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

# Lucas Numbers
# 1, 3, 4, 7, 11, 18, 29, 47, 76, 123

def lucas_number(n):
    """
    Return the nth lucas number
    Can be used to rule out primes and find
    Lucas Psuedo-Primes
    :param n:
    :return:
    """
    a = 1
    b = 3
    luca = 0
    for i in range(n - 2):
        luca = a + b
        a = b
        b = luca

    return luca

def lucas_series(n):
    """
    Return a sequence of length n of
    Luca's numbers
    :param n:
    :return:
    """
    a = 1
    b = 1
    luca = 0
    lucaList = [a, b]
    for i in range(n - 2):
        luca = a + b
        lucaList.append(luca)
        a = b
        b = luca

    return lucaList

def lucas_lehmer_number(n):
    """
    Return the nth luca's-lehmer number
    can check primes of 2**n-1 (mersenne primes)
    Luca's-Lehmer number n-1 is divisible by 2**n - 1
    the number 2**n-1 is definitely prime

    :param n:
    :return:
    """
    a = 4
    luca = 0
    for i in range(n - 1):
        luca = a**2 - 2
        a = luca

    return luca


def lucas_lehmer_sequence(n):
    """
    Return a list of luca's-lehmer numbers of
    length n.  can check primes of 2**n-1 (mersenne primes)
    Luca's-Lehmer number n-1 is divisible by 2**n - 1
    the number 2**n-1 is definitely prime
    :param n:
    :return:
    """
    a = 4
    luca = 0
    lucaLehmerList = [a]
    for i in range(n - 1):
        luca = a ** 2 - 2
        lucaLehmerList.append(luca)
        a = luca

    return lucaLehmerList

# mercen primes can be used taking remainder
# of nth luca's-lehmer number mod(n) and if
# 2**n-1 mod(n) leads to a zero