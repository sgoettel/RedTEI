import os

from extractor.comment_tree import extract_comments


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_FILE = os.path.join(TEST_DIR, "files/GermanRap_comments_small/GermanRap_comments_small.zst")


def test_extraction():
    comments = list(extract_comments(TEST_FILE))
    assert len(comments) == 1028

    first = comments[0]
    assert first.get("author") == "zer0deathserryone"
    assert first.get("permalink") == "/r/GermanRap/comments/176b4p3/ich_bin_coverartdesigner_und_möchte_ihnen_einige/k4kybh8/"
    assert first.get("created_utc") == 1697128377.0
