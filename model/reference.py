from dataclasses import dataclass
from model.publication import Publication


@dataclass
class BaseReference:
    """A class for holding information about a reference"""

    text: str
    cited_by: Publication


@dataclass
class Reference(BaseReference):
    """A class for holding information about reference with authors like in given reference"""

    follows: BaseReference


