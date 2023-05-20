import argparse
import os

parser = argparse.ArgumentParser(description="This writes a test file")
parser.add_argument(
    "--output", help="Where to write to", type=argparse.FileType("w"), required=True
)

if __name__ == "__main__":
    args = parser.parse_args()
    with args.output as o:
        o.write("TEST FILE!")
    # Create an identical file nested in a folder
    os.mkdir("test_dir")
    with open("test_dir/test_file", "w") as o:
        o.write("TEST FILE 2")
