#!/usr/bin/python3
# -*- coding: utf-8 -*-
__title__ = 'Curse of Gemini'
__author__ = 'rendier'

import curses
# ~ import threading
# ~ import queue
from curses import start_color

DEBUG = True
DEVICE_ID_FILE = "device_id.json"

class GeminiChat():


    def __init__(self, **kwargs):
        self.min_x = 0
        self.min_y = 0
        self.max_x = 0
        self.max_y = 0
        self.gemini_chat_window = None
        self.gemini_input_window = None
        self.gemini_border_window = None

        self.Gemini = self.start_curse()
        self.curse_windows()
        while True:
            self.stdscr.getch()

    def text_wrapping(self, text: str, width: int, ):
        lines = ""
        current_line = 0
        start = 0

        while start < len(text):
            end = text.find(" ", start)
            if end == "":
                current_line += text[start:]
                start = len(text)
            else:

                word = text[start, (end - start)]
                if len(current_line) + len(word) + 1 > width:
                    if current_line == "":
                        lines += current_line

                    current_line = word

                else:
                    if current_line != "":
                        current_line += " "

                    current_line += word

                start = end + 1

            if len(current_line) > width:
                lines += current_line[0:width]
                current_line = current_line[width]


        if current_line != "":
            lines += current_line

        return lines



        return

    def start_curse(self):
        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(True)
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        if DEBUG == True:
            print ("Max Y =: ", self.max_y, "Max X =: ", self.max_x)
        curses.curs_set(1)
        curses.set_escdelay(3)
        # ~ if curses.has_colors():
            # ~ curses.start_color()
            # ~ curses.init_pair(1, COLOR_RED, COLOR_BLACK)
            # ~ curses.init_pair(2, COLOR_CYAN, COLOR_BLACK)
            # ~ curses.init_pair(3, COLOR_GREEN, COLOR_BLACK)
        if DEBUG == True:
            print(self.stdscr)
        return self.stdscr

    def curse_windows(self):

        self.chat_h = self.max_y - 5
        self.chat_w = self.max_x - 2

        # Create Border Window
        self.gemini_border_window = self.Gemini.derwin(self.max_y, self.max_x, 0, 0)        # Chat Window (Main Display)
        self.gemini_border_window.box()
        self.gemini_border_window.refresh()

        # Create Chat Window
        self.gemini_chat_window = self.Gemini.derwin(self.chat_h, self.chat_w)
        self.gemini_chat_window.box()
        self.gemini_chat_window.scrollok(True)
        self.gemini_chat_window.refresh()

        # Create Input Window
        self.input_h = 3
        self.input_w = self.max_x - 2
        # ~ self.gemini_input_window = self.Gemini.newwin(self.input_h + 2, self.input_w + 2, 0, 0)
        self.gemini_input_window = self.Gemini.derwin(self.input_h + 2, self.input_w + 2)
        self.gemini_input_window.box()
        self.gemini_input_window.refresh()

        return

    def end_curse(self):

        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

        return

# Example usage in your main script:
if __name__ == "__main__":
    # ~ GemEnVar = GeminiEnvVar()
    #WordConData = WordContextData()
    Gemini = GeminiChat()
    # ~ print(f"This session's device UUID: {GemEnVar.device_id}")
    # ~ if DEBUG == True:
        # ~ print("DEBUG\n\nGemEnVar:\n\n", GemEnVar)

    # Now, when you store chat logs or memories in your database,
    # you can include `my_device_uuid` with each entry.
    # Example (conceptual):
    # db_connection.execute("INSERT INTO chat_log (device_id, message, timestamp) VALUES (?, ?, ?)",
    #                      (my_device_uuid, "Hello Gemini", current_timestamp))
