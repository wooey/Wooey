import argparse
import sys

parser = argparse.ArgumentParser(description="Something")
parser.add_argument('--one-choice-added', choices=[0, 1, 2, 3], nargs=1)
parser.add_argument('--two-choices', choices=[0, 1, 2, 3], nargs=2)
parser.add_argument('--at-least-one-choice', choices=[0, 1, 2, 3], nargs='+')
parser.add_argument('--all-choices', choices=[0, 1, 2, 3], nargs='*')
parser.add_argument('--need-at-least-one-numbers', type=int, nargs='+', required=True, action='append')
parser.add_argument('--choices-str', nargs='+', type=str)
parser.add_argument('--multiple-file-choices', type=argparse.FileType('r'), nargs='*')
parser.add_argument('--more-multiple-file-choices', type=argparse.FileType('r'), nargs='*')

if __name__ == '__main__':
    args = parser.parse_args()
    sys.stdout.write('{}'.format(args))
