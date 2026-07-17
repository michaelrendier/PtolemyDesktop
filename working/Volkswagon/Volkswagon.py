#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://pastebin.com/N51AZjC6

import engine
import transmission
import electrical
import cooling
import drivetrain
import fuel
import brakes
import steering
import seating
import doors
import hood
import trunk
import windows
import dashboard
from errors import DeadBatteryError

class Passat(object):
	
	def __init__(self, parent=None):
		super(Passat, self).__init__(parent)
		
		self.parent = parent
		
		self.engine = engine
		self.transmission = transmission
		self.electrical = electrical
		self.cooling = cooling
		self.drivetrain = drivetrain
		self.fuel = fuel
		self.brakes = brakes
		self.steering = steering
		self.seating = seating
		self.doors = doors
		self.hood = hood
		self.trunk = trunk
		self.windows = windows
		self.dashboard = dashboard


class KeyFob(object):
	
	def __init__(self, parent=None):
		super(KeyFob, self).__init__(parent)
		
		self.parent = parent
		self.identity = "VEHICLE VIN NUMBER"
	
	def lockPressEvent(self, event):
		
		try:
			self.parent.doors.lock()
			return event
		
		except DeadBatteryError:
			pass
		
		
	
	def unlockPressEvent(self, event):
		
		try:
			self.parent.doors.unlock()
			return event
		
		except DeadBatteryError:
			pass
		
		
	
	def trunkPressEvent(self, event):
		
		try:
			self.parent.trunk.open()
			return event
		
		except DeadBatteryError:
			pass
	
	def is_authentic(self):
		return self.identity