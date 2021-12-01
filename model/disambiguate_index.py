from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.index_external import ExternalIndex
from hucitlib import KnowledgeBase
import pkg_resources
import json
from typing import Union


@dataclass_json
@dataclass
class DisambiguateIndex:
    virtuoso_cfg_file = pkg_resources.resource_filename('hucitlib', 'config/virtuoso.ini')
    kb = KnowledgeBase(virtuoso_cfg_file)

    @classmethod
    def find_hucitlib(cls, term: str) -> Union[ExternalIndex, None]:
        try:
            res_term = cls.kb.search(term)
            if res_term and len(res_term) > 0:
                res = res_term[0][1].to_json()
                res_data = json.loads(res)
                return ExternalIndex(uri=res_data["uri"], type="hucitlib")
            else:
                return None
        except:
            return None

    # Assess percentage of entries in index locorum that are ambiguous and difficult to link (2+ linking candidates)
    # Keep Wikidata look-up as a fallback for index entries that don’t have a match in hucitlib
    # Before linking, and for the sake of efficiency, an intermediate step could be the clustering of index entries
    # (e.g. “Aeschylus, Agamemnon” in publication A is grouped together with similar entries in other indexes)
