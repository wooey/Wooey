import argparse
import os

parser = argparse.ArgumentParser(description="This is version 1")
parser.add_argument("--one")

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
