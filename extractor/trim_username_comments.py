"""
Filter out specific authors/bots, deleted or removed comments,
all kind of quotations and URLs, and RemindMeBot calls

Author: Sebastian Göttel, 2024, script based on:
https://github.com/sgoettel/zstsidescripts/blob/main/trim_username_comments.py
"""

import json
import zstandard as zstd
import os
import re

CHUNK_SIZE = 16384

# regex for both URL types
plain_url_regex = re.compile(r'(?<!\])\b(?:https?://|www\.)\S+\b/?',
                             re.IGNORECASE)
markdown_url_regex = re.compile(r'\[([^\]]+)\]\((https?://|www\.)\S+\)')

# regex for zero-width spaces
zero_width_space_regex = re.compile(r'(&amp;#x200B;|&#x200B;|\\u200B)')

# regex for reducing multiple newlines to a single one
newline_regex = re.compile(r'\n\s*\n+')

# regex for inline formatting
# matches text enclosed in ~~ including the tildes
strike_through_regex = re.compile(r"~~(.*?)~~")
# matches text surrounded by **, without adjacent spaces
bold_text_regex = re.compile(r"\*\*(?!\s)(.*?)(?<!\s)\*\*")
# matches text surrounded by *, without adjacent spaces
italic_text_regex = re.compile(r"\*(?!\s)(.*?)(?<!\s)\*")


def read_bot_list(config_dir='src/config'):
    bot_file_path = os.path.join(config_dir, 'botlist.txt')
    bot_file_path = os.path.normpath(bot_file_path)  # normalize path
    with open(bot_file_path, 'r') as file:
        bots = [line.strip().lower() for line in file.readlines()
                if line.strip()]
    return bots


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


def remove_inline_formatting(text):
    # remove ~~strikethrough~~ txt completely, including content between tildes
    text = strike_through_regex.sub('', text)
    # remove double asterisks surrounding **bold text**,
    # preserving the text itself
    text = bold_text_regex.sub(r'\1', text)
    # Remove single asterisks surrounding *italic text*,
    # preserving the text itself
    text = italic_text_regex.sub(r'\1', text)
    return text


def is_comment_empty(comment_body):
    # check if comment body is empty
    return not comment_body.strip()


