import argparse
import sys
import os

parser = argparse.ArgumentParser(description="Just do it without arguments!")

def django_setup():
    # If you want to use your django project modules you have to append your project path

    #code:  sys.path.append('absolute/path/to/project')

    # then set your django settings

    #code:  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

    # setup django

    #code:  import django
    #code:  django.setup()
    pass

def main():
    # django_setup()
    for i in range(10):
        print i

    return 0

if __name__ == "__main__":
    sys.exit(main())
