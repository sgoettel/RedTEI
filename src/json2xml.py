"""
Transform Reddit files in json format to TEI-XML

Author: Lydia Körber, 2023
"""

from datetime import datetime
import json
import html
import os

from lxml import etree
from lxml.etree import (
    Element,
    ElementTree,
    SubElement,
    tostring
)


blacklist_authors = []


def build_subcomments(supercomment_element, subcomment, tree_structure=False, filtered=True):
    """
    Build TEI XML subcomments within a parent comment element.

    Args:
        supercomment_element (Element): The parent comment element to which
            subcomments will be added.
        subcomment (dict): The subcomment data in a dictionary format.
        filtered (bool, optional): Whether deleted comments and authors are
            already removed. Defaults to True.

    Description:
        This function appends subcomments to a specified parent comment element
        in TEI XML format.
        Each subcomment is represented as a <p> element with attributes for
        'id' and 'author'.
        Additionally, line breaks within subcomment text are transformed into
        <lb> elements.

    """
    if not subcomment['author'] in blacklist_authors:
        comment = SubElement(supercomment_element, 'item',
                             id=subcomment['id'])
        # transform 'id' to 'xml:id' attribute
        # https://github.com/knit-bee/tei-transform/blob/60ac079c0d91a9196e98c2be89c9c287cecee824/tei_transform/element_transformation.py#L18
        namespace = "http://www.w3.org/XML/1998/namespace"
        old_attr = 'id'
        old_attribute = comment.attrib.get(old_attr)
        if old_attribute is not None:
            attr_value = comment.attrib.pop(old_attr)
            new_attribute = etree.QName(namespace, old_attr)
            comment.set(new_attribute, attr_value)
        # author and date as subelements
        author = SubElement(comment, 'name')
        author.text = subcomment['author']
        time = datetime.utcfromtimestamp(int(subcomment['created_utc']))
        date = SubElement(comment, 'date')
        date.text = str(time.date())
        # convert html character references
        comment.text = html.unescape(subcomment['body'])
        # tranform line breaks to <lb>
        if '\n' in subcomment['body']:
            num_lb = subcomment['body'].count('\n')
            # text until first line break
            comment.text = subcomment['body'].split('\n')[0]
            for i in range(num_lb):
                line_break = Element("lb")
                # text after line break
                line_break.tail = subcomment['body'].split('\n')[i + 1]
                comment.append(line_break)
        else:
            comment.text = subcomment['body']
        # display date and author after text
        comment.append(date)
        comment.append(author)
        # recursively build comment tree structure if wished
        if tree_structure:
            if subcomment['responses']:
                comment_list = SubElement(comment, 'list')
                for r in subcomment['responses']:
                    if not filtered:
                        if r['body'] == '[deleted]' or r['author'] == '[deleted]':
                            continue
                    build_subcomments(comment_list, r)


