import curses
import time
import random
from curses import wrapper

stdscr = curses.initscr()


# print(" cow")

def main(stdscr):
	stdscr.clear()
	
	stdscr.addstr(10, 5, "It's just one of those days")
	
	while True:
		def dog():
			x = ["moose", "horse", "cat"]
			p = random.randint(1, 10)
			r = random.choice(x)
			stdscr.addstr(5, p, r)
			stdscr.refresh()
			time.sleep(1)
			stdscr.clear()
			stdscr.addstr(10, 5, "It's just one of those days")
			stdscr.refresh()
		
		def g():
			b = ["cow", "frog", "pig"]
			p = random.randint(1, 10)
			a = random.choice(b)
			stdscr.addstr(7, p, a)
			stdscr.refresh()
			time.sleep(1)
			stdscr.clear()
			stdscr.addstr(10, 5, "It's just one of those days")
			stdscr.refresh()
		
		c = stdscr.getch(14, 5)
		if c == ord("d"):
			dog()
		
		
		
		elif c == ord("g"):
			g()
		elif c == ord("q"):
			break


wrapper(main)
