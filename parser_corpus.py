from os import listdir
from os.path import isfile, join
import zipfile
import os
import sys
from typing import List, Any
from lxml import etree
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno
from parser_config import ParserConfig
from model.corpus import Corpus
from model.publication import Publication
import shutil
from index import get_index_types


def parse_target_indent(in_file, out_path, config):
    print(in_file.name)
    odd_offset_counter = {}
    even_offset_counter = {}
    page_num = 0

    # Use max 5 pages to analyze indentation
    for page_layout in extract_pages(in_file):
        page_num += 1
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    (x, y, w, h) = text_line.bbox
                    appr_x = round(x)
                    if page_num % 2 == 1:
                        odd_offset_counter[appr_x] = odd_offset_counter.get(appr_x, 0) + 1
                    else:
                        even_offset_counter[appr_x] = even_offset_counter.get(appr_x, 0) + 1
    # Remove occasional lines - title, page numbers, etc. - anything that occurs a couple of times per page on average
    odd_starts = get_offset_counter(odd_offset_counter, page_num, config)
    even_starts = get_offset_counter(even_offset_counter, page_num, config)

    if len(odd_starts) > 2 or len(even_starts) > 2:
        print("\tWarning: possibly unusual structure")

    page_num = 0
    items: List[List[Any]] = []
    curr_ref_chars = []
    for page_layout in extract_pages(in_file):
        page_num += 1
        # print("page_num", page_num)
        starts = odd_starts if page_num % 2 == 1 else even_starts
        base = starts[0]
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                # print(element.get_text())
                for text_line in element:
                    try:
                        (x, y, w, h) = text_line.bbox
                        appr_x = round(x)
                        if appr_x in starts and len(curr_ref_chars) > 0:
                            items.append(curr_ref_chars)
                            curr_ref_chars = get_text(text_line)  # My parser to decode string
                            # curr_ref_chars = [text_line.get_text()]
                            base = appr_x
                        else:
                            if appr_x < base + config.indent:
                                curr_ref_chars.extend(get_text(text_line))  # My parser to decode string
                                # curr_ref_chars.append(text_line.get_text())
                            else:
                                print("\tSkipped:", text_line.get_text())
                    except:
                        print(sys.exc_info()[0])
            else:
                print("\tNon-text element", element)
    if len(curr_ref_chars) > 0:
        print("".join(curr_ref_chars))
        items.append(curr_ref_chars)
    items = [item for item in items if config.min_length <= len(item) <= config.max_length]
    print("Extracted items: ", len(items))
    out_file = open(out_path, "w", encoding='utf-8')
    for item in items:
        for char in item:
            try:
                out_file.write(char)
            except:
                print(sys.exc_info()[0])
                print("\tFailed to write to file:", char)
        out_file.write("\n")
    out_file.close()
    in_file.close()


def get_text(text_line):
    char_list = []
    for char in text_line:
        if isinstance(char, LTChar) or isinstance(char, LTAnno):
            char_list.append(char.get_text())
    return char_list


def get_offset_counter(offset_counter, page_num, config):
    starts = []
    offset_counter = {k: v for k, v in offset_counter.items() if v > config.noise * page_num}
    for key in offset_counter:
        include = [el for el in starts if key > el + config.indent]
        if len(starts) == 0 or len(include) > 0:
            starts.append(key)
    if len(offset_counter) == len(starts):
        print("\tNo-indent formatting!")
    return starts


def get_table_of_content(path, password):
    fp = open(path, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser, password)
    outlines = document.get_outlines()
    for (level, title, dest, a, se) in outlines:
        print(level, title)


def parse_files(processor, config, jats_file, pub_zip, pub):
    jats_tree = etree.parse(jats_file)
    jats_root = jats_tree.getroot()
    book_parts = jats_root.xpath('//book-part')
    for book_part in book_parts:
        processor(book_part, config, pub_zip, pub)


def parse_bibliography_file(book_part, config, pub_zip, pub):
    title = ' '.join(book_part.xpath('.//title//text()')).lower()
    if 'bibliography' in title:
        href = book_part.xpath('.//self-uri/@xlink:href', namespaces={"xlink": "https://www.w3.org/1999/xlink"})[0]
        target_pdf = pub_zip.open(href)
        pub.bib_file = href
        output_txt_path = pub.zip_path if config.output_to_pub_dir else join(pub.corpus_dir_path, href)
        output_txt_path += "-bibliography.txt"
        print(output_txt_path)
        parse_target_indent(target_pdf, output_txt_path, config)


def parse_index_file(book_part, config, pub_zip, pub):
    title = ' '.join(book_part.xpath('.//title//text()')).lower()
    if 'index' in title:
        href = book_part.xpath('.//self-uri/@xlink:href', namespaces={"xlink": "https://www.w3.org/1999/xlink"})[0]
        target_pdf = pub_zip.open(href)

        # Modify output_txt_path to put target files of the same type to a dedicated folder
        pub.index_files.append(href)
        curr_index_types = get_index_types(title)
        pub.index_types.append(curr_index_types)
        ext = "-" + str(len(pub.index_files)) + "_" + ('-'.join(curr_index_types))
        output_txt_path = join(pub.corpus_dir_path, pub.dir_name + ext + ".txt")
        # Copy original pdf file for analysis
        output_pdf_path = join(pub.corpus_dir_path, pub.dir_name + ext + ".pdf")
        with open(output_pdf_path, 'wb') as f_dest:
            shutil.copyfileobj(target_pdf, f_dest)
        parse_target_indent(target_pdf, output_txt_path, config)


def parse_corpus(my_path):
    zip_arr = [f for f in listdir(my_path) if isfile(join(my_path, f))]
    bib_config = ParserConfig()
    for corpus_zip_name in zip_arr:
        # Corpus object that contains information about all publications
        corpus = Corpus(zip_path=corpus_zip_name, publications=[])

        corpus_zip = zipfile.ZipFile(join(my_path, corpus_zip_name))
        corpus_zip_path = join(my_path, corpus_zip_name)
        corpus_dir_path = os.path.splitext(corpus_zip_path)[0]
        for pub_zip_name in corpus_zip.namelist():
            pub_dir_name = os.path.splitext(pub_zip_name)[0]
            pub_dir_path = join(corpus_dir_path, pub_dir_name)
            corpus_zip.extract(pub_zip_name, pub_dir_path)
            pub_zip_path = join(pub_dir_path, pub_zip_name)

            # Publication object that contains info about publication data (e.g., file names, index types etc.)
            pub = Publication(pub_zip_path)

            # TODO: move this to Publication
            pub_zip = zipfile.ZipFile(pub_zip_path, 'r')
            for file_name in pub.files:
                if file_name.endswith('.xml'):
                    jats_file = pub_zip.open(file_name)
                    try:
                        parse_files(parse_bibliography_file, bib_config, jats_file, pub_zip, pub)
                        parse_files(parse_index_file, bib_config, jats_file, pub_zip, pub)
                    except:
                        corpus.xml_parsing_errors += 1
                        print(sys.exc_info()[0])
                    jats_file.close()
                    corpus.index_count += len(pub.index_files)
                    corpus.bibliography_count += 0 if pub.bib_file is None else 1
            pub_zip.close()
            #

            corpus.publications.append(pub)
            try:
                os.remove(pub_zip_path)
                os.rmdir(pub_dir_path)
            except:
                corpus.other_errors += 1
                # print("Other error", sys.exc_info()[0])
            print(pub)