def json2xml(file, tree_structure=False, output_dir='wohnen_xml',
             filtered=True, subreddit_loc='title'):
    """
    Convert Reddit JSON data to TEI XML format.

    Args:
        file (str): The path to the input JSON file.
        tree_structure (bool, optional): Whether the input file is in a tree
            structure. Defaults to False.
        output_dir (str, optional): The directory to save the generated XML
            file. Defaults to 'wohnen_xml'.
        filtered (bool, optional): Whether deleted comments and authors are
            already removed. Defaults to True.
        subreddit_loc (str, optional): Location to include subreddit
            information ('profiledesc' or 'title'). Defaults to 'title'.

    Returns:
        str: The TEI XML document as a string.
    """
    # read json file
    with open(file, 'r', encoding='latin-1') as f:
        txt = f.read()
    comments = json.loads(txt)
    if not comments:
        print(f'Empty file: {file}')
        return
    # extract post metadata information
    docmeta = dict()
    # use first comment entry to extract meta data information
    if tree_structure:  # dict
        _, info = list(comments.items())[0]
    else:  # list
        info = comments[0]
    time = datetime.utcfromtimestamp(int(info['created_utc']))
    docmeta["date"] = str(time.date())
    # permalink example: /r/wohnen/comments/qqro38/wie_soll_ich_mit_meinen_überempfindlichen/hk1xuv3/
    _, _, subreddit, _, post_id, title, comment_id, _ = \
        info['permalink'].split('/')
    # reconstruct title and URL from permalink
    docmeta["title"] = title
    docmeta["url"] = f'https://www.reddit.com/r/{subreddit}/comments/{post_id}/{title}/'
    docmeta["subreddit"] = subreddit
    if subreddit_loc == 'title':
        docmeta["title"] = f'{subreddit}/{title}'

    # build tei xml doc
    teidoc = Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    header = SubElement(teidoc, 'teiHeader')
    filedesc = SubElement(header, 'fileDesc')

    # title statement
    bib_titlestmt = SubElement(filedesc, 'titleStmt')
    bib_titlemain = SubElement(bib_titlestmt, 'title', type='main')
    bib_titlemain.text = docmeta["title"]
    if 'author' in docmeta.keys():
        bib_author = SubElement(bib_titlestmt, 'author')
        bib_author.text = docmeta.author
    publicationstmt_a = SubElement(filedesc, 'publicationStmt')
    # empty paragraph, otherwise license?
    publicationstmt_p = SubElement(publicationstmt_a, 'p')

    # source description
    sourcedesc = SubElement(filedesc, 'sourceDesc')
    source_bibl = SubElement(sourcedesc, 'bibl')
    biblfull = SubElement(sourcedesc, 'biblFull')
    # title statement once again
    bib_titlestmt2 = SubElement(biblfull, 'titleStmt')
    bib_titlemain2 = SubElement(bib_titlestmt2, 'title', type='main')
    bib_titlemain2.text = docmeta["title"]

    # publication statement
    publicationstmt = SubElement(biblfull, 'publicationStmt')
    publisher = SubElement(publicationstmt, 'publisher')
    publication_date = SubElement(publicationstmt, 'date')
    publication_url = SubElement(publicationstmt, 'ptr', type='URL',
                                 target=docmeta['url'])
    publication_date.text = docmeta['date']

    # profile description
    if subreddit_loc == 'profiledesc':
        profiledesc = SubElement(header, 'profileDesc')
        textclass = SubElement(profiledesc, 'textClass')
        subred = SubElement(textclass, 'subreddit')
        term = SubElement(subred, 'term')
        term.text = docmeta["subreddit"]

    # text, body, comments
    text = SubElement(teidoc, "text")
    body = SubElement(text, "body")
    # correct level for responses? or rather under text or other?
    res = SubElement(body, "div", type="comments")
    responses = SubElement(res, "list")
    if tree_structure:
        # iterate comments to include responses
        for id, comment in comments.items():
            if not filtered:
                if comment['body'] == '[deleted]' or \
                    comment['author'] == '[deleted]':
                    continue
            build_subcomments(responses, comment, tree_structure)
    else:
        for comment in comments:
            if not filtered:
                if comment['body'] == '[deleted]' or \
                    comment['author'] == '[deleted]':
                    continue
            build_subcomments(responses, comment, tree_structure)

    tei_str = tostring(teidoc, pretty_print=True,
                       encoding='utf-8').decode('utf-8')
    if output_dir:
        ElementTree(teidoc).write(f'{output_dir}/{post_id}.xml',
                                  pretty_print=True, encoding='utf-8')
    return tei_str


def demo():
    """A short demo of the json2xml function."""
    print(json2xml('../examples/wohnen_json/qqro38_flat.json', tree_structure=False,
             output_dir='wohnen_xml'))
    print(json2xml('../examples/wohnen_json/qlt4qy_flat.json', tree_structure=False,
                   output_dir='../examples/wohnen_xml'))


def run(dir, output_dir):
    """Convert all json files in a directory to xml."""
    for file in os.listdir(dir):
        json2xml(f'{dir}/{file}', output_dir=output_dir)


if __name__ == '__main__':
    demo()
