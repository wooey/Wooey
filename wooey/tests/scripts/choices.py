import argparse
import sys

parser = argparse.ArgumentParser(description="Something")
parser.add_argument('--one-choice', choices=[0,1,2,3], nargs=1)
parser.add_argument('--two-choices', choices=[0,1,2,3], nargs=2)
parser.add_argument('--at-least-one-choice', choices=[0,1,2,3], nargs='+')
parser.add_argument('--all-choices', choices=[0,1,2,3], nargs='*')

if __name__ == '__main__':
    args = parser.parse_args()
