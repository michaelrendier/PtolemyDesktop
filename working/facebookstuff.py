def insertionSort(lista):
	for i in range(1, len(lista)):
		print("I: ", i)
		currentvalue = lista[i]
		print("CURRENTVALUE: ", currentvalue)
		position = i
		print("POSITION: ", position)

		while position > 0 and lista[position - 1] > currentvalue:
			lista[position] = lista[position - 1]
			print("WHILE")
			position = position - 1

	lista[position] = currentvalue

lista = [88, 90, 5, 19, 23, 41, 2, 83, 60]
insertionSort(lista)
print(lista)
