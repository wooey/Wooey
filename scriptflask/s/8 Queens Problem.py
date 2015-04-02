#!/usr/bin/env python

import argparse
from matplotlib import pyplot as plt
import numpy as np
import sys

parser = argparse.ArgumentParser(description="Solve the 8 Queens problem for arbritary sized boards up to 9")

parser.add_argument("-s", "--size", dest="size", default=4, type=int, choices=range(3, 8),
                  help="size of the board")

args = parser.parse_args()

def under_attack(col, queens):
    left = right = col

    for r, c in reversed(queens):
        left, right = left - 1, right + 1

        if c in (left, col, right):
            return True
    return False

def solve(n):
    if n == 0:
        return [[]]

    smaller_solutions = solve(n - 1)

    return [solution+[(n,i+1)]
        for i in xrange(args.size)
            for solution in smaller_solutions
                if not under_attack(i+1, solution)]


fig = plt.figure()
ax = fig.add_subplot(1,1,1)
def checkerboard(s):
    r = np.ceil(float(s)/2)
    re = np.r_[ r*[0,1] ]
    ro = np.r_[ r*[1,0] ]
    board = np.row_stack(r*(re, ro))
    return board[0:s,0:s]
    
board = checkerboard(args.size)   
solutions = solve(args.size)

n_solutions = len(solutions)
print("There are %d solution(s) for a board %dx%d in size" % (n_solutions, args.size, args.size))
print("Saving images...")
for n, answer in enumerate(solutions):

    ax.cla()
    ax.matshow(board, cmap=plt.cm.gray)
    x, y = zip(*answer)
    ax.scatter(np.array(x)-1, np.array(y)-1, s=1000, marker='o', color='r')

    fig.savefig('solution-%d.png' % (n+1))

    print("Progress: %d%%" % ( 100*(n+1)/n_solutions ) )
    sys.stdout.flush()


