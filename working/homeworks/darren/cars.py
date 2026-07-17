import time
import operator
from collections import namedtuple
from dataclasses import dataclass
from getch import getch
import os


@dataclass
class MachGOGOGODC:
	contestant_name: str
	car_name: str
	car_number: int
	number_of_contestants: int
	height: float
	power: str


MachGOGOGO = namedtuple('MachGOGOGO', ['contestant_name', 'car_name', 'car_number', 'number_of_contestants', 'height', 'power'])

car1 = MachGOGOGO("Team UCEN", "123", 7, 1, 10, "Turbo")
print("Named Tuple: car1", car1)
car2 = MachGOGOGO("Go Mifune", "Mach 5", 5, 1, 4.5, "Turbo")
car3 = MachGOGOGO("Racer X", "Shooting Star", 9, 1, 3.0, "Fly")
car4 = MachGOGOGO("Cruncher Block Spritle", "Mammoth Car", 00, 2, 9, "Destroy Others")
car5 = MachGOGOGO("Flash Marker", "X3", 3, 1, 2.5, "Turbo")
car6 = MachGOGOGO("Ben Cranem", "GRX", 66, 1, 5, "Fly")
car7 = MachGOGOGO("Kim Jugger Snake Oiler", "Black Tiger", 4, 2, 7, "Turbo")
car8 = MachGOGOGO("Grey Ghost Trixie", "Fumee", 23, 2, 2, "Invincible")
print("THISONE", [i for i in dir(car1) if not i.startswith("_")])


car_list = [car1, car2, car3, car4, car5, car6, car7, car8]

def sortCar(car_list, sortby='car_number'):
	print(f"SORTING by: {sortby}")
	#print(car_list.sort(key=operator.attrgetter(sortby)))
	## Changed this to below using sorted() and 'return' the sorted_list
	## https://stackoverflow.com/questions/12087905/pythonic-way-to-sorting-list-of-namedtuples-by-field-name
	sorted_list = sorted(car_list, key=operator.attrgetter(sortby))
	# print(sorted_list)
	return sorted_list
	
def display(car_list):
	## you can work straight with each car by iterating over the list of objects, and reduce the printing function to this.
	print(f"{'Contestant Name':^25} | {'Car Name':^15} | {'Car Number':^10} | {'Number Of Contestants':^25} | {'Height':^10} | {'Power':^10}")
	print("-" * 115)
	for car in car_list:
		print(f"{car.contestant_name:25} | {car.car_name:15} | {car.car_number:10} | {car.number_of_contestants:25} | {car.height:10} | {car.power:10}")
	print("-" * 115)


## I added most of your script to functions to streamline the functionality and using continuous calls (regression) to imitate a main program loop
def main():
	print("Please select an option to begin the game")
	time.sleep(1)
	mode = input("Press 1 to view all racers, Press 2 to sort racers, Press 3 to begin the game or press 4 to exit:\n>")
	
	## Typecheck mode to make sure a number was entered using str().isdigit()
	if str(mode).isdigit():
		
		## input returns strings automatically, so use strings to check mode: "1", '2' etc.
		if mode == '1':
			display(car_list)
			
		elif mode == '2':
			sortby = input("Sort list by which index?\n>")
			## Check if sortby input is in the dictionary of arguments for the dataclass.  This is one advantage
			## over namedtuples, the automagical .__dict__ method created by a dataclass.
			if sortby in car1._asdict():  ## Using car1._asdict() allows me to check if the input exists in the parameters of the named tuple
				display(sortCar(car_list, sortby=sortby))
			else:
				print(f"The key parameter '{sortby}' does not exist.\nReturning to main menu.\n")
			
		elif mode == '3':
			print("Starting Game\n{INSERT GAME FUNCTION HERE}\nReturning to main menu.\n")
		
		## Since this function calls itself, in order to exit the program,
		## you 'return' OUT of the function and the program dies without main() being called again.
		elif mode == '4':
			print("Exiting Program")
			return
		else:
			print("No Mode")
			
		## Calling main() again will create a loop that continues on until
		## # 4 is pressed and you 'return' from the function
		main()
	
	## If main input was not a number
	else:
		print("You must enter a digit to proceed")
		## Calling main() again will create a loop that continues on until
		## # 4 is pressed and you 'return' from the function
		main()
	
	
## if you run this program, it's namespace is '__main__', and main() is called.
## if this is imported into another program, it's namespace will not be '__main__', and main() will not be called.
if __name__ == "__main__":
	main()
	