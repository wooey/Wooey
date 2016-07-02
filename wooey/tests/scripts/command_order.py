import argparse
import sys

parser = argparse.ArgumentParser(description="Something")
parser.add_argument('link', help='the url containing the metadata')
parser.add_argument('name', help='the name of the file')

if __name__ == '__main__':
    args = parser.parse_args()
    sys.stderr.write('{} {}'.format(args.link, args.name))
