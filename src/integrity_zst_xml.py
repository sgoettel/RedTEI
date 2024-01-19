import zstandard as zstd
import json
from lxml import etree as ET
import os
import io
import sys
# dictionary to store the comment count per link_id
def count_comments_in_zst_file(zst_file_path):
    comment_count_per_link_id = {}
    total_json_objects = 0  # Counter for total JSON objects
    with open(zst_file_path, 'rb') as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            for line in text_stream:
                try:
                    comment = json.loads(line)
                    link_id = comment['link_id'][3:]  # Remove 't3_' prefix
                    comment_count_per_link_id[link_id] = comment_count_per_link_id.get(link_id, 0) + 1
                    total_json_objects += 1  # Increment counter
                except json.JSONDecodeError:
                    continue  # Continue to next line if parsing fails
    return comment_count_per_link_id, total_json_objects

# dictionary to store the comment count per XML file
def count_comments_in_xml_files(xml_dir):
    comment_count_per_file = {}
    total_xml_items = 0  # Counter for total <item> in XML files
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]

    for xml_file in xml_files:
        file_path = os.path.join(xml_dir, xml_file)
        tree = ET.parse(file_path)
        root = tree.getroot()

        namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
        comments_list = root.xpath('.//tei:div[@type="comments"]/tei:list', namespaces=namespaces)
        for list_elem in comments_list:
            items_count = len(list_elem.xpath('.//tei:item', namespaces=namespaces))
            total_xml_items += items_count  # Increment counter
            comment_count_per_file[xml_file] = items_count

    return comment_count_per_file, total_xml_items

# Compare comment counts between the zst and XML
def compare_counts(zst_file_path, xml_dir):
    comment_count_per_link_id, total_json_objects = count_comments_in_zst_file(zst_file_path)
    comment_count_per_file, total_xml_items = count_comments_in_xml_files(xml_dir)
    discrepancies_found = False

    for link_id, count_zst in comment_count_per_link_id.items():
        xml_file_name = link_id + '.xml'
        count_xml = comment_count_per_file.get(xml_file_name, 0)

        if count_zst != count_xml:
            discrepancies_found = True
            print(f'Discrepancy found: {link_id} has {count_zst} comments in the zst file, but XML file {xml_file_name} has {count_xml} comments.')
    # Print discrepancies
    if discrepancies_found:
        print(f"Total {total_json_objects} JSON objects counted, {total_xml_items} <item> counted in all XML files.")
    else:
        print(f"All counts match. No discrepancies found. Total {total_json_objects} JSON objects counted, {total_xml_items} <item> counted in all XML files.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python integrity_zst_xml.py [path_to_zst_file] [path_to_xml_directory]")
        sys.exit(1)

    zst_file_path = sys.argv[1]
    xml_directory = sys.argv[2]
    compare_counts(zst_file_path, xml_directory)