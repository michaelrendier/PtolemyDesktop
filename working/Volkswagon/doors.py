#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://pastebin.com/qADTRPAk

import window
import buttons
import keylock
import handle
import latch


def raise_windows():
	
	if buttons.window_up.Pressed:
		window.close()
		

def lower_windows():
	
	if buttons.window_down.Pressed:
		window.open()
		
def lock(key):
	
	if key.is_authentic() == "VEHICLE VIN NUMBER" and (key in keylock or key.lockPressEvent or buttons.lockPressEvent):
		latch.state = "Locked"
		
def unlock(key):
	
	if key.is_authentic() == "VEHICLE VIN NUMBER" and (key in keylock or key.lockPressEvent or buttons.unlockPressEvent):
		latch.state = "Unlocked"
		
def open():
	
	if latch.state == "Unlocked" and handle.pulledEvent:
		door_state = "Opened"
		
def close():
	
	door_state = "Closed"
	
