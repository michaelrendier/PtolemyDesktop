from turtle import Turtle
import random

t = Turtle()
t.screen.bgcolor("black")
t.speed(0)


def random_drawing(turns, distance):
	for x in range(turns):
		right = t.right(random.randint(0, 360))
		left = t.left(random.randint(0, 360))
		t.color(random.choice(["blue", "red", "green"]))
		random.choice([right, left])
		t.fd(distance)


random_drawing(100, 50)
input("Press Enter to Close")

