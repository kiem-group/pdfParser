from __future__ import annotations
import abc
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import uuid
import logging


@dataclass_json
@dataclass
class BaseReference(object):
    """A class for holding information about an abstract reference (e.g., bibliographic or index)"""
    __metaclass__ = abc.ABCMeta
    text: str = None
    ref_num: int = 0
    cited_by_doi: str = None
    cited_by_zip: str = None
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())
        self.logger = logging.getLogger('pdfParser.reference.' + self.__class__.__name__)
        self.logger.debug('Created an instance of %s for %s ', self.__class__.__name__, self.UUID)
        self.parse()

    @abc.abstractmethod
    def parse(self):
        """Parse here reference text"""
        pass

    @property
    def props(self) -> dict:
        return {
            "UUID": self.UUID,
            "text": self.text,
            "ref_num": self.ref_num
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"

    # Restore object from a string representing Neo4j property set (json without parentheses in keys)
    @classmethod
    def deserialize(cls, props: dict) -> BaseReference:
        self = cls(UUID=props["UUID"])
        for key in props.keys():
            setattr(self, key, props[key])
        return self
