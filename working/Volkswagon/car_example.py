#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

# https://pastebin.com/xAUNRFrK

from Volkswagon import Passat
from Volkswagon import KeyFob

class Car(Passat):
	
	def __init__(self, parent=None):
		super(Car, self).__init__(parent)
		
		self.parent = parent
		self.make = 'Volkswagon'
		self.model = 'Passat'
		self.year = 2004
		self.powertrain = 'Turbo Diesel'
		self.vehicle_class = "GLS"
		self.engine_size = "2.0 L"
		self.vehicle_type = 'Wagon'
		
		self.key = KeyFob(parent=self)
		
		if self.key.is_authentic() == "VEHICLE VIN NUMBER":
			self.unlock_doors()
		
		
	def start_car(self, key):
		
		if key.is_authentic == "VEHICLE VIN NUMBER":
			self.engine.start()
		else:
			pass
		
	def lock_doors(self, key): ##
		
		if key.lockPressEvent and self.doors.latch_state == 'Unlocked':
			self.doors.lock(key)
		else:
			pass
		
	def unlock_doors(self, key):
		
		if key.unlockPressEvent:
			self.doors.unlock(key)
			
			
if __name__ == "__main__":
	MyCar = Car()
	MyCar.start_car()