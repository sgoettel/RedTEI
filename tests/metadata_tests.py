import json
import pytest
import sys
sys.path.append('../')

from extractor.json2xml import json2xml


@pytest.fixture
def example_1():
    """example json (dict), xml (string) tuple"""
    with open('files/ushrnp_flat.json') as f:
        j = json.loads(f.read())
    x = json2xml('files/ushrnp_flat.json', output_dir='')
    return j, x


def test_url(example_1):
    """test URL"""
    pass


def test_ids():
    """test processing of link_id, parent_id etc."""
    pass


def test_header():
    """test correct header"""
    pass


if __name__ == '__main__':
    test_url()
    test_ids()
    test_header()
