import argparse
import os

parser = argparse.ArgumentParser(description="This writes a test file")

if __name__ == '__main__':
    args = parser.parse_args()
    with open('test_file', 'w') as o:
        o.write('TEST FILE!')
    # Create an identical file nested in a folder
    os.mkdir('test_dir')
    with open('test_dir/test_file', 'w') as o:
        o.write('TEST FILE 2')
