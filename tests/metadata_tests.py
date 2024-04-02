import sys
sys.path.append('../')

from extractor.json2xml import json2xml
import pytest


@pytest.fixture
def example_data_1():
    return json2xml('files/')

def test_url():
    """test URL"""
    pass

def test_ids():
    """test processing of link_id, parent_id etc."""
    pass


if __name__ == '__main__':
    test_url()
    test_ids()
