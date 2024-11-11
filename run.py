import json
import os
import argparse

from extractor.trim_username_comments import process_comments
from extractor.comment_tree import extract_comments
from extractor.json2xml import json2xml
from extractor.validate import load_schema, validate_directory

MAX_FILES_PER_DIR = 1000 # max files each folder
error_log = []  # error log for problematic JSON objects

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

def pipeline(zstfile, subreddit, no_group=False):
    print(f'Processing subreddit: "{subreddit}".')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subreddits_dir = os.path.join(base_dir, 'subreddits')
    os.makedirs(subreddits_dir, exist_ok=True)
    
    # define mode based on grouping
    mode = "nogroup" if no_group else "grouped"
    subreddit_folder = os.path.join(subreddits_dir, f"{subreddit}_{mode}")
    os.makedirs(subreddit_folder, exist_ok=True)

    # define JSON and XML output directories based on mode
    json_output_dir = os.path.join(subreddit_folder, f"{subreddit}_json_{mode}")
    xml_output_dir = os.path.join(subreddit_folder, f"{subreddit}_xml_{mode}")

    os.makedirs(json_output_dir, exist_ok=True)
    os.makedirs(xml_output_dir, exist_ok=True)
    
    # process comments in the zst file (apply filters)
    process_comments(zstfile, remove_deleted=True, remove_quotes=True, remove_remindme=True, remove_urls=True)
    print("Extracting comments. This may take a while...")
    comments = extract_comments(f"{zstfile.rsplit('.', 1)[0]}_filtered.zst")
    
    if no_group:
        # processing each comment individually in `no_group` mode
        for comment in comments:
            comment_id = comment['id']
            link_id = comment['link_id'].replace('t3_', '')
            json_subdir = get_output_dir(json_output_dir)
            json_filename = f"{json_subdir}/{link_id}_{comment_id}.json"
            try:
                # save each comment as a JSON file and convert it to XML
                with open(json_filename, 'w', encoding='utf-8') as outfile:
                    json.dump([comment], outfile, indent=4)
                xml_subdir = get_output_dir(xml_output_dir)
                json2xml(json_filename, output_dir=xml_subdir, link_id=link_id, comment_id=comment_id, group_mode=not args.no_group)
            except Exception as e:
                error_log.append(f"Error in file {json_filename}: {e}")
    else:
        # group coments by thread in grouped mode
        thread_comments = {}
        for comment in comments:
            thread_id = comment.get('link_id', '').replace('t3_', '')
            if thread_id not in thread_comments:
                thread_comments[thread_id] = []
            thread_comments[thread_id].append(comment)

        # save grouped comments per thread as JSON and convert to XML
        for thread_id, comments_list in thread_comments.items():
            json_subdir = get_output_dir(json_output_dir)
            json_filename = f"{json_subdir}/{thread_id}_flat.json"
            try:
                with open(json_filename, 'w', encoding='utf-8') as outfile:
                    json.dump(comments_list, outfile, indent=4)
                xml_subdir = get_output_dir(xml_output_dir)
                json2xml(json_filename, output_dir=xml_subdir)
            except Exception as e:
                error_log.append(f"Error in file {json_filename}: {e}")
    
    print('Validate XML files.')
    TEI_RELAXNG = load_schema()
    validate_directory(xml_output_dir, TEI_RELAXNG)

def pipeline_json2xml(dir_json):
    """pipeline if the json files already exist: convert to XML, validate"""
    xml_output_dir = dir_json.replace('json', 'xml')
    os.makedirs(xml_output_dir, exist_ok=True)
    for file in os.listdir(dir_json):
        json_path = os.path.join(dir_json, file)
        if os.path.isfile(json_path):
            link_id, comment_id = file.replace('.json', '').split('_')
            # select or create an XML subdirectory for output
            xml_subdir = get_output_dir(xml_output_dir)
            json2xml(json_path, output_dir=xml_subdir, link_id=link_id, comment_id=comment_id)
    
    print('Validate XML files.')
    TEI_RELAXNG = load_schema()
    validate_directory(xml_output_dir, TEI_RELAXNG)

# count JSON objects in a .zst file with NDJSON content
def count_json_objects_in_zst(zst_path):
    count = 0
    with open(zst_path, 'rb') as file:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(file) as reader:
            buffer = ""
            while chunk := reader.read(16384):
                buffer += chunk.decode(errors='ignore')
                # count lines in the buffer that correspond to JSON objects
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        count += 1
    return count

# counts JSON objects in all JSON files within a directory
def count_json_objects_in_directory(directory_path):
    count = 0
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        for line in file:
                            json.loads(line)
                            count += 1
                    except json.JSONDecodeError:
                        # handle JSON array format
                        file.seek(0)
                        data = json.load(file)
                        if isinstance(data, list):
                            count += len(data)
    return count

# compare the number of JSON objects in the filtered .zst file and the JSON output directory
def compare_json_counts(filtered_zst_path, json_output_dir):
    zst_count = count_json_objects_in_zst(filtered_zst_path)
    json_count = count_json_objects_in_directory(json_output_dir)
    
    print(f"Number of JSON objects in filtered .zst file: {zst_count}")
    print(f"Number of JSON objects in JSON output directory: {json_count}")
    
    if zst_count == json_count:
        print("The number of JSON objects matches.")
    else:
        print("Note: number of JSON objects differ, likely due to comments containing null bytes or control characters that couldn't be processed.")
        if error_log:
            print("Details on problematic objects are listed above.")


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
