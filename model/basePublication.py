from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.contributor import Contributor
from model.industryIdentifier import IndustryIdentifier
from typing import Union

@dataclass_json
@dataclass(unsafe_hash=True)
class BasePublication:
    """A class for holding information about a publication"""
    identifiers: [IndustryIdentifier] = None
    title: str = None
    authors: [Contributor] = None
    editors: [Contributor] = None
    year: str = None
    lang: str = None
    publisher: str = None
    location: str = None

    @property
    def doi(self) -> Union[str, None]:
        matches = [id_obj for id_obj in self.identifiers if id_obj.type == "doi"]
        if len(matches) > 0:
            return matches[0].id
        return None

    @property
    def issn(self) -> Union[str, None]:
        matches = [id_obj for id_obj in self.identifiers if id_obj.type == "issn"]
        if len(matches) > 0:
            return matches[0].id
        return None

    @property
    def isbn(self) -> [str]:
        return [id_obj.id for id_obj in self.identifiers if id_obj.type == "isbn"]

    @property
    def props(self) -> dict:
        return {
            "title": self.title,
            "year": self.year,
            "lang": self.lang,
            "publisher": self.publisher,
            "location": self.location
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"
