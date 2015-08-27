import argparse
import sys

parser = argparse.ArgumentParser(description="Something")
parser.add_argument("--output_filename", type=argparse.FileType('w'), required=True, help="Name of Excel output file.", nargs='+')
parser.add_argument("--due_date_field", type=str, help="Column name for due date field. 'Due Date' by default.")

if __name__ == '__main__':
    args = parser.parse_args()
