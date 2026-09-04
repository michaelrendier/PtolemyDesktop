#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from math import *
from turtle import Turtle

# (1/2) < floor(divmod(floor(y/17) * 2**(-17 * floor(x) - divmod(floor(y), 17)), 2))

def tuppers_self_referential_formula(x, y=None, height=17):
    """

    :param x: x coordinate
    :param y: y coordinate
    :param height: height of image
    :return:
    """
    return (1/2) < floor(divmod(floor(y/height) * 2**(-height * floor(x) - divmod(floor(y), height)), 2))

def binary_to_decimal(binary, height=17):
    return int(binary, 2) * height
