import json
import os
import argparse

from extractor.trim_username_comments import process_comments
from extractor.comment_tree import extract_comments
from extractor.json2xml import run
from extractor.validate import load_schema, validate_directory

MAX_FILES_PER_DIR = 1000 # max files each folder

def get_output_dir(base_dir):
    """finds or creates a subdirectory that contains less than MAX_FILES_PER_DIR files."""
    subdirs = sorted(
        [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.isdigit()],
        key=lambda x: int(x)
    )
    # create a new subdirectory if the last one is full
    if not subdirs or len(os.listdir(os.path.join(base_dir, subdirs[-1]))) >= MAX_FILES_PER_DIR:
        next_subdir = str(int(subdirs[-1]) + 1).zfill(5) if subdirs else "00001"
        new_dir = os.path.join(base_dir, next_subdir)
        os.makedirs(new_dir, exist_ok=True)
        return new_dir
    else:
        return os.path.join(base_dir, subdirs[-1])

def pipeline(zstfile, subreddit):
    """full pipeline: filter, extract json files, convert to XML, validate"""
    print(f'Processing subreddit: "{subreddit}".')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subreddits_dir = os.path.join(base_dir, 'subreddits')
    # create general subreddits directory
    os.makedirs(subreddits_dir, exist_ok=True)
    # generate file name for filtered zst file
    zst_filtered = f"{zstfile.rsplit('.', 1)[0]}_filtered.zst"

    # execute process_comments function from trim_username_comments.py
    process_comments(zstfile, remove_deleted=True, remove_quotes=True,
                     remove_remindme=True, remove_urls=True)
    print("Extracting comments. This may take a while...")
    comments = extract_comments(zst_filtered)
    thread_comments = {}    
    for comment in comments:
        thread_id = comment.get('link_id', '').replace('t3_', '')
        if thread_id not in thread_comments:
            thread_comments[thread_id] = []
        thread_comments[thread_id].append(comment)
    for thread_id, comments_list in thread_comments.items():
        with open(f"{dir_json}/{thread_id}_flat.json", 'w', encoding='utf-8') \
            as outfile:
            json.dump(comments_list, outfile, indent=4)
    print('Convert json to XML files.')
    # convert all json to XML
    run(dir_json, dir_xml)
    print('Validate XML files.')
    # validate all XML files
    TEI_RELAXNG = load_schema()
    validate_directory(dir_xml, TEI_RELAXNG)

def pipeline_json2xml(dir_json):
    """pipeline if the json files already exist: convert to XML, validate"""
    dir_xml = dir_json.replace('json', 'xml')
    if not os.path.exists(dir_xml):
        os.mkdir(dir_xml)
    # convert all json to XML
    run(dir_json, dir_xml)
    print('Validate XML files.')
    # validate all XML files
    TEI_RELAXNG = load_schema()
    validate_directory(dir_xml, TEI_RELAXNG)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Reddit comments.')
    parser.add_argument('files', nargs='+', help='Path to one or more .zst files or _json directories.')
    parser.add_argument('--no-group', action='store_true', help='Process each comment individually.')
    args = parser.parse_args()
    for file in args.files:
        if file.endswith('.zst'):
            subreddit = file.split('/')[-1].replace('_comments.zst', '')
            pipeline(file, subreddit, no_group=args.no_group)
        elif file.endswith('_json') or file.endswith('_json/'):
            pipeline_json2xml(file)
        else:
            print('Please provide the path to one or more .zst files or _json directories.')
