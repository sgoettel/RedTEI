import sys
sys.path.append('../')

from extractor.comment_tree import extract_comments
from extractor.trim_username_comments import filter_comments
import pytest


@pytest.fixture
def example_data_1():
    # smallest zst file:
    # GermanRap_comments_small/GermanRap_comments_small.zst
    return json2xml('files/GermanRap_comments_small/GermanRap_comments_small.zst')

def test_url_filter():
    """test URL"""
    # test url filter 5wa69r_flat
    pass

def test_botlist_removal():
    """test comments from bots have been successfully removed"""
    pass

def test_removed_comments():
    """test comments with body = 'removed' are excluded"""
    pass

def test_inline_formatting():
    """test inline formatting (bold, italic, strikethrough) is removed"""
    pass


if __name__ == '__main__':
    test_url_filter()
