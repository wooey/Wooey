import argparse
import sys

import pandas as pd

parser = argparse.ArgumentParser(description="Something")


def main():
    df = pd.DataFrame()
    print(df)


if __name__ == "__main__":
    args = parser.parse_args()
    sys.stdout.write("{}".format(args))
    sys.exit(main())
