#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


def mersenne(x, n):
    """
    Mersenne Sequence
    f(x) = 2x + 1
    :param x: starting x value
    :param n: length of sequence desired
    :return:
    """
    sequence = []
    for i in range(n):
        y = 2 * x + 1
        sequence.append([y])
        print("i =", i, "X =", x, "Y =", y)
        x = y

    return sequence