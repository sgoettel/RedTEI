"""
Filter comments from bots, quotations, URLs and deleted or removed comments

Author: Sebastian Göttel, 2024
https://github.com/sgoettel/zstsidescripts/blob/main/trim_username_comments.py
"""

import argparse
import json
import zstandard as zstd
import re

CHUNK_SIZE = 16384

# regex for both URL types
plain_url_regex = re.compile(r'(?<!\])\b(?:https?://|www\.)\S+\b/?', re.IGNORECASE)
markdown_url_regex = re.compile(r'\[([^\]]+)\]\((https?://|www\.)\S+\)')

def remove_plain_urls(text):
    return plain_url_regex.sub('[URL]', text)

def remove_markdown_urls(text):
    def replace_markdown_url(match):
        link_text, link_url = match.groups()
        # check if text is also URL
        if plain_url_regex.match(link_text):
            return '[URL]'
        else:
            return link_text
    
    return markdown_url_regex.sub(replace_markdown_url, text)

def filter_comments(zst_file, authors, remove_deleted, remove_quotes, remove_remindme, remove_urls, log_file):
    dctx = zstd.ZstdDecompressor()
    cctx = zstd.ZstdCompressor(level=15)
    
    # matches a citation marker at the start of a line or text, capturing everything up to the next citation marker, newline, or end of text
    quote_regex = re.compile(r"(?:\n|^)(&gt;.*?)(?=(\n&gt;)|\n|$)")

    # catches various ways users try to summon the RemindMeBot, even though there's technically just one right way to do it..it can vary..
    remindme_regex = re.compile(r'^\s*(!remindme|!RemindMe|!remind me|RemindMe!|Remind me!)\b', re.IGNORECASE)

    input_filename = zst_file
    output_filename = f"{zst_file.rsplit('.', 1)[0]}_filtered.zst"
    log_filename = log_file

    excluded_counts = {author.lower(): 0 for author in authors} if authors else {}
    deleted_count = 0
    removed_url_only_comments_count = 0
    quote_removal_count = 0
    remindme_count = 0
    url_removal_count = 0

    with open(input_filename, 'rb') as fh, open(output_filename, 'wb') as ofh, open(log_filename, 'w') as lf:
        lf.write("Logfile initiated.\n")
        with dctx.stream_reader(fh) as reader, cctx.stream_writer(ofh) as writer:
            buffer = ""
            deleted_tags = ["[removed]", "[deleted]", "[removed by reddit]"]
            
            while True:
                chunk = reader.read(CHUNK_SIZE)
                if not chunk:
                    break

                buffer += chunk.decode(errors='ignore')

                last_modified_body = None  # initialize last_modified_body for every new chunk

                while True:
                    position = buffer.find('\n')

                    if position == -1:
                        break

                    line = buffer[:position]
                    buffer = buffer[position + 1:]

                    # reset flags for every iteration
                    quote_changed = False
                    url_changed = False

                    try:
                        obj = json.loads(line)
                        body_changed = False
                        original_body = obj["body"]

                        # check and filter out comments from specific authors
                        if authors and obj["author"].lower() in authors:
                            excluded_counts[obj["author"].lower()] += 1
                            continue # skip further processing for this comment

                        # check and remove deleted or removed comments
                        if remove_deleted and obj["body"].strip() in deleted_tags:
                            deleted_count += 1
                            # log the removal
                            lf.write("\n=========== body: deleted/removed ==========\n")
                            lf.write(json.dumps({"original": original_body, "deleted_comment": obj}) + "\n")
                            continue

                        # check if body-text is just plaintext URL
                        if remove_urls and plain_url_regex.fullmatch(obj["body"].strip()):
                            removed_url_only_comments_count += 1
                            # log the removal
                            lf.write("\n=========== body: removed due to being only a URL ==========\n")
                            lf.write(json.dumps({"original": original_body}) + "\n")
                            continue

                        # remove quotations
                        if remove_quotes:
                            cleaned_body = re.sub(quote_regex, '', obj["body"]).strip()
                            if cleaned_body != obj["body"]:
                                obj["body"] = cleaned_body
                                quote_removal_count += 1
                                quote_changed = True
                                body_changed = True

                        if remove_urls:
                            # count URLs in comments
                            original_plain_url_count = len(plain_url_regex.findall(obj["body"]))
                            original_markdown_url_count = len(markdown_url_regex.findall(obj["body"]))

                            # for markdown URLs
                            new_body_markdown_urls_removed = remove_markdown_urls(obj["body"])
                            # for plain URLs
                            new_body_plain_urls_removed = remove_plain_urls(new_body_markdown_urls_removed)

                            if new_body_plain_urls_removed != obj["body"]:
                                obj["body"] = new_body_plain_urls_removed
                                body_changed = True
                                url_changed = True
                                
                                # count URLs after processing
                                new_plain_url_count = len(plain_url_regex.findall(obj["body"]))
                                new_markdown_url_count = len(markdown_url_regex.findall(obj["body"]))
                                
                                # count number of processed URLs and add to url_removal_count
                                urls_removed = (original_plain_url_count - new_plain_url_count) + (original_markdown_url_count - new_markdown_url_count)
                                url_removal_count += urls_removed

                        # remove RemindMe bot invocations
                        if remove_remindme and remindme_regex.search(obj["body"]):
                            remindme_count += 1
                            body_changed = True
                            lf.write("\n=========== body: !remindme ==========\n")
                            lf.write(json.dumps({"original": original_body, "modified": obj["body"]}) + "\n")


                        if body_changed: #this keeps me going..
                            if last_modified_body != obj["body"]:  # only log if applicable
                                last_modified_body = obj["body"]  # refresh last_modified_body
                                if quote_changed:
                                    lf.write("\n=========== body: contained quotation ==========\n")
                                    lf.write(json.dumps({"original": original_body, "modified": obj["body"]}) + "\n")
                                if url_changed:
                                    lf.write("\n=========== body: URL (any type) ==========\n")
                                    lf.write(json.dumps({"original": original_body, "modified": obj["body"]}) + "\n")

                        writer.write(json.dumps(obj).encode() + b"\n")

                    except json.JSONDecodeError:
                        continue


    return excluded_counts, deleted_count, quote_removal_count, remindme_count, url_removal_count, removed_url_only_comments_count

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filter Reddit comments based on certain criteria.')
    parser.add_argument('zst_file', help='Path to the zst compressed file containing Reddit comments.')
    parser.add_argument('-a', '--author', action='append', help='Username(s) to be filtered out.', required=False)
    parser.add_argument('-rd', '--remove-deleted', action='store_true', help='Remove comments with deleted or removed body.')
    parser.add_argument('-rq', '--remove-quotes', action='store_true', help='Remove quotes from comment body.')
    parser.add_argument('-rr', '--remove-remindme', action='store_true', help='Remove comments asking for RemindMeBot (at the beginning of a comment).')
    parser.add_argument('-ru', '--remove-urls', action='store_true', help='Remove URLs from comment body.')
    parser.add_argument('-log', '--log-file', default='removed_comments_log.txt', help='File to log removed comments and quotes.')

    args = parser.parse_args()

    authors_to_remove = [author.lower() for author in args.author] if args.author else []

    excluded_counts, deleted_count, quote_removal_count, remindme_count, url_removal_count, removed_url_only_comments_count = filter_comments(args.zst_file, authors_to_remove, args.remove_deleted, args.remove_quotes, args.remove_remindme, args.remove_urls, args.log_file)

    for name, count in excluded_counts.items():
        if count > 0:
            print(f"{count} comment(s) from '{name}' excluded.")

    if args.remove_deleted:
        print(f"{deleted_count} 'deleted/removed' comment(s) excluded.")
    
    if args.remove_quotes:
        print(f"{quote_removal_count} quotes removed from comments.")
    
    if args.remove_remindme:
        print(f"{remindme_count} comment(s) asking for RemindMeBot removed.")
    
    if args.remove_urls:
        print(f"{url_removal_count} URL(s) removed from comments.")
    
    print(f"{removed_url_only_comments_count} comment(s) removed for being only a URL.")

    print("Script executed successfully.")
    