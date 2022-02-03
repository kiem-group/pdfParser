from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.publication_base import BasePublication


@dataclass_json
@dataclass(unsafe_hash=True)
class ExternalPublication(BasePublication):
    """A class for holding information about an external publication"""
    # properties
    confidence: float = 0
    url: str = None
    type: str = None  # google, crossref, brill

    @property
    def props(self) -> dict:
        props = BasePublication.props.fget(self)
        props["confidence"] = self.confidence
        props["url"] = self.url
        props["type"] = self.type
        return props
