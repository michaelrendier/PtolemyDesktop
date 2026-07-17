#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import numpy as np
import fractions as fr
import sympy as sp


a = np.array([[1, 2], [3, 4]])
a2 = np.array([[3, 2, 0, 1], [4, 0, 1, 2], [3, 0, 2, 1], [9, 2, 3, 1]])
a3 = np.array([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20], [21, 22, 23, 24, 25]])
b = sp.Matrix([[fr.Fraction(3), fr.Fraction(2), fr.Fraction(0), fr.Fraction(1)],
               [fr.Fraction(4), fr.Fraction(0), fr.Fraction(1), fr.Fraction(2)],
               [fr.Fraction(3), fr.Fraction(0), fr.Fraction(2), fr.Fraction(1)],
               [fr.Fraction(9), fr.Fraction(2), fr.Fraction(3), fr.Fraction(1)]])
b2 = np.array([[fr.Fraction(3), fr.Fraction(2), fr.Fraction(0), fr.Fraction(1)],
               [fr.Fraction(4), fr.Fraction(0), fr.Fraction(1), fr.Fraction(2)],
               [fr.Fraction(3), fr.Fraction(0), fr.Fraction(2), fr.Fraction(1)],
               [fr.Fraction(9), fr.Fraction(2), fr.Fraction(3), fr.Fraction(1)]], dtype=fr.Fraction)

class Matrix(sp.Matrix):
    """
    Totally the pits.
    """
    def __init__(self, array):
        sp.Matrix().__init__(array)
        self.array = np.array(array, dtype=fr.Fraction)
        # self.array = array
        for i in range(self.array.shape[0]):
            for j in range(self.array.shape[1]):
                self.array[i][j] = fr.Fraction(self.array[i][j])
        self.example = """\n\nRemember:\n columd and rows\n start at 0.\n\n    0 1 2 3\n0 [ a b c d ]\n1 [ e f g h ]\n2 [ i j k l ]\n3 [ m n o p ]"""
        print(dir(self))

    # def __truediv__(self, divisor):
    #     return self.__itruediv__(divisor)

    # def __doc__(self):
    #     print("HALLEUEA")
    #     return "OMGONWGONETSKJHGOWEG"

    def __str__(self):
        return str(self.array)

    def __repr__(self):
        return f"{self.__class__.__name__}(array={self.array.tolist()})"

    def __array_finalize__(self, obj):
        return f"Matrix initialized,\n{self}\n{obj}"

    def divide(self, divisor, row=None, col=None):
        if row and col:
            return self.array[row][col] / divisor
        elif row:
            return self.array[row] / divisor
        else:
            return self.array / divisor

    def col_shift(self, array, num_shift=1):
        """Shift all columns of array to the left num_shift times."""
        y, x = array.shape
        arrayList = array.tolist()

        if 0 < num_shift <= x:
            for shift in range(num_shift):
                for i in arrayList:
                    i.append(i.pop(0))
        else:
            raise IndexError(f"Array has less than {num_shift} columns...")
        array = np.array(arrayList)

        return array

    def row_shift(self, array, num_shift=1):
        """Shift all rows of array up num_shift times."""
        y, x = array.shape
        arrayList = array.tolist()

        if 0 < num_shift <= y:
            for shift in range(num_shift):
                arrayList.append(arrayList.pop(0))
        else:
            raise IndexError(f"Array has less than {num_shift} rows...")
        array = np.array(arrayList)

        return array

    def ero_replace(self, array, row1, row2, multiple):
        """From array, add to row1, a multiple of row2."""
        y, x = array.shape

        if 0 <= row1 < y and 0 <= row2 < y:
            array[row1] += (multiple * array[row2])

        else:
            raise IndexError("Row index out of range of array shape...")

        return array

    def ero_interchange(self, row1, row2):
        """Swap row1 and row2 in array."""
        print(f"***{self/25})")
        #         print(array)
        print("CLS\n", self.array)
        y, x = self.array.shape
        if 0 <= row1 < y and 0 <= row2 < y:
            changeRow = np.array(self.array[row1])
            self.array[row1] = self.array[row2]
            self.array[row2] = changeRow

        else:
            raise IndexError(f"Array has less than {y} rows...")

        return self.array

    def ero_scaling(self, array, row, multiple):
        """Multiply row with multiple in array."""
        y, x = array.shape
        if 0 <= row < y:
            array[row] = array[row] * multiple

        else:
            raise IndexError(f"Array has less than {y} rows...")

        return array

    # def __array_finalize__(self, obj):
    #     return f"Matrix initialized,\n{self}\n{obj}"

firstMatrix = Matrix([[3, 2, 0, 1], [4, 0, 1, 2], [3, 0, 2, 1], [9, 2, 3, 1]])
print(firstMatrix.__doc__, '\n', type(firstMatrix))
# print("THISONE:\n", firstMatrix.__truediv__(23))
# print("These too\n", firstMatrix[0])
# print("****---->>\n", str(firstMatrix.ero_interchange(1, 3)))
# print(dir(firstMatrix))
# print(firstMatrix.ero_interchange.__doc__)
# print(help(firstMatrix.ero_interchange))
# print("March march march march...\n", (firstMatrix.divide(23)))
# print("SJHDF", firstMatrix.__itruediv__(23))
print("TRUE", firstMatrix.divide(23))
print("Final:\n", firstMatrix)


