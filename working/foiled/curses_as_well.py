#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
This is a tutorial for curses. Curses is a Python library that helps you handle
keyboard input and control the displayed text on the terminal. The tutorial
closely follows.

We'll jump in with the structure of a basic curses program.
"""

import curses

def main():
    # create a window object that represents the terminal window
    stdscr = curses.initscr()
    
    # Don't print what I type on the terminal
    curses.noecho()
    # React to every key press, not just when pressing "enter"
    curses.cbreak()
    # Enable easy key codes (will come back to this)
    stdscr.keypad(True)
    # Proceed with your program
    print("Running some program...")
    # Clean up after yourself
    teardown(stdscr)

def teardown(stdscr):
    # reverse everything that you changed about the terminal
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    # restore the terminal to its original state
    curses.endwin()

main()

"""
Unfortunately, if something goes wrong during your part of the program, it can
exit without running the teardown function. That could leave your terminal in
a weird state because curses messed with it. Curses has an answer to this
problem that also happens to make all of the above code a lot easier to write.
"""

import curses
from curses import wrapper

def main(stdscr):
    # Clear screen
    stdscr.clear()
    # Proceed with your program
    print("Running some program")

# wrapper is a function that does all of the setup and teardown, and makes sure
# your program cleans up properly if it errors!
wrapper(main)

"""
Using the wrapper function is much cleaner, as you can see. From now on, we'll
just modify what's inside the function `main`, and assume we have the import and
the wrapper set up as above.
Now we can learn how to handle user input.

When the user presses a key, we want to be able to handle that action. The first
step in doing so is discovering which key was pressed. The function `getch` does
this for us. It returns a value that we can compare like so:
c = stdscr.getch()
c == ord('a') # Do this to check for a letter key
c == curses.KEY_UP # Do this to check for special keys
See https://docs.python.org/3.5/library/curses.html#constants for all special
key values.
"""

def main(stdscr):
    stdscr.clear()
    while True:
        # Store the key value in the variable `c`
        c = stdscr.getch()
        # Clear the terminal
        stdscr.clear()
        if c == ord('a'):
            stdscr.addstr("You pressed the 'a' key.")
        elif c == curses.KEY_UP:
            stdscr.addstr("You pressed the up arrow.")
        else:
            stdscr.addstr("This program doesn't know that key.....")

"""
What's stdscr.addstr? That's curses' way of printing. Later, we'll see that it
can also take arguments like y and x positions, which tell it where to print
the string on the terminal. For now, it just prints wherever the cursor is.
It's important to note that stdscr.clear, which is called in the block above,
not only clears the terminal, but also moves the cursor back to the top left.

You may have noticed that the program waits at stdscr.getch for the user to
press a key. We call this behavior "blocking", and would say that stdscr.getch
blocks the flow of the program. For some programs, this is useful. For others,
often in the case of games, this is not the desired behavior. Thankfully, curses
allows non-blocking key input as well.
"""

import time

def main(stdscr):
    # Make stdscr.getch non-blocking
    stdscr.nodelay(True)
    stdscr.clear()
    width = 4
    count = 0
    direction = 1
    while True:
        c = stdscr.getch()
        # Clear out anything else the user has typed in
        curses.flushinp()
        stdscr.clear()
        # If the user presses p, increase the width of the springy bar
        if c == ord('p'):
            width += 1
        # Draw a springy bar
        stdscr.addstr("#" * count)
        count += direction
        if count == width:
            direction = -1
        elif count == 0:
            direction = 1
        # Wait 1/10 of a second. Read below to learn about how to avoid
        # problems with using time.sleep with getch!
        time.sleep(0.1)

"""
Calling stdscr.nodelay(True) made stdscr.getch() non-blocking. If Python gets to
that line and the user hasn't typed anything since last time, getch will return
-1, which doesn't match any key.

What if the user managed to type more than one character since the last time
getch was called? All of those characters will start to build up, and getch will
return the value for each one in the order that they came. This can cause
delayed reactions if you're writing a game. After getch, you can call
curses.flushinp to clear out the rest of the characters that the user typed.

This is a good place to talk more about getch.

Every time the user presses a key, that key's value gets stored in a list. When
getch is called, it goes to that list and pops that value. If the user manages
to press several keys before getch is called, getch will pop the least recently
added value (the oldest key pressed). The rest of the keys remain in the list!
The process continues like this. So there's a problem if there is a delay
between calls to getch: Key values can build up. If you don't want this to
happen, curses.flushinp() clears the list of inputted values. This ensures that
the next key the user presses after curses.flushinp() is what getch will return
next time it is called.
"""

"""
To continue learning about curses, checkout the addstr method to see how you can
print strings at certain y, x coordinates. You can start here:
https://docs.python.org/3/library/curses.html#window-objects
"""