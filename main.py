from os import listdir
from os.path import isfile, join
import zipfile
import os
import logging as log
import sys
from lxml import etree
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTAnno


# Guess type of index. Can return several types
# verborum - index of words
# locorum  - index of references
# nominum  - index of names
   # nominum_ancient - ancient people
   # nominum_modern  - modern authors
# rerum    - index of subjects
# geographicus - index of places
def get_index_types(index_title):
    keywords = {
        'verborum': ['general', 'verborum', 'verborvm', 'abstract', 'word', 'words', 'term', 'terms', 'termes', 'wort', 'sachindex', 'général', 'generalis', 'mots'],
        'locorum': ['locorum', 'loco', 'rum', 'locorvm', 'biblical', 'non-biblical', 'quran', 'biblicum',
                    'citation', 'citations', 'quotation', 'quotations', 'source', 'sources', 'reference', 'references',
                    'scripture', 'scriptures',  'verse', 'verses', 'passage', 'passages', 'line', 'lines', 'cited', 'textes', 'cités', 'papyri', 'fragmentorum'],
        'nominum_ancient': ['nominum', 'nominvm', 'propriorvm', 'name', 'names',
                            'proper', 'person', 'persons', 'personal', 'people', 'writer', 'writers', 'poet', 'poets',
                            'author', 'authors',
                            'ancient', 'antique', 'classical', "medieval", 'greek', 'egyptian', 'latin',
                            'auteur', 'auteurs', 'anciens',
                            'eigennamen', 'noms', 'propres', 'personnages'],
        'nominum_modern': ['modern', 'author', 'authors', 'editor', 'editors', 'scholar', 'scholars', 'auteur', 'auteurs', 'modernes'],
        'rerum': ['rerum', 'rervm', 'subject', 'subjects', 'theme', 'themes', 'topic', 'topics', 'thématique', 'thematic'],
        'geographicus': ['geographicus', 'geographic', 'geographical', 'géographique', 'place', 'places', 'location', 'locations', 'site', 'sites', 'topographical'],
        'bibliographicus': ['bibliographicus', 'bibliographique', 'bibliographical', 'bibliographic', 'manuscript', 'manuscripts', 'collections', 'ventes'],
        'museum': ['museum', 'museums', 'meseums', 'musées', 'collections'],
        'epigraphic': ['epigraphic', 'epigraphical', 'inscriptionum', 'inscriptions']
    }
    # exclude_keywords ?

    index_terms = [term for term in index_title.split(" ") if len(term.strip()) > 3]
    if len(index_terms) == 1:
        return ['verborum']
    hits = {}
    max_hit = 0
    for term in index_terms:
        for key in keywords.keys():
            for keyword in keywords[key]:
                if keyword == term:
                    hits[key] = hits.get(key, 0) + 1
                    if hits[key] > max_hit:
                        max_hit = hits[key]
    if not bool(hits.keys()):
        print(index_title)
        return ['unknown']
    # return hits.keys()
    return [k for k, v in hits.items() if v == max_hit]

    # index of very specific stuff
    # 'index of scribal errors'
    # 'index of verse-end corruptions'
    # 'index of verse-end borrowings'
    # 'index of grammatical topics'
    # 'index of greek words'


def parse_target(in_file, out_path, stats):
    output_string = StringIO()
    parser = PDFParser(in_file)
    doc = PDFDocument(parser)
    rsrc_mgr = PDFResourceManager()
    device = TextConverter(rsrc_mgr, output_string, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrc_mgr, device)
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)
    output = output_string.getvalue()
    lines = output.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    out_file = open(out_path, "w")
    try:
        for line in non_empty_lines:
            out_file.write(line+"\n\n")
    except:
        # print("Output error", sys.exc_info()[0])
        stats["output_errors"] += 1
    in_file.close()
    out_file.close()


def parse_ref_pages():
    ref_pages = []
    # single, range, page ith location
    return ref_pages


INDENT = 150  # Allowed offset from the start of the reference on the next line
NOISE = 3  # Number of elements per page which are not references or indices (e.g., title, subtitle, page, footnote)
REF_MIN_LENGTH = 10  # Minimal length of the reference
REF_MAX_LENGTH = 300 # Maximal length of the reference


