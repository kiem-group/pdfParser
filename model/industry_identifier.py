from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
import uuid


@dataclass_json
@dataclass
class IndustryIdentifier:
    """A class for holding information about publication industry identifier"""
    id: str = None     # Identifier
    type: str = None   # ISBN, DOI, etc.
    format: str = None
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())

    @property
    def props(self) -> dict:
        return asdict(self)

    def serialize(self):
        prop_str = ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items())
        return "{" + prop_str + "}"

    # Restore object from a Neo4j property set
    @classmethod
    def deserialize(cls, props):
        self = cls(UUID=props["UUID"])
        for key in props.keys():
            setattr(self, key, props[key])
        return self
