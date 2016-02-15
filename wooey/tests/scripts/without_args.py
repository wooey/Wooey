import argparse
import sys

parser = argparse.ArgumentParser(description="Just do it without arguments!")

def main():
    for i in range(10):
        print(i)

    return 0

if __name__ == "__main__":
    parser.parse_args()
    sys.exit(main())
