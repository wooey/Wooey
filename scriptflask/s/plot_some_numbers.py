#!/usr/bin/env python

import argparse
import time


def main():
    parser = argparse.ArgumentParser(description='Plot some numbers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                     help='a space separated list of numbers to plot')

    parser.add_argument('--random', type=int, choices=range(0, 10, 1),
                     help='a random number between these values will be added to the result')

    args = parser.parse_args()

    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    l1 = args.integers
    ax.plot(range(0, len(l1)), l1)
    print("Plotting Figure 1\n%s" % l1)
    fig.savefig('Figure 1.png')

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    l2 = [x - args.integers[n + 1] for n, x in enumerate(args.integers[:-1])]
    ax.plot(range(0, len(l2)), l2)

    print("Plotting Figure 2\n%s" % l2)
    fig.savefig('Figure 2.png')


if __name__ == '__main__':
    main()
