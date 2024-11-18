import json
import os
import re
import tempfile

import pytest

from extractor.json2xml import json2xml

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


def get_ids(json_data):
    """Hilfsfunktion zur dynamischen Extraktion von `link_id` und `comment_id`"""
    link_id = json_data[0]["link_id"].split("_")[1]  # Entferne `t3_`-Präfix
    comment_id = json_data[0]["id"]
    return link_id, comment_id


# Fixture für den `grouped` Modus
@pytest.fixture
def grouped_example():
    """Beispiel JSON und XML für den `grouped` Modus."""
    filename = os.path.join(TEST_DIR, "files/grouped/14u42ly_flat.json")

    with open(filename, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    output_dir = tempfile.TemporaryDirectory().name
    xml_output = json2xml(filename, output_dir=output_dir, group_mode=True)

    with open(f"{output_dir}/14u42ly.xml", "r", encoding="utf-8") as xml_file:
        xml_data = xml_file.read()

    return json_data, xml_data


# Fixture für den `nogroup` Modus
@pytest.fixture
def nogroup_example():
    """Beispiel JSON und XML für den `nogroup` Modus."""
    filename = os.path.join(TEST_DIR, "files/nogroup/14t73le_jr1494w.json")

    with open(filename, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Dynamische Extraktion von link_id und comment_id
    link_id, comment_id = get_ids(json_data)

    output_dir = tempfile.TemporaryDirectory().name
    xml_output = json2xml(
        filename,
        output_dir=output_dir,
        group_mode=False,
        link_id=link_id,
        comment_id=comment_id,
    )
    with open(
        f"{output_dir}/{link_id}_{comment_id}.xml", "r", encoding="utf-8"
    ) as xml_file:
        xml_data = xml_file.read()
    return json_data, xml_data


def test_grouped_comment_structure(grouped_example):
    """Testet die chronologische Struktur der Kommentare im `grouped` Modus."""
    dates = re.findall(r"<date>\d{4}-\d{2}-\d{2}</date>", grouped_example[1])
    assert dates == sorted(dates)


def test_grouped_subcomment_number(grouped_example):
    """Stellt sicher, dass alle Subkommentare im XML im `grouped` Modus enthalten sind."""
    assert len(grouped_example[0]) == grouped_example[1].count("<item source=")


def test_grouped_subcomment_url(grouped_example):
    """Testet die URL-Struktur für Unterkommentare im `grouped` Modus."""
    urls = re.findall('<item source="(.+?)">', grouped_example[1])
    for u, comment in zip(urls, grouped_example[0]):
        subreddit = comment["subreddit"]
        post_id = comment["link_id"].replace("t3_", "")
        comment_id = comment["id"]
        expected_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}/"
        assert u == expected_url


def test_nogroup_body_structure(nogroup_example):
    """Prüft den Body-Inhalt im `nogroup` Modus (Einzelkommentar)."""
    tree = nogroup_example[1]
    assert re.search(r"<body>.*<p>.*</p>.*</body>", tree, re.DOTALL)
    assert '<div type="comments">' not in tree


def test_nogroup_subcomment_url(nogroup_example):
    """Testet die URL-Struktur für den Kommentar im `--no-group` Modus."""
    url = re.search(r'<ptr type="comment" target="(.+?)"/>', nogroup_example[1]).group(
        1
    )
    comment = nogroup_example[0][0]
    subreddit = comment["subreddit"]
    post_id = comment["link_id"].replace("t3_", "")
    comment_id = comment["id"]
    expected_url = (
        f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}/"
    )
    assert url == expected_url


def test_nogroup_author(nogroup_example):
    """Testet, dass der Autor im `nogroup` Modus korrekt im XML enthalten ist."""
    tree = nogroup_example[1]
    author = re.search(r"<author>(.*?)</author>", tree).group(1)
    assert author == nogroup_example[0][0]["author"]


def test_encoding():
    """Überprüft, dass Encoding-Fehler vermieden werden."""
    filename = os.path.join(TEST_DIR, "files/grouped/14u42ly_flat.json")
    try:
        json2xml(filename, output_dir="files/tmp_output", group_mode=True)
    except Exception as e:
        raise AssertionError(f"Fehler aufgetreten: {e}")
    else:
        assert True


def test_user_removal(grouped_example):
    """Testet die Entfernung von /u/ im `grouped` Modus."""
    assert not re.findall(r"/u/(\w+)", grouped_example[1])
