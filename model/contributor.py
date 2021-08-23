from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Contributor:
    """A class for holding information about a publication contributor"""

    def __init__(self, jats_contrib):
        self.parse_jats(jats_contrib)

    type: str = None
    surname: str = None
    given_names: str = None

    @property
    def jats_contrib(self) -> str:
        return self._jats_contrib

    def parse_jats(self, jats_contrib):
        if jats_contrib is None:
            return
        contrib_type = jats_contrib.xpath('@contrib-type')
        if len(contrib_type) > 0:
            self.type = contrib_type[0]
            self.surname = ' '.join(jats_contrib.xpath('.//name/surname/text()'))
            self.given_names = ' '.join(jats_contrib.xpath('.//name/given-names/text()'))