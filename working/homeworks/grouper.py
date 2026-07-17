#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from itertools import zip_longest


def grouper(n, iterable, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)

names = ['name1', 'name2', 'name3', 'name4', 'name5', 'name6']
for item1 in grouper(5, names, 'None'):
    print('\t'.join(item1))