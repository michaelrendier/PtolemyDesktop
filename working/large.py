from memory_profiler import profile

@profile
def large_function():
    return sum(2**i for i in range(1000000))


large_function()
