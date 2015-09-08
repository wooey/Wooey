import argparse
import sys
from numpy import mgrid, linspace, zeros, copy, multiply, add
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser(description="Something")
parser.add_argument('height', help='The height of the image.', type=int, default=400)
parser.add_argument('width', help='the width of the image.', type=int, default=400)
parser.add_argument('xmin', help='The minimum region to compute.', type=float, default=-2)
parser.add_argument('xmax', help='The maximum region to compute.', type=float, default=0.5)
parser.add_argument('ymin', help='The minimum region to compute.', type=float, default=-1.25)
parser.add_argument('ymax', help='The maximum region to compute.', type=float, default=1.25)


def mandel(n, m, itermax, xmin, xmax, ymin, ymax):
    # from https://thesamovar.wordpress.com/2009/03/22/fast-fractals-with-python-and-numpy/
    ix, iy = mgrid[0:n, 0:m]
    x = linspace(xmin, xmax, n)[ix]
    y = linspace(ymin, ymax, m)[iy]
    c = x+complex(0, 1)*y
    del x, y
    img = zeros(c.shape, dtype=int)
    ix.shape = n*m
    iy.shape = n*m
    c.shape = n*m
    z = copy(c)
    for i in xrange(itermax):
        if not len(z):
            break
        multiply(z, z, z)
        add(z, c, z)
        rem = abs(z)>2.0
        img[ix[rem], iy[rem]] = i+1
        rem = -rem
        z = z[rem]
        ix, iy = ix[rem], iy[rem]
        c = c[rem]

    plt.imshow(img)
    plt.savefig('fractal.png')


def limit(value, min, max, default):
    if value < min or value > max:
        return default
    return value

if __name__ == '__main__':
    args = parser.parse_args()
    height = limit(args.height, 1, 2000, 400)
    width = limit(args.width, 1, 2000, 400)
    mandel(args.height, args.width, 100, args.xmin, args.xmax, args.ymin, args.ymax)
