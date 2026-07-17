# Words_for_Hashtag.txt file content
# Linux,Java,Python
#

f1 = open('Words_for_Hashtag.txt', 'r+')
f1text = f1.read()			# Create a string you can work with more than once.
f2 = open('hashtaged.txt', 'w+')
n1 = f1text.rstrip('\n')
print("N1:", n1)
checkWords = n1.split()		# Using just .split() on it's own will automagically assume to split at spaces (" ")
print("CHECKWORDS:", checkWords)

repWords = ["#" + i for i in checkWords]
print("REPWORDS:", repWords)

print("F1TEXT:", f1text)
for line in f1text:			# Using f1text, which is still able to be read
	print("LINE:", line, sep=" ", end=" ")		#Using spaces to separate instead of the automatic "\n"
	for check, rep in zip(checkWords, repWords):
		line = line.replace(check, rep)
	f2.write(line)
f1.close()
f2.close()