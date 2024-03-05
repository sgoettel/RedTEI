import argparse
import lzma
import os
from pickle import load as load_pickle
import sys

from lxml import etree


def load_schema(TEI_SCHEMA ='../tei-schema-pickle.lzma'):
    if not os.path.exists(TEI_SCHEMA):
        # download schema from trafilatura
        os.system(f'wget -O {TEI_SCHEMA} https://github.com/adbar/trafilatura/raw/d31c8d74b08785c7e297d36449fd8869b49b6f1f/trafilatura/data/tei-schema-pickle.lzma')
    with lzma.open(TEI_SCHEMA, 'rb') as schemafile:
        schema_data = load_pickle(schemafile)
    TEI_RELAXNG = etree.RelaxNG(etree.fromstring(schema_data))
    return TEI_RELAXNG


def validate(path, TEI_RELAXNG):
    xmldoc = etree.parse(path)
    result = TEI_RELAXNG.validate(xmldoc)
    if result is False:
        print('not a valid TEI document: %s', TEI_RELAXNG.error_log)
        print(path, result)
    return result


def validate_directory(directory, TEI_RELAXNG):
    pathlist = [f'{directory}/{path}' for path in os.listdir(directory)
                    if path.endswith('.xml')]
    for path in pathlist:
        validate(path, TEI_RELAXNG)


if __name__ == '__main__':
    # usage: python validate.py [directory] [tei_schema(optional)]
    directory = sys.argv[1]
    if len(sys.argv) > 2:
        TEI_RELAXNG = load_schema(sys.argv[2])
    else:
        TEI_RELAXNG = load_schema()
    validate_directory(directory, TEI_RELAXNG)
    