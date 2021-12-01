from dataclasses import dataclass
from dataclasses_json import dataclass_json
import uuid


@dataclass_json
@dataclass(unsafe_hash=True)
class ExternalIndex:
    """A class for holding information about index disambiguation"""
    uri: str = None
    type: str = None
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())

    @property
    def props(self) -> dict:
        return {
            "UUID": self.UUID,
            "uri": self.uri,
            "type": self.type
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"

    @classmethod
    def deserialize(cls, props):
        self = cls(UUID=props["UUID"])
        for key in props.keys():
            setattr(self, key, props[key])
        return self
