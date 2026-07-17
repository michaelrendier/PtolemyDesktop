import math
import multiprocessing
import random
import sys
import time
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

__doc__ = """
		This script can only be used on text files
		with the data arranged as a string of numbers.
		The text must be able to pass through the .split()
		function, which splits at whitespaces
		(' ', '\t', '\n') etc. after being read into a string.
		"""


def merge(*args):
	# Support explicit left/right args, as well as a two-item
	# tuple which works more cleanly with multiprocessing.
	left, right = args[0] if len(args) == 1 else args
	left_length, right_length = len(left), len(right)
	left_index, right_index = 0, 0
	merged = []
	while left_index < left_length and right_index < right_length:
		if left[left_index] <= right[right_index]:
			merged.append(left[left_index])
			left_index += 1
		else:
			merged.append(right[right_index])
			right_index += 1
	if left_index == left_length:
		merged.extend(right[right_index:])
	else:
		merged.extend(left[left_index:])
	return merged


def merge_sort(data):
	length = len(data)
	if length <= 1:
		return data
	
	# middle = length / 2
	middle = length // 2  # floor division returns an integer instead of a float
	
	left = merge_sort(data[:middle])
	right = merge_sort(data[middle:])
	return merge(left, right)


def merge_sort_parallel(data):
	# Creates a pool of worker processes, one per CPU core.
	# We then split the initial data into partitions, sized
	# equally per worker, and perform a regular merge sort
	# across each partition.
	processes = multiprocessing.cpu_count()
	pool = multiprocessing.Pool(processes=8)
	size = int(math.ceil(float(len(data)) / processes))
	data = [data[i * size:(i + 1) * size] for i in range(processes)]
	data = pool.map(merge_sort, data)
	# Each partition is now sorted - we now just merge pairs of these
	# together using the worker pool, until the partitions are reduced
	# down to a single sorted result.
	while len(data) > 1:
		# If the number of partitions remaining is odd, we pop off the
		# last one and append it back after one iteration of this loop,
		# since we're only interested in pairs of partitions to merge.
		extra = data.pop() if len(data) % 2 == 1 else None
		data = [(data[i], data[i + 1]) for i in range(0, len(data), 2)]
		data = pool.map(merge, data) + ([extra] if extra else [])
	return data[0]


# if _name_ == "_main_":
if __name__ == "__main__":  # needed two underscores for these variables
	print("THESE:", sys.argv)
	if sys.argv[1] == "-u":
		print("OPENING URL")
		data_unsorted = None
		html = ""
		try:
			url = sys.argv[2]
			response = urlopen(url)
			html = response.read()
			data_unsorted = [int(i) for i in html.split()]
		
		except HTTPError as e:
			print(f"The URL you requested can not be found. {e.args}")
			print(f"Please check your URL and try again! ({e.errno})")
		
		except URLError as e:
			print(f"There was no internet found.")
			print(f"Please check your connnection and\n"
			      f"try running script again!\n{e.reason}")
	
	else:
		print("USING RANDOM SIZE 1000")
		size = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 1000
		data_unsorted = [random.randint(0, size) for _ in range(size)]
	
	if data_unsorted == None:
		print("Your Data could not be retrieved from the URL")
		pass
	
	else:
		filename = str(url.split("/")[-1]) + ".sorted"   # retrieve name of url file
		file = open(filename, 'w+')                     # moved from below
		file.write(f"DATA UNSORTED:\n{data_unsorted}\n")
		file.close()
		
		print("DATA UNSORTED", data_unsorted, "\n")
		
		# for sort in merge_sort, merge_sort_parallel:
		for sort in merge_sort(data_unsorted), merge_sort_parallel(
				data_unsorted):  # you have to give the data to the functions
			
			start = time.time()
		data_sorted = sort
		end = time.time() - start
		
		# print sort, end, sorted(data_unsorted) == data_sorted
		print(set(sort), end, set(sorted(data_unsorted)) == set(data_sorted), "\n")  # needed parenthesis
		file = open(filename, 'a')
		# I used set() to remove repeats ie: set(sort)
		file.write(f"DATA SORTED:\n{set(sort)},\ntime={end} s,\nequal to sorted() function={set(sorted(data_unsorted)) == set(data_sorted)}\n")  # moved from below.
		file.close()