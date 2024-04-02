import lxml
import json
import pytest
import re
import sys
sys.path.append('../')

from extractor.json2xml import json2xml, remove_control_characters


@pytest.fixture
def first_entry():
    return "a"

@pytest.fixture
def example_json_1():
    with open('files/ushrnp_flat.json') as f:
        return json.loads(f.read())

@pytest.fixture
def example_xml_1():
    print(str(json2xml('files/ushrnp_flat.json', output_dir='')))
    return str(json2xml('files/ushrnp_flat.json', output_dir=''))

def test_comment_structure():
    """test structure of subcomments"""
    # chronological order of subcomments
    pass

def test_subcomment_number(example_json_1, example_xml_1):
    """assure all subcomments are included in the XML file"""
    #print(first_entry)
    #print(type(example_json_1))
    assert len(example_json_1) == example_xml_1.count('<item source=')

def test_encoding():
    """make sure encoding errors are fixed"""
    body = "Hey Lena, vielen Dank f\u00fcr dein AmA!\n\n* Hast du das Gef\u00fchl, dass Deutschrap in den letzten Jahren ernsthaft politischer geworden ist oder einfach nur mehr Leute Cash mit \"politischen\" Tracks machen wollen? \n\n* Gibt es Tracks von dir, hinter denen du mittlerweile \u00fcberhaupt nicht mehr stehst, wenn ja warum? \n\n* Hast du lieber erst einen Beat, bei dem du denkst, \"krass, da k\u00f6nnte diesdas darauf passen\" oder hast du erst deine Lines beisammen, bevor du Beats pickst? \n\n* Wen w\u00fcrdest du gerne einmal featuren? Wen definitiv nicht?\n\nDanke f\u00fcr deine Musik, bleib stabil!"
    print(body)
    body_fixed = remove_control_characters(body)
    test_cases = [(body, True), (body_fixed, False)]
    for string, expected_result in test_cases:
        assert test_xml_encoding(string) == expected_result
    #assert not lxml.etree.tostring(body, pretty_print=True, encoding='utf-8')
    #assert lxml.etree.tostring(body_fixed, pretty_print=True, encoding='utf-8')

def test_xml_encoding(s):
    try:
        lxml.etree.fromstring(s.encode('utf-8'))
        return False  # No encoding error
    except UnicodeEncodeError:
        return True  # Encoding error occurred

def test_user_removal(example_xml_1):
    """test removal of /u/"""
    assert not re.findall(r'/u/(\w+)', example_xml_1)

def test_subcomment_url():
    """test subcomment url has the correct structure"""
    # f'https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}
    # constructed from permalink
    # constructed other
    pass


if __name__ == '__main__':
    test_comment_structure()
    test_subcomment_number(example_json_1, example_xml_1)
    test_encoding()
    test_user_removal(example_xml_1)
    test_subcomment_url()
