import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='wooey',
    version='0.12.0',
    packages=find_packages(),
    scripts=['scripts/wooify'],
    entry_points={'console_scripts': ['wooify = wooey.backend.command_line:bootstrap', ]},
    install_requires=[
        'celery>=4.0,<5',
        'clinto>=0.3.0',
        'Django~=1.11 ;python_version<="2.7"',
        'Django>=2,<2.2 ;(python_version>"2.7" and python_version<="3.4")',
        'Django>=2,<=2.2 ;(python_version>"2.7" and python_version<="3.5")',
        'Django>=3,<4 ;python_version>="3.6"',
        'django-autoslug',
        'django-celery-results',
        'django-storages',
        'eventlet>=0.22.1 ;platform_system=="Windows"',
        'jsonfield<3',
        'pypiwin32==219 ;(platform_system=="Windows" and python_version<="3.4")',
        'pypiwin32 ;(platform_system=="Windows" and python_version>"3.4")',
        'six',
    ],
    extras_require={
        'dev': [
            'boto3',
            'coverage',
            'factory-boy',
            'mock',
            'nose',
            'sphinx',
            'tox',
        ]
    },
    include_package_data=True,
    description='A Django app which creates a web GUI and task interface for argparse scripts',
    url='http://www.github.com/wooey/wooey',
    author='Chris Mitchell <chris.mit7@gmail.com>, Martin Fitzpatrick <martin.fitzpatrick@gmail.com>',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
