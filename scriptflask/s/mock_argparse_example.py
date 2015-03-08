#!/usr/bin/env python

import argparse


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                     help='an integer for the accumulator')

    parser.add_argument('--sum', dest='accumulate', action='store_const',
                     const=sum, default=max,
                     help='sum the integers (default: find the max)')

    parser.add_argument('--womp', dest='womp', action='store',
                     type=int, default=0,
                     help='subtract value')

    args = parser.parse_args()
    print(args.accumulate(args.integers) - args.womp)


if __name__ == '__main__':
    main()
