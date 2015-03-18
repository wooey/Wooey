from setuptools import setup, find_packages

with open('README.md') as readme:
    long_description = readme.read()

version = __import__('wooey').__version__

setup(
    name='Wooey',
    version=version,
    url='http://github.com/mfitzp/Wooey',
    author='Martin Fitzpatrick',
    author_email='martin.fitzpatrick@gmail.com',
    description='Simple Web UIs for Python Scripts',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Desktop Environment',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Widget Sets',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4'
    ],
    long_description=long_description,
)
