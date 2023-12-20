"""
Extract comments from a Reddit zst file

Author: Sebastian Göttel, 2023
https://github.com/sgoettel/zstsidescripts/blob/main/comment_tree.py
"""

import argparse
import json
import zstandard as zstd

CHUNK_SIZE = 16384

def extract_comments(zst_file, link_id=None, structured=True):
    dctx = zstd.ZstdDecompressor()
    comments_mapping = {}
    top_level_comments = []

    with open(zst_file, 'rb') as fh:
        with dctx.stream_reader(fh) as reader:
            buffer = ""

            while True:
                chunk = reader.read(CHUNK_SIZE)
                if not chunk:
                    break

                buffer += chunk.decode(errors='ignore')

                while True:
                    position = buffer.find('\n')
                    if position == -1:
                        break

                    line = buffer[:position]
                    buffer = buffer[position + 1:]

                    try:
                        obj = json.loads(line)

                        if link_id and obj.get('link_id', '').replace('t3_', '') != link_id:
                            continue

                        if obj.get('link_id', '').startswith('t3_'):
                            comments_mapping[obj['id']] = obj
                            if obj['parent_id'].startswith('t3_'):
                                top_level_comments.append(obj['id'])
                            obj['responses'] = []

                    except json.JSONDecodeError:
                        continue

    if structured:
        for comment_id, comment in comments_mapping.items():
            parent_id = comment['parent_id'].replace('t1_', '')
            if parent_id in comments_mapping:
                comments_mapping[parent_id]['responses'].append(comment)

        comments = {comment_id: comments_mapping[comment_id] for comment_id in top_level_comments}
    else:
        comments = list(comments_mapping.values())

    return comments

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract the comments from a Reddit zst compressed file.')
    parser.add_argument('zst_file', help='Path to the zst compressed file containing Reddit comments.')
    parser.add_argument('out_dir', help='Path to the output directory.')
    parser.add_argument('-l', '--link_id', help='Link ID of the Reddit post without prefix.', default=None)
    parser.add_argument('-a', '--all', action='store_true', help='Extract all threads from the zst file.')
    parser.add_argument('-s', '--structured', action='store_true', default=False, help='Extract comments in structured format.')
    parser.add_argument('-f', '--flat', action='store_true', default=False, help='Extract comments in flat format.')

    args = parser.parse_args()

    if args.structured:
        suffix = "_tree"
    else:
        suffix = "_flat"

    if args.all:
        print("Extracting all threads. This may take a while...")
        threads = set()
        dctx = zstd.ZstdDecompressor()

        with open(args.zst_file, 'rb') as fh:
            with dctx.stream_reader(fh) as reader:
                buffer = ""

                while True:
                    chunk = reader.read(CHUNK_SIZE)
                    if not chunk:
                        break

                    buffer += chunk.decode(errors='ignore')

                    while True:
                        position = buffer.find('\n')
                        if position == -1:
                            break

                        line = buffer[:position]
                        buffer = buffer[position + 1:]

                        try:
                            obj = json.loads(line)
                            threads.add(obj.get('link_id', '').replace('t3_', ''))
                        except json.JSONDecodeError:
                            continue

        for thread_id in threads:
            comments = extract_comments(args.zst_file, thread_id, args.structured)
            with open(f"{args.out_dir}/{thread_id}{suffix}.json", 'w', encoding='utf-8') as outfile:
                json.dump(comments, outfile, indent=4)

    else:
        if not args.link_id:
            args.link_id = input("Please provide a link ID without prefix: ")
        comments = extract_comments(args.zst_file, args.link_id, args.structured)
        with open(f"{args.out_dir}/{args.link_id}{suffix}.json", 'w', encoding='utf-8') as outfile:
            json.dump(comments, outfile, indent=4)
