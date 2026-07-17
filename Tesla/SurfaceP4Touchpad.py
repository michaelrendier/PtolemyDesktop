#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from subprocess import Popen, PIPE
import os


def cycleTouchpad():

	command = """xinput --list-props "Microsoft Surface Type Cover Touchpad" | grep \'Device Enabled\'"""

	process = Popen(args=command, stdout=PIPE, stderr=PIPE, shell=True).communicate()

	state = int(process[0].decode().split("\t")[-1].replace("\n", ""))

	if state == 0:
		os.system("xinput --enable 'Microsoft Surface Type Cover Touchpad'")

	elif state == 1:
		os.system("xinput --disable 'Microsoft Surface Type Cover Touchpad'")


