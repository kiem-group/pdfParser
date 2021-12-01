import sys
from typing import List, Any
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass
class ParserConfig:
    """A class that defines parameters for indentation-based PDF parser"""
    indent: int = 100      # Maximal horizontal offset to consider the next line a continuation of the previous
    noise: int = 1         # Minimal threshold on lines with certain indentation. Helps to exclude non-references
    min_length: int = 30   # Minimal length of the reference or index term, to exclude page numbers, titles, etc.
    max_length: int = 300  # Maximal length of the reference or index term, to exclude article content
    min_words: int = 3     # Minimal number of words in reference or index (currently not used)
    max_words: int = 100   # Maximal number of words in reference or index (currently not used)


bib_config = ParserConfig()


@dataclass_json
@dataclass
class SkippedText:
    pos: int = None
    text: str = None


@dataclass_json
@dataclass
class PdfParser:

    @classmethod
    def get_table_of_content(cls, path, password):
        fp = open(path, 'rb')
        parser = PDFParser(fp)
        document = PDFDocument(parser, password)
        outlines = document.get_outlines()
        content = {}
        for (level, title, dest, a, se) in outlines:
            content[level] = title
        return content

    @classmethod
    def parse_target_indent(cls, in_file, config=bib_config):
        odd_offset_counter = {}
        even_offset_counter = {}
        # TODO use length of line in parser
        odd_length = 0
        even_length = 0
        page_num: int = 0
        count_last_dot = 0

        def get_line_offset(el):
            nonlocal odd_length, even_length
            (x, y, w, h) = el
            appr_x = round(x)
            if page_num % 2 == 1:
                odd_offset_counter[appr_x] = odd_offset_counter.get(appr_x, 0) + 1
                if x + w > odd_length:
                    odd_length = x + w
            else:
                even_offset_counter[appr_x] = even_offset_counter.get(appr_x, 0) + 1
                if x + w > even_length:
                    even_length = x + w

        for page_layout in extract_pages(in_file):
            page_num += 1
            # for element in page_layout:
            for idx, element in enumerate(page_layout):
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        # Probing first 500 lines:
                        #   if at least 100 of them end with a dot, we assume all lines must end with a dot.
                        if idx < 500 and count_last_dot <= 100:
                            line_chars = cls.__get_text(text_line)
                            if line_chars[-2] == '.':
                                count_last_dot += 1
                        try:
                            get_line_offset(text_line.bbox)
                        except:
                            print("Failed to get bbox", text_line)

        # Remove occasional lines - title, page numbers, etc. - anything that occurs a couple of times per page on average
        odd_starts = cls.__get_offset_counter(odd_offset_counter, page_num, config)
        even_starts = cls.__get_offset_counter(even_offset_counter, page_num, config)

        if len(odd_starts) > 2 or len(even_starts) > 2:
            print("\tWarning: multi-column or unusual format")
            print("\t\todd starts:", odd_starts)
            print("\t\teven starts:", even_starts)

        page_num = 0
        items: List[List[Any]] = []
        skipped: List[SkippedText] = []
        incomplete = []

        def split_reference(line_chars, appr_x, curr_ref_chars, base):
            curr_stripped = cls.__convert_to_str(curr_ref_chars).strip()
            try:
                new_ref = appr_x == base and len(curr_stripped) > 0
                # A reference should not end with , or -
                if new_ref:
                    if count_last_dot >= 100:
                        # Line must end with a dot but it does not
                        if not curr_stripped.endswith('.'):
                            incomplete.append(len(items))
                    else:
                        # Line looks unfinished
                        if curr_stripped.endswith(',') or curr_stripped.endswith('–'):
                            # print("Reference can't end like this: ", curr_stripped[-1])
                            incomplete.append(len(items))
                if new_ref:
                    # print("REFERENCE: ", convert_to_str(curr_ref_chars))
                    items.append(curr_ref_chars)
                    return True  # My parser to decode string
                else:
                    # print(base, "<=", appr_x, "<", base + config.indent)
                    if base <= appr_x < base + config.indent:
                        if len(incomplete) > 0:
                            idx = incomplete.pop(0)
                            items[idx].extend(line_chars)
                        else:
                            curr_ref_chars.extend(line_chars)  # My parser to decode string
                    # Record skipped text for method evaluation
                    else:
                        skipped.append(SkippedText(len(items), cls.__convert_to_str(line_chars)))
            except:
                print("Failed to parse index text: ", curr_stripped)
                print(sys.exc_info()[0])
            return False

        # TODO odd_starts and even_starts should ahve the same number of columns, trim otherwise
        if len(odd_starts) != len(even_starts):
            print("Layout differs for odd and even pages!")

        n = min(len(odd_starts), len(even_starts))
        col_curr = []
        for i in range(n):
            col_curr.append([])
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
                            line_chars = cls.__get_text(text_line)
                            # print("NEXT LINE:", convert_to_str(line_chars))
                            try:
                                if col_num < n and col_num < len(col_curr):
                                    is_ref_added = split_reference(line_chars, appr_x, col_curr[col_num], starts[col_num])
                                    if is_ref_added:
                                        col_curr[col_num] = line_chars
                                else:
                                    # print("SKIPPING: ", convert_to_str(line_chars))
                                    skipped.append(SkippedText(len(items), cls.__convert_to_str(line_chars)))
                            except:
                                print("Failed to process line", cls.__convert_to_str(line_chars))
                        except:
                             print("Failed to get bbox", text_line)
                # else:
                    # print("\tNon-text element", element)
        for curr in col_curr:
            if len(curr) > 0:
                items.append(curr)
        items = [item for item in items if config.min_length <= len(item) <= config.max_length]
        refs = []
        for item in items:
            refs.append(cls.__convert_to_str(item))
        in_file.close()
        return [refs, skipped]

    @classmethod
    def __convert_to_str(cls, item):
        def convert(char):
            if len(char) == 1:
                num = ord(char)
                if 63043 <= num <= 63052:
                    return str(num - 63043)
            return char
        decoded_item = [convert(char) for char in item]
        return ''.join(decoded_item)

    @classmethod
    def __get_text(cls, text_line):
        char_list = []
        for char in text_line:
            if isinstance(char, LTChar) or isinstance(char, LTAnno):
                char_list.append(char.get_text())
                # if 'Bold' in char.fontname:
                #     print("Bold", char.get_text())
        return char_list

    @classmethod
    def __get_offset_counter(cls, offset_counter, page_num, config):
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

