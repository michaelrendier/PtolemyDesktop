# crs.py; simple illustration of curses library, consisting of a very
# unexciting "game"; keeps drawing the user's input characters into a
# box, filling one column at a time, from top to bottom, left to right,
# returning to top left square when reach bottom right square

# the bottom row of the box is displayed in another color

# usage: python crs.py boxsize

# how to play the "game": keep typing characters, until wish to stop,
# which you do by hitting the q key

import curses, sys, traceback

# global variables

class gb:
	boxrows = int(sys.argv[1]) # number of rows in the box
	boxcols = boxrows # number of columns in the box
	scrn = None # will point to window object
	row = None # current row position
	col = None # current column position

def draw(chr):
	# paint chr at current position, overwriting what was there; if it's
	# the last row, also change colors; if instead of color we had
	# wanted, say, reverse video, we would specify curses.A_REVERSE instead of
	# curses.color_pair(1)
	if gb.row == gb.boxrows-1:
		gb.scrn.addch(gb.row,gb.col,chr,curses.color_pair(1))
	else:
		gb.scrn.addch(gb.row,gb.col,chr)
	# implement the change
	gb.scrn.refresh()
	# move down one row
	gb.row += 1
	# if at bottom, go to top of next column
	if gb.row == gb.boxrows:
		gb.row = 0
		gb.col += 1
		# if in last column, go back to first column
		if gb.col == gb.boxcols: gb.col = 0

# this code is vital; without this code, your terminal would be unusable
# after the program exits
def restorescreen():
	# restore "normal"--i.e. wait until hit Enter--keyboard mode
	curses.nocbreak()
	# restore keystroke echoing
	curses.echo()
	# required cleanup call
	curses.endwin()

def main():
	# first we must create a window object; it will fill the whole screen
	gb.scrn = curses.initscr()
	# turn off keystroke echo
	curses.noecho()
	# keystrokes are honored immediately, rather than waiting for the
	# user to hit Enter
	curses.cbreak()
	# start color display (if it exists; could check with has_colors())
	curses.start_color()
	# set up a foreground/background color pair (can do many)	
	curses.init_pair(1,curses.COLOR_RED,curses.COLOR_WHITE)
	# clear screen
	gb.scrn.clear()
	# set current position to upper-left corner; note that these are our
	# own records of position, not Curses'
	gb.row = 0
	gb.col = 0
	# implement the actions done so far (just the clear())
	gb.scrn.refresh()
	# now play the "game"
	while True:
		# read character from keyboard
		c = gb.scrn.getch()
		# was returned as an integer (ASCII); make it a character
		c = chr(c)
		# quit?
		if c == 'q': break
		# draw the character
		draw(c)
	# restore original settings
	restorescreen()

if __name__ =='__main__':
	# in case of execution error, have a smooth recovery and clear
	# display of error message (nice example of Python exception
	# handling); it is recommended that you use this format for all of
	# your Python curses programs; you can automate all this (and more)
	# by using the built-in function curses.wrapper(), but we've shown
	# it done "by hand" here to illustrate the issues involved
	try:
		main()
	except:
		restorescreen()
		# print error message re exception
		traceback.print_exc()
