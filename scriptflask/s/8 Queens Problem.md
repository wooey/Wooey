# Introduction

The eight queens puzzle is the problem of placing eight chess queens on an 8*8 chessboard
so that no two queens threaten each other. Thus, a solution requires 
that no two queens share the same row, column, or diagonal.

## Instructions

To use this script select the size of the board from the drop down on the left hand size. All possible 
positions will be output as figures.


## More info

This is a demo script to show off Wooey function. The back-end of this script is a plain-old-Python command-line script
using argparse to define arguments.

    usage: 8 Queens Problem.py [-h] [-s {3,4,5,6,7,8,9}]

    Solve the 8 Queens problem for arbritary sized boards up to 9

    optional arguments:
      -h, --help            show this help message and exit
      -s {3,4,5,6,7,8,9}, --size {3,4,5,6,7,8,9}
                            size of the board

The source code for this an all other demo scripts are [in the Wooey repo](https://github.com/mfitzp/Wooey/blob/master/scripts/8%20Queens%20Problem.py).