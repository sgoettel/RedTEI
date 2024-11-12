import json
import pytest
import re
import sys
from lxml import etree
sys.path.append('../')

from extractor.json2xml import json2xml

def parse_xml_structure(xml_string):
    """Hilfsfunktion zur Normalisierung der XML-Struktur, um Whitespaces zu ignorieren."""
    wrapped_string = f"<root>{xml_string}</root>"
    root = etree.fromstring(wrapped_string)
    # Entferne den Wrapper-Tag und canonicalisiere den XML-Inhalt für konsistenten Vergleich
    return etree.tostring(root[0], method="c14n")  # Canonical XML

@pytest.fixture
def grouped_example():
    """Dynamisches Beispiel JSON und XML für den `grouped` Modus."""
    with open('files/grouped/14u42ly_flat.json') as f:
        json_data = json.load(f)

    # json2xml mit dynamischem Dateinamen
    output_dir = 'files/tmp_output'
    xml_output = json2xml('files/grouped/14u42ly_flat.json', output_dir=output_dir, group_mode=True)
    with open(f"{output_dir}/14u42ly.xml", 'r') as xml_file:
        xml_data = xml_file.read()
    return json_data, xml_data

@pytest.fixture
def nogroup_example():
    """Dynamisches Beispiel JSON und XML für den `nogroup` Modus."""
    with open('files/nogroup/14t73le_jr1494w.json') as f:
        json_data = json.load(f)
        
    # Dynamisch link_id und comment_id ermitteln
    link_id = json_data[0]["link_id"].split("_")[1]
    comment_id = json_data[0]["id"]

    # json2xml mit dynamischem Dateinamen im `--no-group` Modus
    output_dir = 'files/tmp_output'
    xml_output = json2xml(
        'files/nogroup/14t73le_jr1494w.json', 
        output_dir=output_dir, 
        group_mode=False, 
        link_id=link_id, 
        comment_id=comment_id
    )
    with open(f"{output_dir}/{link_id}_{comment_id}.xml", 'r') as xml_file:
        xml_data = xml_file.read()
    return json_data, xml_data

def test_grouped_header_structure(grouped_example):
    """Testet den Header für den `grouped` Modus strukturell."""
    json_data, xml_data = grouped_example
    header_gold = """
    <fileDesc>
      <titleStmt>
        <title type="main">pashanim_sommergewitter_heat_waves_remix</title>
      </titleStmt>
      <publicationStmt>
        <p/>
      </publicationStmt>
      <sourceDesc>
        <bibl>Reddit/GermanRap: pashanim_sommergewitter_heat_waves_remix, 2023-07-08</bibl>
        <biblFull>
          <titleStmt>
            <title type="main">Reddit/GermanRap</title>
          </titleStmt>
          <publicationStmt>
            <publisher/>
            <ptr type="URL" target="https://www.reddit.com/r/GermanRap/comments/14u42ly/"/>
            <date type="last_comment">2023-07-08</date>
          </publicationStmt>
        </biblFull>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <creation>
        <date type="download">2023-07-08</date>
      </creation>
    </profileDesc>
    """
    # Verwende den gesamten <teiHeader>-Tag
    header = re.search(r'<teiHeader>(.*?)</teiHeader>', xml_data, re.DOTALL).group(1)
    assert parse_xml_structure(header) == parse_xml_structure(header_gold)



def test_nogroup_header_structure(nogroup_example):
    """Testet den Header für den `nogroup` Modus strukturell."""
    json_data, xml_data = nogroup_example
    header_gold = """
    <fileDesc>
      <titleStmt>
        <title type="main">jindo109_vs_liuz_proving_grounds_berlin_dltlly</title>
      </titleStmt>
      <publicationStmt>
        <p/>
      </publicationStmt>
      <sourceDesc>
        <bibl>Reddit/GermanRap: jindo109_vs_liuz_proving_grounds_berlin_dltlly, 2023-07-07</bibl>
        <biblFull>
          <titleStmt>
            <title type="main" level="a">jindo109_vs_liuz_proving_grounds_berlin_dltlly</title>
            <author>muelletob</author>
          </titleStmt>
          <publicationStmt>
            <publisher/>
            <ptr type="thread" target="https://www.reddit.com/r/GermanRap/comments/14t73le/"/>
            <ptr type="comment" target="https://www.reddit.com/r/GermanRap/comments/14t73le/comment/jr1494w/"/>
            <date>2023-07-07</date>
          </publicationStmt>
          <seriesStmt>
            <title type="main" level="m">Reddit</title>
            <title type="sub" level="m">GermanRap</title>
          </seriesStmt>
        </biblFull>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <creation>
        <date type="download">2023-07-07</date>
      </creation>
    </profileDesc>
    """
    # Verwende den gesamten <teiHeader>-Tag
    header = re.search(r'<teiHeader>(.*?)</teiHeader>', xml_data, re.DOTALL).group(1)
    assert parse_xml_structure(header) == parse_xml_structure(header_gold)



