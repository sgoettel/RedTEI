import json
import os
import pytest
import sys
sys.path.append('../')

from extractor.comment_tree import extract_comments
from extractor.trim_username_comments import (filter_comments,
                                              remove_plain_urls,
                                              remove_markdown_urls,
                                              remove_inline_formatting)


@pytest.fixture
def example_zst():
    # smallest zst file:
    # GermanRap_comments_small/GermanRap_comments_small.zst
    comments = extract_comments('files/GermanRap_comments_small/GermanRap_comments_small.zst')
    return comments


@pytest.fixture
def example_zst_filtered():
    # smallest zst file:
    # GermanRap_comments_small/GermanRap_comments_small.zst
    filter_comments('files/GermanRap_comments_small/GermanRap_comments_small.zst',
                    authors=['AutoModerator', 'ClausKlebot', 'sneakpeekbot'],
                    remove_deleted=True,
                    remove_quotes=True,
                    remove_remindme=True,
                    remove_urls=True,
                    log_file='files/test.log')
    comments = extract_comments('files/GermanRap_comments_small/GermanRap_comments_small_filtered.zst')
    return comments


@pytest.fixture
def example_json_files():
    """returns a list of json files/dictionaries"""
    dir = 'files/GermanRap_comments_small/GermanRap_comments_small_json/'
    # example list of extracted json files
    files = list()
    for f in os.listdir(dir):
        with open(dir+f, 'r', encoding='latin-1') as f:
            txt = f.read()
        comments = json.loads(txt)
        files.append(comments)
    return files


def test_url_filter():
    """test URL"""
    # remove plain urls
    assert remove_plain_urls('http://example.io') == '[URL]'
    assert remove_plain_urls('https://example.io') == '[URL]'
    # w/ www
    assert remove_plain_urls('http://www.example.io') == '[URL]'
    # wo/ http
    assert remove_plain_urls('www.example.io') == '[URL]'
    # different domain
    assert remove_plain_urls('http://example.eu') == '[URL]'
    # text before and after
    assert remove_plain_urls('text www.example.io text') == 'text [URL] text'
    # remove markdown urls
    assert remove_markdown_urls('[text](www.link.de)') == 'text'
    # text and link are urls
    assert remove_markdown_urls('[www.example.com](www.link.de)') == '[URL]'
    # no url
    assert remove_markdown_urls('[text](no url)') == '[text](no url)'


def test_botlist_removal(example_zst_filtered):
    """test comments from bots have been successfully removed"""
    botlist = {'AutoModerator', 'ClausKlebot', 'sneakpeekbot'}
    # TODO FIX
    authors = set(comment["author"] for comment in example_zst_filtered)
    # check empty set intersection of bots and authors
    assert not botlist.intersection(authors)


def test_removed_comments(example_zst_filtered):
    """test removed comments are excluded"""
    del_strings = ["[removed]", "[deleted]", "[removed by reddit]"]
    for comment in example_zst_filtered:
        for d in del_strings:
            assert not d in comment["body"]
            # in case we implement removal of deleted authors' comments:
            # assert not d in comment["author"]


def test_inline_formatting():
    """test inline formatting (bold, italic, strikethrough) is removed"""
    # remove_inline_formatting
    # strikethrough
    assert remove_inline_formatting('Als ~~Zugführer~~ Lokführer muss man') \
        == 'Als  Lokführer muss man'
    # bold
    assert remove_inline_formatting('Als **Zugführer** Lokführer muss man') \
        == 'Als Zugführer Lokführer muss man'
    # italic
    assert remove_inline_formatting('Als *Zugführer* Lokführer muss man') \
        == 'Als Zugführer Lokführer muss man'
    # mismatch of asterisks
    assert remove_inline_formatting('Als **Zugführer* Lokführer muss man') \
        == 'Als Zugführer* Lokführer muss man'
    # bold and italic in one sentence
    assert remove_inline_formatting('Als *Zugführer* **Lokführer** muss man') \
        == 'Als Zugführer Lokführer muss man'


if __name__ == '__main__':
    test_url_filter()
    test_botlist_removal()
    test_removed_comments()
    test_inline_formatting()
