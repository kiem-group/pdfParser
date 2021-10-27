from dataclasses import dataclass
from dataclasses_json import dataclass_json
from dataclasses import asdict

@dataclass_json
@dataclass
class IndustryIdentifier:
    """A class for holding information about publication industry identifier"""
    id: str = None      # Identifier
    type: str = None    # ISBN, DOI, etc.
    format: str = None

    def serialize(self):
        props = asdict(self)
        prop_str = ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in props.items())
        return "{" + prop_str + "}"
