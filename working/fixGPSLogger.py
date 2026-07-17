#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'


import os, sys

cwd = '/home/rendier/Dropbox/Apps/GPSLogger for Android/'

for i in os.listdir(cwd):
    # print(i)
    if os.path.isdir(cwd + i):
        os.chdir(cwd + i)
        os.system('cp *.kml ..')