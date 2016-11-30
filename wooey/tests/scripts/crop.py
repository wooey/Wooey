#!/usr/bin/env python

__author__ = 'chris'
import argparse
import sys
from PIL import Image

parser = argparse.ArgumentParser(description="Crop images")
parser.add_argument('--image', help='The image to crop', type=argparse.FileType('r'), required=True)
parser.add_argument('--left', help='The number of pixels to crop from the left', type=int, default=0)
parser.add_argument('--right', help='The number of pixels to crop from the right', type=int, default=0)
parser.add_argument('--top', help='The number of pixels to crop from the top', type=int, default=0)
parser.add_argument('--bottom', help='The number of pixels to crop from the bottom', type=int, default=0)
parser.add_argument('--save', help='Where to save the new image', type=argparse.FileType('w'), required=True)


def main():
    args = parser.parse_args()
    im = Image.open(args.image.name)
    width, height = im.size
    right = width-args.right
    bottom = height-args.bottom
    new = im.crop((args.left, args.top, right, bottom))
    new.save(args.save.name)

if __name__ == "__main__":
    sys.exit(main())
