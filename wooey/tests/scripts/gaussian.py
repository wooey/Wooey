#!/usr/bin/env python
__author__ = 'chris'
import argparse
import sys
import math
from matplotlib import pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description="This will plot a gaussian distribution with the given parameters.")
parser.add_argument('--mean', help='The mean of the gaussian.', type=float, required=True)
parser.add_argument('--std', help='The standard deviation (width) of the gaussian.', type=float, required=True)


def main():
    args = parser.parse_args()
    u = args.mean
    s = abs(args.std)
    variance = s**2
    amplitude = 1/(s*math.sqrt(2*math.pi))
    fit = lambda x: [amplitude*math.exp((-1*(xi-u)**2)/(2*variance)) for xi in x]
    # plot +- 4 standard deviations
    X = np.linspace(u-4*s, u+4*s, 100)
    Y = fit(X)
    plt.plot(X, Y)
    plt.title('Gaussian distribution with mu={0:.2f}, sigma={1:.2f}'.format(u, s))
    plt.savefig('gaussian.png')

if __name__ == "__main__":
    sys.exit(main())
