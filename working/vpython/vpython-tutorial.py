GlowScript 2.1 VPython
from vpython import *

ball = sphere(pos=vector(0, 0, 0), radius=0.5, color=color.cyan, make_trail=True)
wallR = box(pos=vector(6, 0, 0), size=vector(0.2, 12, 12), color=color.green)
wallL = box(pos=vector(-6, 0, 0), size=vector(0.2, 12, 12), color=color.green)
wallT = box(pos=vector(0, 6, 0), size=vector(12, 0.2, 12), color=color.blue)
wallB = box(pos=vector(0, -6, 0), size=vector(12, 0.2, 12), color=color.blue)
wallNF = box(pos=vector(0, 0, -6), size=vector(12, 12, 0.2), color=color.red)

TheBox = compound([wallR, wallL, wallT, wallB, wallNF])

ball.velocity = vector(23, 5, 32)

vscale = 0.1
varr = arrow(pos=ball.pos, axis=vscale * ball.velocity, color=color.yellow)

deltat = 0.005
t = 0
ball.pos = ball.pos + ball.velocity * deltat

scene.autoscale = False

while True:
	rate(200)
	
	# TheBox.rotate(angle=(6.28/10), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
	
	if ball.pos.x + 0.5 > wallR.pos.x + 0.1:
		ball.velocity.x = -ball.velocity.x
	if ball.pos.x - 0.5 < wallL.pos.x + 0.1:
		ball.velocity.x = -ball.velocity.x
	if ball.pos.y + 0.5 > wallT.pos.y + 0.1:
		ball.velocity.y = -ball.velocity.y
	if ball.pos.y - 0.5 < wallB.pos.y + 0.1:
		ball.velocity.y = -ball.velocity.y
	if ball.pos.z + 0.5 < 6.1:
		ball.velocity.z = -ball.velocity.z
	if ball.pos.z - 0.5 > wallNF.pos.z + 0.1:
		ball.velocity.z = -ball.velocity.z
	varr.axis = vscale * ball.velocity
	ball.pos = ball.pos + ball.velocity * deltat
	varr.pos = ball.pos + ball.velocity * deltat
	t = t + deltat