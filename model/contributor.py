from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Contributor:
    """A class for holding information about a publication contributor"""

    type: str = None
    surname: str = None
    given_names: str = None
    full_name: str = None
    # TODO save order of authors

    @classmethod
    def from_jats(cls, jats_contrib):
        self = cls()
        if jats_contrib is not None:
            contrib_type = jats_contrib.xpath('@contrib-type')
            if len(contrib_type) > 0:
                self.type = contrib_type[0]
                self.surname = ' '.join(jats_contrib.xpath('.//name/surname/text()'))
                self.given_names = ' '.join(jats_contrib.xpath('.//name/given-names/text()'))
                self.full_name = self.surname + ", " + self.given_names
        return self

    @property
    def props(self) -> dict:
        return {
            "type": self.type,
            "surname": self.surname,
            "given_names": self.given_names,
            "full_name": self.full_name
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"
