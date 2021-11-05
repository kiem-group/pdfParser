from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.reference_bibliographic import Reference
import Levenshtein as lev
import uuid
from typing import Optional


@dataclass_json
@dataclass
class Cluster:
    refs: [Reference]
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())
        if not self.refs:
            self.refs = []

    def ref_lev_ratio(self, ref: Reference, match_all=False) -> float:
        avg_ratio = 0
        if self.refs and len(self.refs) > 0:
            ref_text = ref.text.lower()
            if match_all:
                avg_ratio = lev.ratio(ref_text, self.refs[0])
            else:
                sum_ratio = 0
                for entry in self.refs:
                    entry_text = entry.text.lower()
                    if ref_text == entry_text:
                        sum_ratio += 1.0
                    else:
                        sum_ratio += lev.ratio(ref_text, entry_text)
                avg_ratio = sum_ratio / len(self.refs)
            # TODO: revise based on clustering method improvement in tests
        return avg_ratio

    def add_reference(self, ref: Reference):
        self.refs.append(ref)

    def remove_reference_by_uuid(self, ref_uuid: str) -> bool:
        m = len(self.refs)
        self.refs = [e for e in self.refs if e.uuid != ref_uuid]
        return m != len(self.refs)

    @property
    def props(self) -> dict:
        return {
            "UUID": self.UUID,
            "size": len(self.refs),
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"


@dataclass_json
@dataclass
class ClusterSet:
    clusters: [Cluster] = None
    threshold: float = 0.75

    def __post_init__(self):
        if not self.clusters:
            self.clusters = []

    # checks if similar references already exists in clusters
    # by matching with first sample in a cluster or with all samples in a cluster
    def get_ref_cluster(self, ref: Reference, match_all=False) -> Optional[Cluster]:
        if not self.clusters:
            return None
        for cluster in self.clusters:
            avg_ratio = cluster.ref_lev_ratio(ref, match_all)
            if avg_ratio > self.threshold:
                return cluster
        return None

    def clear(self):
        self.clusters = []

    def remove_reference(self, ref: Reference) -> bool:
        for cluster in self.clusters:
            if cluster.remove_reference_by_uuid(ref.uuid):
                return True
        return False

    # Compute editing distance for local clustering of similar references
    def add_references(self, refs: [Reference]):
        n = len(refs)
        for i in range(n):
            ref = refs[i]
            cluster = self.get_ref_cluster(ref)
            if cluster is not None:
                cluster.add_reference(ref)
            else:
                self.clusters.append(Cluster(refs=[ref]))
