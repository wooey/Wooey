import sys

from django import get_version
from packaging.version import parse as parse_version

DJANGO_VERSION = parse_version(get_version())
DJ21 = parse_version("2.1")
DJ20 = parse_version("2.0")
DJ111 = parse_version("1.11")
DJ110 = parse_version("1.10")
DJ19 = parse_version("1.9")
DJ18 = parse_version("1.8")
DJ17 = parse_version("1.7")
DJ16 = parse_version("1.6")

PY_FULL_VERSION = parse_version(
    "{}.{}.{}".format(
        sys.version_info.major, sys.version_info.minor, sys.version_info.micro
    )
)
PY_MINOR_VERSION = parse_version(
    "{}.{}".format(sys.version_info.major, sys.version_info.minor)
)
PY34 = parse_version("3.4")
PY343 = parse_version("3.4.3")
PY33 = parse_version("3.3")
PY336 = parse_version("3.3.6")
