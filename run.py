import argparse
import os

from collections import defaultdict
from multiprocessing import Pool

from extractor.comment_tree import extract_comments
from extractor.comment_processing import process_comment_batch, process_thread_batch
from extractor.json2xml import pipeline_json2xml
from extractor.trim_username_comments import process_comments
from extractor.utils import compare_json_counts, make_chunks
from extractor.validate import validate_directory


NUM_PROCESSES = max(os.cpu_count(), 32)
CHUNK_SIZE = 100  # batch size


def run_multi_process(func, iterator, json_dir, xml_dir):
    "Run multiprocessing in batches."
    batches = make_chunks(iterator, CHUNK_SIZE)
    with Pool(processes=NUM_PROCESSES) as pool:
        pool.starmap(
            func,
            [(batch, json_dir, xml_dir) for batch in batches],
        )


def pipeline(zstfile, subreddit, no_group=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subreddits_dir = os.path.join(base_dir, "subreddits")
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

    # process comments in zst file (apply filters)
    print(f"Filtering comments in {subreddit}...")
    process_comments(
        zstfile,
        remove_deleted=True,
        remove_quotes=True,
        remove_remindme=True,
        remove_urls=True,
    )

    filtered_zst_path = f"{zstfile.rsplit('.', 1)[0]}_filtered.zst"

    print(f"Extracting comments from {filtered_zst_path}. This may take a while...")

    # process based on mode
    if no_group:
        print("Processing comments in 'no-group' mode...")
        run_multi_process(
            process_comment_batch,
            extract_comments(filtered_zst_path),
            json_output_dir,
            xml_output_dir,
        )
    else:
        thread_comments = defaultdict(list)

        for comment in extract_comments(filtered_zst_path):
            thread_id = comment.get("link_id", "").replace("t3_", "")
            thread_comments[thread_id].append(comment)

        print(f"Processing {len(thread_comments)} threads in 'grouped' mode...")
        run_multi_process(
            process_thread_batch,
            thread_comments.items(),
            json_output_dir,
            xml_output_dir,
        )

    print("Validating XML files...")
    validate_directory(xml_output_dir)

    # JSON object count consistency between filtered zst file and JSON output directory
    filtered_zst_path = f"{zstfile.rsplit('.', 1)[0]}_filtered.zst"
    print(
        "Checking consistency of JSON object (comments) count between the filtered .zst file and JSON output directory..."
    )
    compare_json_counts(filtered_zst_path, json_output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Reddit comments.")
    parser.add_argument(
        "files", nargs="+", help="Path to one or more .zst files or _json directories."
    )
    parser.add_argument(
        "--no-group", action="store_true", help="Process each comment individually."
    )
    args = parser.parse_args()
    for inputfile in args.files:
        if inputfile.endswith(".zst"):
            subreddit = inputfile.split("/")[-1].replace("_comments.zst", "")
            pipeline(inputfile, subreddit, no_group=args.no_group)
        elif inputfile.endswith("_json") or inputfile.endswith("_json/"):
            pipeline_json2xml(inputfile)
        else:
            print(
                "Please provide the path to one or more .zst files or _json directories."
            )
