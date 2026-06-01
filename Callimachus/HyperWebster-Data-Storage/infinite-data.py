#!/usr/bin/python3

import math
import time
import sys

class HyperWebster:
    """
    Method to store data without needing a physical location behind a multilayered 256 bit 
    """
    def __init__(self):
        # The 'Alphabet' of your universe
        self.characters = """`1234567890-=\tqwertyuiop[]\\asdfghjkl;'\nzxcvbnm,./ ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?"""
        # ~ print("DEBUG", self.characters)
        self.char_list = [char for char in self.characters]
        # ~ print("DEBUG", self.char_list)
        self.N = len(self.char_list)
        # ~ print("DEBUG", self.N)
        sys.set_int_max_str_digits(0)
    def regenerate_text(self, address):
        """
        REGENERATION: Takes a large integer (the address) and 
        returns the unique string located at that coordinate.
        """
        if address < 0:
            raise ValueError("Address must be a non-negative integer.")
        
        # We start at address 0 (empty string or first char)
        # Bijective mapping: we must find which 'length' shelf the address sits on.
        res = []
        address += 1  # Shift for 1-based bijective logic
        
        while address > 0:
            address, rem = divmod(address - 1, self.N)
            res.append(self.char_list[rem])
            
        # The characters are generated in reverse order due to the math
        return "".join(reversed(res))

    def point_to_text(self, text):
        """
        INDEXING: Takes a string and returns its unique integer coordinate
        within the infinite permutation set.
        """
        text = text
        address = 0
        for i, char in enumerate(reversed(text)):
            # ~ print("DEBUG", "i = ", i, "char = ", char, "charlistindex = ", self.char_list.index(char))
            index = self.char_list.index(char) + 1
            address += index * (self.N ** i)
        
        return address - 1 # Return to 0-based coordinate space


class UniversalCoordinateSystem:
    """
    The 'Demotic' Wrapper: Handles the Flag Bits to decide 
    which logic engine to engage for a 256-bit packet.
    """
    def __init__(self, text_engine, pixel_engine=None):
        self.text_engine = text_engine
        self.pixel_engine = pixel_engine

    def decode_packet(self, packet_256bit):
        # Extract the first 8 bits as the 'Flag' (Determinative)
        # The remaining 248 bits are the 'Coordinate'
        flag = packet_256bit >> 248
        coordinate = packet_256bit & ((1 << 248) - 1)
        
        if flag == 0:
            # Standard Text Mode
            return self.text_engine.locate_text(coordinate)
        elif flag == 1:
            # Pixel Mode (Logic to be expanded manually as you build)
            return f"Bitmap Mode: Indexing {coordinate} on the XZ Plane."
        elif flag == 2:
            # Irrational/Constant Mode
            return "Irrational Mode: Constant Expansion triggered."
        else:
            return "Undefined Mode: New data space required."

# Example for your study:
# alphabet = list("abcdefghijklmnopqrstuvwxyz0123456789 ")
# engine = InfiniteHyperwebster(alphabet)
# coord = engine.get_address("cody")
# print(f"The coordinate for 'cody' is: {coord}")
# print(f"Regenerating from {coord}: {engine.locate_text(coord)}")

# TODO:SETTINGS — hardcoded path, use PTOL_ROOT
text = open(PTOL_ROOT + "/TESTdb-struct.sql").read()
text_length = len(text)
print(text_length)
HW = HyperWebster()
pointer = HW.point_to_text(text)
print("this will be a json file evetually\n", pointer, text_length, time.ctime())
