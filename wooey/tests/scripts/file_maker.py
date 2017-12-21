import argparse

parser = argparse.ArgumentParser(description="This writes a test file")

if __name__ == '__main__':
    args = parser.parse_args()
    with open('test_file', 'wb') as o:
        o.write('TEST FILE!')
