import os

from io import StringIO

from extractor.json2xml import json2xml
from extractor.validate import validate

from .xml_conversion_tests import grouped_example, nogroup_example


TEST_DIR = os.path.abspath(os.path.dirname(__file__))


def test_validation_group(grouped_example):
    assert validate(StringIO(grouped_example[1])) is True


def test_validation_nogroup(nogroup_example):
    assert validate(StringIO(nogroup_example[1])) is True
