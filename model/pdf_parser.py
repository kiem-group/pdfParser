import sys
from typing import List, Any
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno
from parser_config import ParserConfig
from dataclasses import dataclass
from dataclasses_json import dataclass_json
bib_config = ParserConfig()


@dataclass_json
@dataclass
class SkippedText:
    pos: int = None
    text: str = None


def parse_target_indent(in_file, config=bib_config):
    print(in_file.name)
    odd_offset_counter = {}
    even_offset_counter = {}
    odd_length = 0
    even_length = 0
    page_num: int = 0

    for page_layout in extract_pages(in_file):
        page_num += 1
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    try:
                        (x, y, w, h) = text_line.bbox
                        appr_x = round(x)
                        if page_num % 2 == 1:
                            odd_offset_counter[appr_x] = odd_offset_counter.get(appr_x, 0) + 1
                            if x + w > odd_length:
                                odd_length = x + h
                        else:
                            even_offset_counter[appr_x] = even_offset_counter.get(appr_x, 0) + 1
                            if x + w > even_length:
                                even_length = x + h
                    except:
                        print("Failed to get bbox", text_line)
    # Remove occasional lines - title, page numbers, etc. - anything that occurs a couple of times per page on average
    odd_starts = get_offset_counter(odd_offset_counter, page_num, config)
    even_starts = get_offset_counter(even_offset_counter, page_num, config)

    if len(odd_starts) > 2 or len(even_starts) > 2:
        print("\tWarning: multi-column or unusual format")
        print("odd line length: ", odd_length)
        print("odd starts:", odd_starts)
        print("even line length: ", even_length)

    page_num = 0
    items: List[List[Any]] = []
    skipped: List[SkippedText] = []

    def split_reference(line_chars, appr_x, curr_ref_chars, base):
        curr_stripped = convert_to_str(curr_ref_chars).strip()
        try:
            # print("Line starts at: ", appr_x)
            # print("Line: ", convert_to_str(line_chars))
            new_ref = appr_x == base and len(curr_ref_chars) > 0
            # A reference should not end with , or -
            if len(curr_stripped) > 1:
                if curr_stripped.endswith(',') or curr_stripped.endswith('–'):
                    # print("Reference can't end like this: ", curr_stripped[len(curr_stripped) - 1])
                    new_ref = False
            if new_ref:
                # print("REFERENCE: ", convert_to_str(curr_ref_chars))
                items.append(curr_ref_chars)
                return True  # My parser to decode string
            else:
                if base <= appr_x < base + config.indent:
                    curr_ref_chars.extend(line_chars)  # My parser to decode string
                # Record skipped text for method evaluation
                else:
                    # print("SKIPPED: ", curr_stripped)
                    skipped.append(SkippedText(len(items), convert_to_str(line_chars)))
        except:
            print("Failed to parse index text: ", curr_stripped)
            print(sys.exc_info()[0])
        return False

    # TODO odd_starts and even_starts should ahve the same number of columns, trim otherwise
    if len(odd_starts) != len(even_starts):
        print("Layout differs for odd and even pages!")

    n = min(len(odd_starts), len(even_starts))
    col_curr = [[]*n]
    for page_layout in extract_pages(in_file):
        page_num += 1
        starts = odd_starts if page_num % 2 == 1 else even_starts
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    try:
                        (x, y, w, h) = text_line.bbox
                        appr_x = round(x)
                        col_num = 0
                        for start in starts:
                            if appr_x >= start + config.indent:
                                col_num += 1
                        line_chars = get_text(text_line)
                        if col_num < n:
                            is_ref_added = split_reference(line_chars, appr_x, col_curr[col_num], starts[col_num])
                            if is_ref_added:
                                col_curr[col_num] = line_chars
                        else:
                            # Text outside the boundaries of the last column
                            # print("SKIPPED 2: ", convert_to_str(line_chars))
                            skipped.append(SkippedText(len(items), convert_to_str(line_chars)))
                    except:
                        print("Failed to get bbox", text_line)
            else:
                print("\tNon-text element", element)
    for curr in col_curr:
        if len(curr) > 0:
            items.append(curr)
    items = [item for item in items if config.min_length <= len(item) <= config.max_length]
    refs = []
    for item in items:
        refs.append(convert_to_str(item))
    in_file.close()
    return [refs, skipped]


def convert_to_str(item):
    def convert(char):
        if len(char) == 1:
            num = ord(char)
            if 63043 <= num <= 63052:
                return str(num - 63043)
        return char
    decoded_item = [convert(char) for char in item]
    return ''.join(decoded_item)


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
        if len(starts) == 0 or len(include) > len(starts) - 1:
            starts.append(key)
    if len(offset_counter) == len(starts):
        print("\tNo-indent formatting!")
    # print("Starts: ", starts)
    return starts


def get_table_of_content(path, password):
    fp = open(path, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser, password)
    outlines = document.get_outlines()
    for (level, title, dest, a, se) in outlines:
        print(level, title)
