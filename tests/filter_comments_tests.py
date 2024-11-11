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
    # kleinste zst-Datei für den Test:
    comments = extract_comments('files/GermanRap_comments_small/GermanRap_comments_small.zst')
    return comments


@pytest.fixture
def example_zst_filtered():
    # Filtered zst-Datei
    filter_comments('files/GermanRap_comments_small/GermanRap_comments_small.zst',
                    authors=['AutoModerator', 'ClausKlebot', 'sneakpeekbot'],
                    remove_deleted=True,
                    remove_quotes=True,
                    remove_remindme=True,
                    remove_urls=True,
                    log_file='files/test.log')
    comments = extract_comments('files/GermanRap_comments_small/GermanRap_comments_small_filtered.zst')
    return comments


@pytest.fixture(params=["grouped", "nogroup"])
def example_json_files(request):
    """Gibt eine Liste von JSON-Dateien zurück, basierend auf dem Gruppierungsmodus."""
    mode = request.param
    dir = f'files/GermanRap_comments_small/GermanRap_comments_small.zst_json_{mode}/0001/'
    files = []
    
    # Laden der JSON-Dateien aus dem entsprechenden Verzeichnis
    for f in os.listdir(dir):
        with open(os.path.join(dir, f), 'r', encoding='utf-8') as file:
            comments = json.load(file)
            files.append(comments)
    return files


def test_url_filter():
    """Testet das Filtern von URLs."""
    assert remove_plain_urls('http://example.io') == '[URL]'
    assert remove_plain_urls('https://example.io') == '[URL]'
    assert remove_plain_urls('http://www.example.io') == '[URL]'
    assert remove_plain_urls('www.example.io') == '[URL]'
    assert remove_plain_urls('http://example.eu') == '[URL]'
    assert remove_plain_urls('text www.example.io text') == 'text [URL] text'
    assert remove_markdown_urls('[text](www.link.de)') == 'text'
    assert remove_markdown_urls('[www.example.com](www.link.de)') == '[URL]'
    assert remove_markdown_urls('[text](no url)') == '[text](no url)'


def test_botlist_removal(example_zst_filtered):
    """Testet, ob Kommentare von Bots erfolgreich entfernt wurden."""
    botlist = {'AutoModerator', 'ClausKlebot', 'sneakpeekbot'}
    authors = set(comment["author"].lower() for comment in example_zst_filtered)
    assert not botlist.intersection(authors)


def test_removed_comments(example_zst_filtered):
    """Testet, ob entfernte Kommentare ausgeschlossen wurden."""
    del_strings = ["[removed]", "[deleted]", "[removed by reddit]"]
    for comment in example_zst_filtered:
        for d in del_strings:
            assert d not in comment["body"]


def test_inline_formatting():
    """Testet, ob Inline-Formatierung entfernt wird."""
    assert remove_inline_formatting('Als ~~Zugführer~~ Lokführer muss man') == 'Als  Lokführer muss man'
    assert remove_inline_formatting('Als **Zugführer** Lokführer muss man') == 'Als Zugführer Lokführer muss man'
    assert remove_inline_formatting('Als *Zugführer* Lokführer muss man') == 'Als Zugführer Lokführer muss man'
    assert remove_inline_formatting('Als **Zugführer* Lokführer muss man') == 'Als Zugführer* Lokführer muss man'
    assert remove_inline_formatting('Als *Zugführer* **Lokführer** muss man') == 'Als Zugführer Lokführer muss man'


if __name__ == '__main__':
    pytest.main()
