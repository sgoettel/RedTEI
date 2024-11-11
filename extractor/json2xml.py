"""
Transform Reddit files in json format to TEI-XML

Author: Lydia Körber, Sebastan Göttel 2024
"""

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
    """Return a character if it belongs to certain classes"""
    return char if char.isprintable() or char.isspace() else ''


def remove_control_characters(string):
    """Prevent non-printable and XML invalid character errors"""
    return ''.join(map(return_printables_and_spaces, string))

def process_comment_text(comment_text):
    """Processes the comment text, converts HTML characters, and removes problematic XML characters."""
    comment_text = html.unescape(comment_text) # convert html character references
    comment_text = comment_text.replace("&gt;", ">") # Replace &gt; with > manually to ensure correct display in XML
    comment_text = remove_control_characters(comment_text)
    comment_text = re.sub(r'/u/(\w+)', r'\1', comment_text) # replace username mentions, /u/username → username
    
    # Remove additional control characters and NULL bytes
    comment_text = comment_text.replace('\u001c', ' ') # File Separator
    comment_text = comment_text.replace('\u001e', ' ') # Record Separator
    comment_text = comment_text.replace('\0', ' ')  # NULL-Bytes
    
    # transform line breaks to <lb> (do we need white space after last line break?)
    try:
        if '\n' in comment_text:
            text_parts = comment_text.split('\n')
            elements = [remove_control_characters(text_parts[0])]
            for part in text_parts[1:]:
                lb_element = Element("lb")
                lb_element.tail = remove_control_characters(part)  # ensure XML-safe text
                elements.append(lb_element)
            return elements
        else:
            return [remove_control_characters(comment_text)]
    except ValueError as e:
        print("Error processing comment text:", repr(comment_text))
        print("Error message:", e)
        raise e
    
def create_comment_element(parent_element, comment, base_info, element_type='item'):
    """Creates XML element for a comment (as <item> or <p> depending on the mode)."""
    comment_url = f"{base_info['thread_url']}comment/{comment['id']}/"
    
    # different structures depending on the mode
    if element_type == 'item':
        # standard mode: Comment as <item> with metadata
        comment_elem = SubElement(parent_element, 'item', source=comment_url)
        
        # process the comment's text content
        comment_content = process_comment_text(comment['body'])
        if isinstance(comment_content, list):
            comment_elem.text = comment_content[0]
            for element in comment_content[1:]:
                comment_elem.append(element)
        else:
            comment_elem.text = comment_content

        # add <date> and <name> only in standard mode
        date_elem = SubElement(comment_elem, 'date')
        date_elem.text = str(datetime.utcfromtimestamp(int(comment['created_utc'])).date())
        date_elem.tail = " "  # optional space after <date> (how should we handle this?)

        author_elem = SubElement(comment_elem, 'name')
        author_elem.text = comment['author']
        author_elem.tail = " "  # optional space after <name> (same question)
        
    else:
        # `--no-group` mode: only comment text as <p> without metadata
        comment_elem = SubElement(parent_element, 'p')
        comment_content = process_comment_text(comment['body'])
        if isinstance(comment_content, list):
            comment_elem.text = comment_content[0]
            for element in comment_content[1:]:
                comment_elem.append(element)
        else:
            comment_elem.text = comment_content

    return comment_elem

