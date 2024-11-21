import os
import sys

from lxml import etree

SOURCE_DIR = os.path.abspath(os.path.dirname(__file__))
TEI_DTD = etree.DTD(os.path.join(SOURCE_DIR, "tei_corpus.dtd"))


def validate(path):
    xmldoc = etree.parse(path)
    result = TEI_DTD.validate(xmldoc)
    if result is False:
        print("not a valid TEI document: %s", TEI_DTD.error_log.last_error)
        print(path, result)
    return result


def validate_directory(directory):
    """validates all XML files in the directory and subdirectories recursively."""
    for root, _, files in os.walk(
        directory
    ):  # all directories and subdirectories recursively
        for filename in files:
            path = os.path.join(root, filename)
            # only validate XML files
            if path.endswith(".xml") and os.path.getsize(path) > 0:
                try:
                    validate(path)
                except etree.XMLSyntaxError as e:
                    print(f"Syntax error in file {path}: {e}")
            else:
                print(f"Skipping invalid or empty file: {path}")


if __name__ == "__main__":
    # usage: python validate.py [directory] [tei_dtd(optional)]
    directory = sys.argv[1]
    if len(sys.argv) > 2:
        TEI_DTD = etree.DTD(sys.argv[2])
    validate_directory(directory)
