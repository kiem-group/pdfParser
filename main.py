from os import listdir
from os.path import isfile, join
import zipfile
import os
import sys
from lxml import etree
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTChar


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


def parse_index(in_file, out_path, stats):
    try:
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
        # print(out_path)
        out_file = open(out_path, "w")
        try:
            for line in non_empty_lines:
                out_file.write(line+"\n")
                # record = [entry for entry in line.split(",") if entry.strip() != ""]
        except:
            e = sys.exc_info()[0]
            # print("Output error", e)
            stats["output_errors"] += 1
        in_file.close()
        out_file.close()
    except:
        e = sys.exc_info()[0]
        # print("Parsing error", e)
        stats["pdf_parsing_errors"] += 1


def parse_index_info(index_path):
    for page_layout in extract_pages(index_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    print(text_line)
                    for character in text_line:
                        if isinstance(character, LTChar):
                            print(character.get_text())
                            print(character.size)


def get_stats(mypath):
    stats = {"index_count": 0, "output_errors": 0, "pdf_parsing_errors": 0}
    zip_arr = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for corpus_zip_name in zip_arr:
        corpus_zip = zipfile.ZipFile(join(mypath, corpus_zip_name))
        corpus_zip_path = join(mypath, corpus_zip_name)
        corpus_dir_path = os.path.splitext(corpus_zip_path)[0]
        # corpus_zip.extractall(corpus_dir_path)
        # print(corpus_zip.namelist())
        index_types = {}
        for pub_zip_name in corpus_zip.namelist():
            # pub_file_path = join(corpus_zip_path, pub_zip_name)
            pub_dir_path = os.path.splitext(join(corpus_dir_path, pub_zip_name))[0]
            corpus_zip.extract(pub_zip_name, pub_dir_path)
            pub_zip_path = join(pub_dir_path, pub_zip_name)
            pub_zip = zipfile.ZipFile(pub_zip_path, 'r')
            # Get a list of all archived file names from zip
            list_file_names = pub_zip.namelist()
            # Iterate over the file names
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
                            if 'index' in title:
                                stats["index_count"] += 1
                                pub_index_count += 1
                                href = book_part.xpath('.//self-uri/@xlink:href',
                                                       namespaces={"xlink": "http://www.w3.org/1999/xlink"})[0]
                                curr_index_types = get_index_types(title)
                                for type_name in curr_index_types:
                                    index_types[type_name] = index_types.get(type_name, 0) + 1
                                # content_type = book_part.xpath('.//self-uri/@content-type')[0]
                                index_pdf = pub_zip.open(href)
                                # Modify path if needed to put indices of the same type to a common folder
                                curr_type_str = '-'.join(curr_index_types)
                                index_txt_path = pub_dir_path + "-" + str(pub_index_count) + "_" + curr_type_str + ".txt"
                                parse_index(index_pdf, index_txt_path, stats)
                    except:
                        e = sys.exc_info()[0]
                        print(e)
                    jats_file.close()
            pub_zip.close()
            try:
                os.remove(pub_zip_path)
                os.rmdir(pub_dir_path)
            except:
                e = sys.exc_info()[0]
                print(e)
        print(index_types)
    for item in stats.items():
        print(item)


if __name__ == '__main__':
    get_stats('data')