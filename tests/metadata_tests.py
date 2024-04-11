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
    x = json2xml('files/ushrnp_flat.json', output_dir='').decode('utf-8')
    return j, x


def test_url(example_1):
    """test URL"""
    tree = example_1[1]
    url = re.findall(r'<ptr type="URL" target="(.*?)"/>', tree)[0]
    assert url == "https://www.reddit.com/r/GermanRap/comments/ushrnp/"


def test_dates(example_1):
    tree = example_1[1]
    # creation date
    c_date = re.findall(r"<date>(.*?)</date>", tree)[0]
    assert c_date == "2022-05-18"
    # download date
    d_date = re.findall(r'<date type="download">(.*?)</date>', tree)[0]
    assert d_date == "2022-06-17"
    # assert download date after creation date
    assert c_date < d_date


def test_header(example_1):
    """test correct header"""
    tree = example_1[1]
    header_gold = """
    <fileDesc>
      <titleStmt>
        <title type="main">ask_me_anything_hey_ich_bin_lena_stoehrfaktor</title>
      </titleStmt>
      <publicationStmt>
        <p/>
      </publicationStmt>
      <sourceDesc>
        <bibl/>
        <biblFull>
          <titleStmt>
            <title type="main">Reddit/GermanRap</title>
          </titleStmt>
          <publicationStmt>
            <publisher/>
            <ptr type="URL" target="https://www.reddit.com/r/GermanRap/comments/ushrnp/"/>
            <date>2022-05-18</date>
          </publicationStmt>
        </biblFull>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <creation>
        <date type="download">2022-06-17</date>
      </creation>
    </profileDesc>
    """
    header = re.findall(r'<teiHeader>(.*?)</teiHeader>', tree, re.DOTALL)[0]
    # ignore whitespaces
    assert re.sub(r'\s+', '', header) == re.sub(r'\s+', '', header_gold)


if __name__ == '__main__':
    test_url()
    test_dates()
    test_header()
