#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

# Stern-Brocot sequence...
# add previous two terms, and add last term of the two added
#
#____  ____  ____
#1, 1, 2, 1, 3, 2, 3, 1, 4, 3, 5, 2, 5, 3
#   ----  ----  ----
#
# as fractions:
# 1/1, 1/2, 2/1, 1/3, 3/2, 2/3, 3/1, 1/4, 4/3, 3/5, 5/2, 2/5, 5/3
# lists all possible fractions in most simplified form.  1/2 exists
# and you will not ever find 2/4 or 5/10 etc...