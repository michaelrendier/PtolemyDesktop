import random

def shortestWay(n):

    minx = 1 
    miny = 1

    maxx = 5
    maxy = 5

    x_start = 1
    y_start = 1

    X_end = 3
    Y_end = 5

    for i in range (n):

        way = random.choice(["up", "down", "left", "right"])
        print("INSIDE WAY:", way)


        if way == "up" and y_start<maxy:
                y_start +=1
                print("Y + 1")

        elif way == "down" and y_start>miny:
                y_start -=1
                print("Y - 1")

        elif way == "left" and x_start>minx:
                x_start -=1
                print("X - 1")

        elif way == "right" and x_start<maxx:
                x_start += 1
                print("X + 1")
                
    print("WAY:", way)	
    print("XSTART:", x_start, "YSTART:", y_start)

    if x_start == X_end and y_start == Y_end:

        return(x_start,y_start)

    x1 = x_start
    y1 = y_start


    return (x1, y1)

list1 = []
for i in range(25):

    way = shortestWay(10)
    print("OUTER WAY:", way)

    theShortestWay = abs(way[0]) + abs(way[1])

    list1.append(theShortestWay)

    x = min (list1)

    print(way, "distance from start: ", theShortestWay, "cells")

print ("Minimal distance: ", x)
