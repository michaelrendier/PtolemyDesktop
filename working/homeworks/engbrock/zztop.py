import os


class TaskList(object):
	
	def __init__(self, parent=None):
		super(TaskList, self).__init__()
		
		os.system("clear")
		self.parent = parent
		
		self.line(1)
		
	def inputer(self):
		self.a = input("Stevie what are you doing today ?  ")
		return self.a
		
	def adderloop(self):
		self.amount = 3
		self.x = 0
		self.z = []
		while self.x < self.amount:
			self.enter = self.inputer()
			self.z.append(self.enter)
			self.x += 1
		return self.z
		
	def line(self, b):
		self.todo = self.adderloop()
		for item in self.todo:
			print(item)
			
Today = TaskList()