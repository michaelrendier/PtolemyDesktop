#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

seen = set()

edges = []

def dfs(node, k, A):
    # print("Node:", node, "k:", k, "A:", A)
    for i in range(k):
        # print("A[i]:", A[i])
        string = node + A[i]
        # print("STRING:", string)
        if string not in seen:
            seen.add(string)
            # print("SEEN:", seen)
            # print("string[1:]")
            dfs(string[1:], k, A)
            edges.append(i)
            # print("EDGES:", edges)


def deBruijn(n, k, A):

    seen.clear()
    edges.clear()

    startingNode = (n - 1) * A[0]
    # print("startingNode:", startingNode)
    dfs(startingNode, k, A)

    S = ""

    l = pow(k, n)
    # print("l:", l)
    for i in range(l):
        S += A[edges[i]]
    S += startingNode

    return S

def main():

    n = 3
    k = 3
    A = "012"

    print(deBruijn(n, k, A))

if __name__ == "__main__":
    main()



