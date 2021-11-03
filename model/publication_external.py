from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.publication_base import BasePublication


@dataclass_json
@dataclass(unsafe_hash=True)
class ExternalPublication(BasePublication):
    """A class for holding information about an external publication"""
    # properties
    confidence: float = 0
    url_google: str = None
    url_crossref: str = None

    @property
    def props(self) -> dict:
        props = BasePublication.props.fget(self)
        props["confidence"] = self.confidence
        props["url_google"] = self.url_google
        props["url_crossref"] = self.url_crossref
        return props
