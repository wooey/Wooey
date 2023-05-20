import argparse
import os

parser = argparse.ArgumentParser(description="This is version 2")
parser.add_argument("--one")
parser.add_argument("--two")

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
