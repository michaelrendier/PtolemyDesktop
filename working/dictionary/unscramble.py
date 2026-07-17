import itertools as it

words = []

with open("words.txt", 'r') as file:
	words = file.read().lower().split("\n")
	file.close()
	
def unscramble(string, length):
	mycombo = list(it.permutations(string, length))
	
	mylist = []
	
	for i in mycombo:
		mylist.append("".join(i))
	
	wordlist = []
	
	for i in mylist:
		if i in words:
			wordlist.append(i)
	
	print(sorted(set(wordlist)))


	

mystr = "".join(sorted(input("Input Letters: ")))
myrep = int(input("How long is word: "))

print("Processing")

unscramble(mystr, myrep)
