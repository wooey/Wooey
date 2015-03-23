#!/usr/bin/env python

import argparse
from matplotlib import pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description="Solve the 8 Queens problem for arbritary sized boards")

parser.add_argument("-s", "--size", dest="size", default=8, type=int, choices=range(3, 12),
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

for n, answer in enumerate(solve(args.size)):
    ax.cla()
    ax.matshow(board, cmap=plt.cm.gray)
    x, y = zip(*answer)
    ax.scatter(np.array(x)-1, np.array(y)-1, s=1000, marker='o', color='r')

    fig.savefig('solution-%d.png' % n)
    