def parse_target_indent(in_file, out_path):
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
    odd_starts = get_offset_counter(odd_offset_counter, page_num)
    even_starts = get_offset_counter(even_offset_counter, page_num)

    if len(odd_starts) > 2 or len(even_starts) > 2:
        print("\tWarning: possibly unusual structure")

    page_num = 0
    items = []
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
                            curr_ref_chars = get_text(text_line)  # My parser to decode unicode
                            # curr_ref_chars = [text_line.get_text()]
                            base = appr_x
                        else:
                            if appr_x < base + INDENT:
                                curr_ref_chars.extend(get_text(text_line))  # My parser to decode unicode
                                # curr_ref_chars.append(text_line.get_text())
                            else:
                               print("\tSkipped:", text_line.get_text())
                    except:
                        print(sys.exc_info()[0])
            else:
                print("\tNon-text element", element)
    print("Done!")
    if len(curr_ref_chars) > 0:
        items.append(curr_ref_chars)
    items = [item for item in items if REF_MIN_LENGTH <= len(item) <= REF_MAX_LENGTH]
    out_file = open(out_path, "w", encoding='utf-8')
    for item in items:
        ref = u''.join(item)
        out_file.write(ref+'\n')
        # for char in item:
        #     try:
        #         out_file.write(char)
        #     except:
        #         print(sys.exc_info()[0])
        #         print("\tFailed to write to file:", char)
        # out_file.write('\n')
    out_file.close()
    in_file.close()


def get_text(text_line):
    char_list = []
    for char in text_line:
        if isinstance(char, LTChar) or isinstance(char, LTAnno):
            char_list.append(char.get_text())
    return char_list


def get_offset_counter(offset_counter, page_num):
    starts = []
    offset_counter = {k: v for k, v in offset_counter.items() if v > NOISE * page_num}
    for key in offset_counter:
        include = [el for el in starts if key > el + INDENT]
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


def get_stats(mypath):
    stats = {"index_count": 0, "bibliography_count": 0, "xml_parsing_errors": 0, "output_errors": 0, "other_errors": 0}
    zip_arr = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for corpus_zip_name in zip_arr:
        corpus_zip = zipfile.ZipFile(join(mypath, corpus_zip_name))
        corpus_zip_path = join(mypath, corpus_zip_name)
        corpus_dir_path = os.path.splitext(corpus_zip_path)[0]
        # corpus_zip.extractall(corpus_dir_path)
        # print(corpus_zip.namelist())
        index_types = {}
        count = 0
        for pub_zip_name in corpus_zip.namelist():
            # pub_file_path = join(corpus_zip_path, pub_zip_name)
            pub_dir_path = os.path.splitext(join(corpus_dir_path, pub_zip_name))[0]
            corpus_zip.extract(pub_zip_name, pub_dir_path)
            pub_zip_path = join(pub_dir_path, pub_zip_name)
            pub_zip = zipfile.ZipFile(pub_zip_path, 'r')
            # Get a list of all archived file names from zip
            list_file_names = pub_zip.namelist()
            # Iterate over the file names
            count += 1
            for file_name in list_file_names:
                if file_name.endswith('.xml'):
                    # Extract a single file from zip
                    # pub_zip.extract(file_name, join(corpus_dir_path, 'temp_xml'))
                    jats_file = pub_zip.open(file_name)
                    try:
                        jats_tree = etree.parse(jats_file)
                        jats_root = jats_tree.getroot()
                        book_parts = jats_root.xpath('//book-part')
                        pub_index_count = 0
                        for book_part in book_parts:
                            title = ' '.join(book_part.xpath('.//title//text()')).lower()
                            if any(word in title for word in ['index', 'bibliography']):
                                href = book_part.xpath('.//self-uri/@xlink:href',
                                                       namespaces={"xlink": "http://www.w3.org/1999/xlink"})[0]
                                target_pdf = pub_zip.open(href)
                                # Modify output_txt_path to put target files of the same type to a dedicated folder
                                if 'index' in title:
                                    stats["index_count"] += 1
                                    pub_index_count += 1
                                    curr_index_types = get_index_types(title)
                                    for type_name in curr_index_types:
                                        index_types[type_name] = index_types.get(type_name, 0) + 1
                                    ext = "-" + str(pub_index_count) + "_" + ('-'.join(curr_index_types))
                                    output_txt_path = pub_dir_path + ext + ".txt"
                                else:
                                    # if 'bibliography' in title:
                                    stats["bibliography_count"] += 1
                                    output_txt_path = pub_dir_path + "-bibliography.txt"
                                    # parse_target(target_pdf, output_txt_path, stats)
                                    parse_target_indent(target_pdf, output_txt_path)
                                # parse_target(target_pdf, output_txt_path, stats)
                    except:
                        stats["xml_parsing_errors"] += 1
                        # print(sys.exc_info()[0])
                    jats_file.close()
            pub_zip.close()
            try:
                os.remove(pub_zip_path)
                os.rmdir(pub_dir_path)
            except:
                stats["other_errors"] += 1
                # print("Other error", sys.exc_info()[0])
        print(index_types)
    print(count)
    for item in stats.items():
        print(item)


if __name__ == '__main__':
    get_stats('data')

