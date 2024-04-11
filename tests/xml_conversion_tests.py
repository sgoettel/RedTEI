import json
import pytest
import re
import sys
sys.path.append('../')

from extractor.json2xml import json2xml


@pytest.fixture
def example_1():
    """example json (dict), xml (string) tuple"""
    with open('files/ushrnp_flat.json') as f:
        j = json.loads(f.read())
    x = str(json2xml('files/ushrnp_flat.json', output_dir=''))
    return j, x


@pytest.fixture
def example_2():
    """example json (dict), xml (string) tuple"""
    with open('files/5wa69r_flat.json') as f:
        j = json.loads(f.read())
    x = str(json2xml('files/5wa69r_flat.json', output_dir=''))
    return j, x


def test_comment_structure(example_1):
    """test chronological structure of subcomments"""
    # <date>yyyy-mm-dd</date>
    dates = re.findall(r'<date>\d\d\d\d-\d\d-\d\d</date>', example_1[1])
    # chronological order of subcomments
    assert dates == sorted(dates)


def test_subcomment_number(example_1):
    """assure all subcomments are included in the XML file"""
    assert len(example_1[0]) == example_1[1].count('<item source=')


def test_encoding(example_1):
    """make sure encoding errors are fixed"""
    # assert correct file conversion of a file that used to throw errors
    # TODO find a nicer way to test this
    try:
        json2xml("files/lmjo20_flat.json", output_dir='')
    except Exception as e:
        raise AssertionError(f"Error occurred: {e}")
    else:  # Assertion passes if the function call does not raise an error
        assert True


def test_user_removal(example_1):
    """test removal of /u/"""
    assert not re.findall(r'/u/(\w+)', example_1[1])


def test_subcomment_url_from_permalink(example_1):
    """test subcomment url has the correct structure"""
    # f'https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}
    urls = re.findall('<item source=".+">', example_1[1])
    for u, comment in zip(urls, example_1[0]):
        u_link = u.split('"')[1].replace('https://www.reddit.com', '')
        # constructed from permalink
        assert u_link == comment['permalink']


def test_subcomment_url_other(example_2):
    """test subcomment url has the correct structure"""
    # f'https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}
    urls = re.findall('<item source=".+">', example_2[1])
    for u, comment in zip(urls, example_2[0]):
        u_link = u.split('"')[1]
        # constructed other
        subreddit = comment['subreddit']
        post_id = comment["link_id"].replace('t3_', '')
        comment_id = comment['id']
        comment_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}"
        assert u_link == comment_url


if __name__ == '__main__':
    test_comment_structure()
    test_subcomment_number(example_1)
    test_encoding()
    test_user_removal(example_1)
    test_subcomment_url_from_permalink()
    test_subcomment_url_other()
