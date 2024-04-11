"""
Transform Reddit files in json format to TEI-XML

Author: Lydia Körber, 2023
"""

import concurrent.futures
from datetime import datetime
import html
import json
import os
import re

from lxml.etree import (
    Element,
    ElementTree,
    SubElement,
    tostring
)


def return_printables_and_spaces(char):
    'Return a character if it belongs to certain classes'
    return char if char.isprintable() or char.isspace() else ''


def remove_control_characters(string):
    '''Prevent non-printable and XML invalid character errors'''
    return ''.join(map(return_printables_and_spaces, string))


def build_subcomments(supercomment_element, subcomment, base_info,
                      tree_structure=False, filtered=True):
    """
    Build TEI XML subcomments within a parent comment element.

    Args:
        supercomment_element (Element): The parent comment element to which
            subcomments will be added.
        subcomment (dict): The subcomment data in a dictionary format.
        base_info (dict): metadata of the comment thread.
        tree_structure (bool, optional): Whether comments and subcomments are
            saved in a nested tree structure. Defaults to False.
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
    # Check for 'permalink' in subcomment, else construct URL
    if 'permalink' in subcomment:
        comment_url = f"https://www.reddit.com{subcomment['permalink']}"
    else:
        subreddit = base_info['subreddit']
        post_id = base_info["post_id"]
        comment_id = subcomment['id']
        comment_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/comment/{comment_id}"

    comment = SubElement(supercomment_element, 'item', source=comment_url)

    # author, date as subelements
    author = SubElement(comment, 'name')
    author.text = subcomment['author']
    time = datetime.utcfromtimestamp(int(subcomment['created_utc']))
    date = SubElement(comment, 'date')
    date.text = str(time.date())

    comment_text = html.unescape(subcomment['body'])
    # convert html character references
    while "&gt;" in comment_text:
        comment_text = html.unescape(comment_text)
    # Replace &gt; with > manually to ensure correct display in XML
    comment_text = comment_text.replace("&gt;", ">")
    comment_text = remove_control_characters(comment_text)
    # replace username mentions, /u/username → username
    comment_text = re.sub(r'/u/(\w+)', r'\1', comment_text)
    # replace NULL bytes/control character
    comment_text = comment_text.replace('\u001c', ' ')

    # transform line breaks to <lb>
    if '\n' in comment_text:
        num_lb = comment_text.count('\n')
        # text until first line break
        comment.text = comment_text.split('\n')[0]
        for i in range(num_lb):
            line_break = Element("lb")
            # text after line break
            line_break.tail = comment_text.split('\n')[i + 1]
            comment.append(line_break)
    else:
        comment.text = comment_text

    # display date, author and url after text
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
                build_subcomments(comment_list, r, base_info)


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
    # extract retrieved_on date
    if 'retrieved_on' in info:
        retrieved_date = datetime.utcfromtimestamp(int(info['retrieved_on']))
    # fallback to retrieved_utc if retrieved_on is not available
    elif 'retrieved_utc' in info:
        retrieved_date = datetime.utcfromtimestamp(int(info['retrieved_utc']))
    else:  # retrieval date not saved in json, use os creation time of file
        file_creation = os.path.getctime(file)
        retrieved_date = datetime.fromtimestamp(file_creation)
    # Convert retrieved date to string representation
    retrieved_on = str(retrieved_date.date())
    # process subreddit and link_id for URL and title
    subreddit = info['subreddit']
    post_id = info['link_id'][3:]  # remove 't3_'
    docmeta['post_id'] = post_id
    # reconstruct URL
    docmeta["url"] = f'https://www.reddit.com/r/{subreddit}/comments/{post_id}/'
    docmeta["subreddit"] = subreddit
    # create title
    if 'permalink' in info:
        _, _, subreddit, _, post_id, title, _, _ = info['permalink'].split('/')
        docmeta["title"] = title
        if subreddit_loc == 'title':
            docmeta["title"] = title
    else:
        # use subreddit and link_id if no permalink
        docmeta["title"] = post_id
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
    bib_titlemain2.text = 'Reddit/' + docmeta["subreddit"]

    # publication statement
    publicationstmt = SubElement(biblfull, 'publicationStmt')
    publisher = SubElement(publicationstmt, 'publisher')
    publication_url = SubElement(publicationstmt, 'ptr', type='URL',
                                 target=docmeta['url'])
    date_publication = SubElement(publicationstmt, 'date')
    date_publication.text = docmeta["date"]

    # profile description
    profiledesc = SubElement(header, 'profileDesc')
    creation = SubElement(profiledesc, 'creation')
    date_creation = SubElement(creation, 'date', type='download')
    # use retrieved_on variable (either retrieved_on or retrieved_utc)
    date_creation.text = retrieved_on

    # additional profile description
    # (if subreddit information is included in the profileDesc)
    if subreddit_loc == 'profiledesc':
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
            build_subcomments(responses, comment, docmeta,
                              tree_structure)
    else:
        for comment in comments:
            if not filtered:
                if comment['body'] == '[deleted]' or \
                        comment['author'] == '[deleted]':
                    continue
            build_subcomments(responses, comment, docmeta, tree_structure)

    tei_str = tostring(teidoc, pretty_print=True, encoding='utf-8')
    if output_dir:
        ElementTree(teidoc).write(f'{output_dir}/{post_id}.xml',
                                  pretty_print=True, encoding='utf-8')
    return tei_str


def demo():
    """A short demo of the json2xml function."""
    json_files = ['5wa69r_flat', '1891529_flat', 'ushrnp_flat', 'wmip8z_flat',
                  '4dklie_flat', 'lmjo20_flat']
    for f in json_files:
        print(json2xml(f'../examples/demo/{f}.json', tree_structure=False,
                       output_dir='../examples/demo'))


def run(dir, output_dir):
    """Convert all json files in a directory to xml."""
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for file in os.listdir(dir):
            try:
                executor.submit(json2xml, f'{dir}/{file}',
                                output_dir=output_dir)
            except Exception as e:
                print(file, e)


if __name__ == '__main__':
    demo()
