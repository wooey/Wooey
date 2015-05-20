import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
DJANGUI_TEMPLATE_DIR = os.path.join('djangui', 'templates')

setup(
    name='djangui',
    version='0.1.0',
    packages=find_packages(),
    data_files=[(DJANGUI_TEMPLATE_DIR, [os.path.join(root, filename) for root, folders, files in os.walk(DJANGUI_TEMPLATE_DIR)
                                        for filename in files])],
    scripts=['scripts/djanguify.py'],
    include_package_data=True,
    license='GPLv3',
    description='An app to create a Django app or project from argparse scripts',
    long_description=README,
    url='http://www.github.com/chris7/djangui',
    author='Chris Mitchell',
    author_email='chris.mit7@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv3 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)

