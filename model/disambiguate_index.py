from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.index_external import ExternalIndex
from hucitlib import KnowledgeBase
import pkg_resources
import json
from typing import Union
import logging
from urllib.request import Request, urlopen

module_logger = logging.getLogger('pdfParser.disambiguate_index')


@dataclass_json
@dataclass
class DisambiguateIndex:
    virtuoso_cfg_file = pkg_resources.resource_filename('hucitlib', 'config/virtuoso.ini')
    kb = KnowledgeBase(virtuoso_cfg_file)

    @classmethod
    def find_hucitlib(cls, term: str) -> Union[ExternalIndex, None]:
        try:
            module_logger.info("Huhitlib - searching for: " + term)
            res_term = cls.kb.search(term)
            if res_term and len(res_term) > 0:
                res = res_term[0][1].to_json()
                res_data = json.loads(res)
                module_logger.debug("Hucitlib - term match found: " + term)
                return ExternalIndex(uri=res_data["uri"], type="hucitlib")
            else:
                module_logger.debug("Hucitlib - term not found: " + term)
                return None
        except Exception as e:
            module_logger.error("Failed to access Hucitlib: \n\t %s", e)
            return None

    # Assess percentage of entries in index locorum that are ambiguous and difficult to link (2+ linking candidates)
    # Keep Wikidata look-up as a fallback for index entries that don’t have a match in hucitlib
    # Before linking, and for the sake of efficiency, an intermediate step could be the clustering of index entries
    # (e.g. “Aeschylus, Agamemnon” in publication A is grouped together with similar entries in other indexes)

    @classmethod
    def find_wikidata(cls, term: str, lang="en") -> Union[ExternalIndex, None]:
        url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + term
        url += "&language=" + lang
        url += "&format=json"
        try:
            req = Request(url, headers={'User-Agent': 'Chrome/93.4'})
            resp = urlopen(req)
            wiki_data = json.load(resp)
            if len(wiki_data["search"]) > 0:
                module_logger.debug("Wikidata - term match found: " + term)
                return ExternalIndex(uri=wiki_data["search"][0]["url"], type="wikidata")
            return None
        except Exception as e:
            module_logger.error("Failed to access Wikidata: \n\t %s", e)
            return None

        # from wikidata.client import Client
        # try:
        #     client = Client()
        #     entity = client.get(term, load=True)
        #     print(entity)
        #     # for key in image.keys:
        #     #     print(key)
        #     # else:
        #     #     module_logger.debug("Wikidata - term not found: " + term)
        #     #     return None
        #     return ExternalIndex(uri="term", type="wikidata")
        # except:
        #     module_logger.error("Failed to access Wikidata")
        #     return None