def create_tei_header(teidoc, docmeta, retrieved_on, group_mode):
    """creates the TEI header based on the mode."""
    header = SubElement(teidoc, 'teiHeader')
    filedesc = SubElement(header, 'fileDesc')
    
    # common titleStmt
    titleStmt = SubElement(filedesc, 'titleStmt')
    title_main = SubElement(titleStmt, 'title', type='main')
    title_main.text = docmeta["title"]

    # common publicationStmt
    publicationStmt = SubElement(filedesc, 'publicationStmt')
    SubElement(publicationStmt, 'p')

    # sourceDesc for both modes with basic information
    sourceDesc = SubElement(filedesc, 'sourceDesc')
    bibl = SubElement(sourceDesc, 'bibl')
    bibl.text = f"Reddit/{docmeta['subreddit']}: {docmeta['title']}, {docmeta['date']}"

    biblFull = SubElement(sourceDesc, 'biblFull')
    titleStmt_full = SubElement(biblFull, 'titleStmt')

    # distinction depending on mode
    if group_mode:
        # standard mode (grouped): simpler structure
        title_main_full = SubElement(titleStmt_full, 'title', type='main')
        title_main_full.text = f"Reddit/{docmeta['subreddit']}"

        pubStmt = SubElement(biblFull, 'publicationStmt')
        publisher = SubElement(pubStmt, 'publisher')
        ptr_url = SubElement(pubStmt, 'ptr', type="URL", target=docmeta["thread_url"])
        date_publication = SubElement(pubStmt, 'date', type="last_comment")
        date_publication.text = str(docmeta["date"])

    else:
        # `--no-group` mode: more detailed structure
        title_main_a = SubElement(titleStmt_full, 'title', type='main', level="a")
        title_main_a.text = docmeta["title"]

        author = SubElement(titleStmt_full, 'author')
        author.text = docmeta["author"]

        pubStmt = SubElement(biblFull, 'publicationStmt')
        publisher = SubElement(pubStmt, 'publisher')
        ptr_thread = SubElement(pubStmt, 'ptr', type="thread", target=docmeta["thread_url"])
        ptr_comment = SubElement(pubStmt, 'ptr', type="comment", target=docmeta["comment_url"])
        date_last_comment = SubElement(pubStmt, 'date')
        date_last_comment.text = str(docmeta["date"])

        # specific seriesStmt for `--no-group`
        seriesStmt = SubElement(biblFull, 'seriesStmt')
        title_main_m = SubElement(seriesStmt, 'title', type="main", level="m")
        title_main_m.text = "Reddit"
        
        title_sub_m = SubElement(seriesStmt, 'title', type="sub", level="m")
        title_sub_m.text = docmeta["subreddit"]

    # common profileDesc with download date
    profileDesc = SubElement(header, 'profileDesc')
    creation = SubElement(profileDesc, 'creation')
    download_date = SubElement(creation, 'date', type="download")
    download_date.text = retrieved_on


def json2xml(file, tree_structure=False, output_dir=None, 
             filtered=True, subreddit_loc='title', link_id=None, 
             comment_id=None, group_mode=True):
    """converts Reddit JSON data into TEI XML."""
    # read JSON file
    with open(file, 'r', encoding='latin-1') as f:
        txt = f.read()
    comments = json.loads(txt)
    if not comments:
        print(f'Empty file: {file}')
        return
    
    # extract metadata
    info = comments[-1] if not tree_structure else list(comments.values())[-1]
    post_id = link_id or info['link_id'][3:]  # remove 't3_' prefix
    subreddit = info['subreddit']

    # create title and URL
    title = post_id  # fallback if no permalink part is present
    if 'permalink' in info:
        _, _, subreddit, _, post_id, title, *_ = info['permalink'].split('/')
    
    thread_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
    comment_url = f"{thread_url}comment/{info['id']}/"

    # create metadata structure
    docmeta = {
        "post_id": post_id,
        "title": title,
        "date": datetime.utcfromtimestamp(int(info['created_utc'])).date(),
        "subreddit": subreddit,
        "author": info.get("author", "Unknown Author"),
        "thread_url": thread_url,
        "comment_url": comment_url,
    }
    
    # determine download date
    if 'retrieved_on' in info:
        retrieved_date = datetime.utcfromtimestamp(int(info['retrieved_on']))
    elif 'retrieved_utc' in info:
        retrieved_date = datetime.utcfromtimestamp(int(info['retrieved_utc']))
    else:
        file_creation = os.path.getctime(file)
        retrieved_date = datetime.fromtimestamp(file_creation)
    retrieved_on = str(retrieved_date.date())

    # create TEI root element and add header
    teidoc = Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    create_tei_header(teidoc, docmeta, retrieved_on, group_mode)

    # text body based on mode
    text = SubElement(teidoc, "text")
    body = SubElement(text, "body")
    if group_mode:
        # standard mode: insert comments into a <list>
        comments_div = SubElement(body, "div", type="comments")
        comment_list = SubElement(comments_div, "list")
        
        for comment in comments:
            if not filtered or comment['body'] != '[deleted]':
                create_comment_element(comment_list, comment, docmeta, element_type='item')
    else:
        # `--no-group` mode: each comment as an individual <p> element
        if not filtered or info['body'] != '[deleted]':
            create_comment_element(body, info, docmeta, element_type='p')

    # save XML
    tei_str = tostring(teidoc, pretty_print=True, encoding='utf-8')
    filename = f"{output_dir}/{post_id}.xml" if group_mode else f"{output_dir}/{link_id}_{comment_id}.xml"
    ElementTree(teidoc).write(filename, pretty_print=True, encoding='utf-8')
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
    for file in os.listdir(dir):
        try:
            json2xml(f'{dir}/{file}', output_dir=output_dir)
        except Exception as e:
            print(file, e)


if __name__ == '__main__':
    demo()
