import sys

from django import get_version
from distutils.version import StrictVersion
DJANGO_VERSION = StrictVersion(get_version())
DJ21 = StrictVersion('2.1')
DJ20 = StrictVersion('2.0')
DJ111 = StrictVersion('1.11')
DJ110 = StrictVersion('1.10')
DJ19 = StrictVersion('1.9')
DJ18 = StrictVersion('1.8')
DJ17 = StrictVersion('1.7')
DJ16 = StrictVersion('1.6')

PY_FULL_VERSION = StrictVersion('{}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
PY_MINOR_VERSION = StrictVersion('{}.{}'.format(sys.version_info.major, sys.version_info.minor))
PY34 = StrictVersion('3.4')
PY343 = StrictVersion('3.4.3')
PY33 = StrictVersion('3.3')
PY336 = StrictVersion('3.3.6')