def filter_comments(zst_file, authors, remove_deleted, remove_quotes,
                    remove_remindme, remove_urls, log_file):
    dctx = zstd.ZstdDecompressor()
    cctx = zstd.ZstdCompressor(level=15)

    # pre 2023 quotation: matches a citation marker at the start of a line or
    # text, capturing everything up to the next citation marker, newline,
    # or end of text
    quote_regex = re.compile(r"(?:\n|^)(&gt;.*?)(?=(\n&gt;)|\n|$)")

    # onwards 2023 quotation
    modern_quote_regex = re.compile(r"(?:\n|^)>[^\n]+(\n>[^\n]*)*")

    # catches various ways users try to summon the RemindMeBot, even though
    # there's technically just one right way to do it..it can vary..
    remindme_regex = re.compile(r'^\s*(!remindme|!RemindMe|!remind me|RemindMe!|Remind me!)\b', re.IGNORECASE)

    input_filename = zst_file
    output_filename = f"{zst_file.rsplit('.', 1)[0]}_filtered.zst"
    log_filename = log_file

    excluded_counts = {author.lower(): 0 for author in authors} \
        if authors else {}
    deleted_count = 0
    removed_url_only_comments_count = 0
    quote_removal_count = 0
    remindme_count = 0
    url_removal_count = 0

    with open(input_filename, 'rb') as fh, \
            open(output_filename, 'wb') as ofh, \
            open(log_filename, 'w') as lf:
        lf.write("Logfile initiated.\n")
        with dctx.stream_reader(fh) as reader, \
                cctx.stream_writer(ofh) as writer:
            buffer = ""
            deleted_tags = ["[removed]", "[deleted]", "[removed by reddit]"]

            while True:
                chunk = reader.read(CHUNK_SIZE)
                if not chunk:
                    break

                buffer += chunk.decode(errors='ignore')

                # initialize last_modified_body for every new chunk
                last_modified_body = None

                while True:
                    position = buffer.find('\n')

                    if position == -1:
                        break

                    line = buffer[:position]
                    buffer = buffer[position + 1:]

                    # apply inline-formatting removals
                    line = remove_inline_formatting(line)

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
                            # skip further processing for this comment
                            continue

                        # check and remove deleted or removed comments
                        if remove_deleted \
                                and obj["body"].strip() in deleted_tags:
                            deleted_count += 1
                            # log the removal
                            lf.write("\n=========== body: deleted/removed ==========\n")
                            lf.write(json.dumps({
                                "original": original_body,
                                "deleted_comment": obj})
                                + "\n")
                            continue

                        # check if body-text is just plaintext URL
                        if remove_urls and \
                                plain_url_regex.fullmatch(obj["body"].strip()):
                            removed_url_only_comments_count += 1
                            # log the removal
                            lf.write("\n=========== body: removed due to being only a URL ==========\n")
                            lf.write(json.dumps({"original": original_body})
                                     + "\n")
                            continue

                        # remove quotations
                        if remove_quotes:
                            cleaned_body_before_strip = re.sub(quote_regex,
                                                               '', obj["body"])
                            cleaned_body_after_strip = \
                                re.sub(modern_quote_regex, '',
                                       cleaned_body_before_strip).strip()

                            # check if significant changes were made, besides removing whitespace
                            substantial_change_made = \
                                (cleaned_body_before_strip.strip()
                                 != obj["body"].strip()) or \
                                (cleaned_body_after_strip !=
                                    cleaned_body_before_strip.strip())

                            if substantial_change_made:
                                obj["body"] = cleaned_body_after_strip
                                quote_removal_count += 1
                                quote_changed = True
                                body_changed = True

                        # remove URLs
                        if remove_urls:
                            # count URLs in comments
                            original_plain_url_count = \
                                len(plain_url_regex.findall(obj["body"]))
                            original_markdown_url_count = \
                                len(markdown_url_regex.findall(obj["body"]))

                            # for markdown URLs
                            new_body_markdown_urls_removed = \
                                remove_markdown_urls(obj["body"])
                            # for plain URLs
                            new_body_plain_urls_removed = \
                                remove_plain_urls(new_body_markdown_urls_removed)

                            if new_body_plain_urls_removed != obj["body"]:
                                obj["body"] = new_body_plain_urls_removed
                                body_changed = True
                                url_changed = True

                                # count URLs after processing
                                new_plain_url_count = \
                                    len(plain_url_regex.findall(obj["body"]))
                                new_markdown_url_count = \
                                    len(markdown_url_regex.findall(obj["body"]))

                                # count number of processed URLs and add to url_removal_count
                                urls_removed = (original_plain_url_count - new_plain_url_count) \
                                    + (original_markdown_url_count - new_markdown_url_count)
                                url_removal_count += urls_removed

                                cleaned_body = obj["body"].strip()
                                # match strings consisting only of "[URL]"
                                # followed by any combination of
                                # "!", "?", ".", spaces, or newlines,
                                # repeated any number of times

                                if not cleaned_body or re.fullmatch(r'(\[URL\]([!?\.])*[\s\n]*)+', cleaned_body):
                                    # log comment and skip writing in output data
                                    lf.write("\n=========== body: only [URL] placeholders ==========\n")
                                    lf.write(json.dumps({"original": original_body}) + "\n")
                                    continue  # skip comment

                        # remove RemindMe bot invocations
                        if remove_remindme and remindme_regex.search(obj["body"]):
                            remindme_count += 1
                            lf.write("\n=========== body: !remindme ==========\n")
                            lf.write(json.dumps({"original": obj["body"]}) + "\n")
                            continue

                        # remove all Zero-Width Spaces and reduce multiple
                        # newlines down to a single one
                        # this is done for all comments,
                        # regardless of other modifications
                        obj["body"] = zero_width_space_regex.sub('', obj["body"])
                        obj["body"] = newline_regex.sub('\n', obj["body"])

                        if body_changed:  # check if we got any modifications
                            # only log if applicable
                            if last_modified_body != obj["body"]:
                                # refresh last_modified_body
                                last_modified_body = obj["body"]

                                # logging the changes if there are any
                                if quote_changed:
                                    lf.write("\n=========== body: contained quotation ==========\n")
                                    lf.write(json.dumps({"original": original_body}) + "\n\n")
                                    lf.write(json.dumps({"modified": obj["body"]}) + "\n")
                                if url_changed:
                                    lf.write("\n=========== body: URL (any type) ==========\n")
                                    lf.write(json.dumps({"original": original_body}) + "\n\n")
                                    lf.write(json.dumps({"modified": obj["body"]}) + "\n")

                        # check if the comment is empty after all modifications
                        # and cleaning
                        if is_comment_empty(obj["body"]):
                            # logging empty and ignored comments
                            lf.write("\n=========== body: empty or whitespace only ==========\n")
                            lf.write(json.dumps({"original": original_body}) + "\n")
                            # skip writing this comment to the output file
                            continue

                        # writing the updated comment back to the output file
                        writer.write(json.dumps(obj).encode() + b"\n")

                    except json.JSONDecodeError:
                        continue

    return excluded_counts, deleted_count, quote_removal_count, \
        remindme_count, url_removal_count, removed_url_only_comments_count


def process_comments(zst_file, remove_deleted=False, remove_quotes=False,
                     remove_remindme=False, remove_urls=False):
    # read botlist
    authors = read_bot_list()
    # extract file name and path
    input_filename_without_path = os.path.basename(zst_file)
    input_filename_without_extension = \
        input_filename_without_path.rsplit('.', 1)[0]
    log_filename = f"filtered_log_{input_filename_without_extension}.txt"

    excluded_counts, deleted_count, quote_removal_count, remindme_count, \
        url_removal_count, removed_url_only_comments_count = \
        filter_comments(zst_file, authors, remove_deleted, remove_quotes,
                        remove_remindme, remove_urls, log_filename)

    for name, count in excluded_counts.items():
        if count > 0:
            print(f"{count} comment(s) from '{name}' excluded.")

    if remove_deleted:
        print(f"{deleted_count} 'deleted/removed' comment(s) excluded.")

    if remove_quotes:
        print(f"{quote_removal_count} quote(s) removed from comments.")

    if remove_remindme:
        print(f"{remindme_count} comment(s) asking for RemindMeBot removed.")

    if remove_urls:
        print(f"{url_removal_count} URL(s) removed from comments.")

    print(f"{removed_url_only_comments_count} comment(s) removed for being only a URL.")

    print("Script executed successfully.")
