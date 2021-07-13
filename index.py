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