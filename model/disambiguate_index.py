from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.index_external import ExternalIndex
from model.reference_index import IndexReference
from hucitlib import KnowledgeBase, HucitAuthor, HucitWork
import pkg_resources
import json
from typing import Union


@dataclass_json
@dataclass
class DisambiguateIndex:
    virtuoso_cfg_file = pkg_resources.resource_filename('hucitlib', 'config/virtuoso.ini')
    kb = KnowledgeBase(virtuoso_cfg_file)

    @classmethod
    def find_author_hucitlib(cls, author_name: str) -> Union[ExternalIndex, None]:
        cls.kb.get_authors()
        res_author = cls.kb.search(author_name)
        if res_author and len(res_author) > 0:
            author = res_author[0][1].to_json()
            author_data = json.loads(author)
            # Create instance of ExternalIndex
            return ExternalIndex(url_hucitlib = author_data["uri"])
        return None
