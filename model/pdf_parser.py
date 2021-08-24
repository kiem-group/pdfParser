import sys
from typing import List, Any
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno
from parser_config import ParserConfig
bib_config = ParserConfig()


def parse_target_indent(in_file, config=bib_config):
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
                for text_line in element:
                    try:
                        (x, y, w, h) = text_line.bbox
                        appr_x = round(x)
                        if appr_x in starts and len(curr_ref_chars) > 0:
                            items.append(curr_ref_chars)
                            curr_ref_chars = get_text(text_line)  # My parser to decode string
                            base = appr_x
                        else:
                            if appr_x < base + config.indent:
                                curr_ref_chars.extend(get_text(text_line))  # My parser to decode string
                            # TODO record skipped text for method evaluation
                            # else:
                            #     print("\tSkipped:", get_text(text_line))
                    except:
                        print(sys.exc_info()[0])
            else:
                print("\tNon-text element", element)
    if len(curr_ref_chars) > 0:
        # print("".join(curr_ref_chars))
        items.append(curr_ref_chars)
    items = [item for item in items if config.min_length <= len(item) <= config.max_length]
    refs = []

    def convert(char):
        if len(char) == 1:
            num = ord(char)
            if 63043 <= num <= 63052:
                return str(num - 63043)
        return char

    for item in items:
        decoded_item = [convert(char) for char in item]
        ref = ''.join(decoded_item)
        refs.append(ref)
    in_file.close()
    return refs


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
