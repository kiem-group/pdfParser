from __future__ import annotations
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.contributor import Contributor
from model.industry_identifier import IndustryIdentifier
from typing import Union
import uuid
import logging


@dataclass_json
@dataclass(unsafe_hash=True)
class BasePublication:
    """A class for holding information about a publication"""
    # properties
    title: str = None
    year: str = None
    lang: str = None
    publisher: str = None
    location: str = None
    # relationships
    authors: [Contributor] = None
    editors: [Contributor] = None
    identifiers: [IndustryIdentifier] = None
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())
        self.logger = logging.getLogger('pdfParser.publication.' + self.__class__.__name__)
        # self.logger.debug('Created an instance of %s for %s ', self.__class__.__name__, self.UUID)

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
            "UUID": self.UUID,
            "title": self.title,
            "year": self.year,
            "lang": self.lang,
            "publisher": self.publisher,
            "location": self.location
        }

    def serialize(self) -> str:
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"

    # Restore object from a string representing Neo4j property set (json without parentheses in keys)
    @classmethod
    def deserialize(cls, props: dict) -> BasePublication:
        self = cls(UUID=props["UUID"])
        for key in props.keys():
            setattr(self, key, props[key])
        return self
