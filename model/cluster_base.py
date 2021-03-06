# author: Natallia Kokash, natallia.kokash@gmail.com

import abc
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.reference_base import BaseReference
import uuid
from typing import Optional


@dataclass_json
@dataclass
class BaseCluster:
    refs: [BaseReference]
    batch: str = None
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())
        if not self.refs:
            self.refs = []

    @abc.abstractmethod
    def ref_lev_ratio(self, ref, match_all=False) -> float:
        return 0

    def add_reference(self, ref: BaseReference):
        self.refs.append(ref)

    def remove_reference_by_uuid(self, ref_uuid: str) -> bool:
        m = len(self.refs)
        self.refs = [e for e in self.refs if e.uuid != ref_uuid]
        return m != len(self.refs)

    @property
    def props(self) -> dict:
        return {
            "UUID": self.UUID,
            "batch": self.batch,
            "size": len(self.refs),
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"

    @classmethod
    def deserialize(cls, props: dict, refs):
        self = cls(UUID=props["UUID"], refs=refs)
        for key in props.keys():
            setattr(self, key, props[key])
        return self


@dataclass_json
@dataclass
class BaseClusterSet:
    clusters: [BaseCluster] = None
    threshold: float = 0.75
    batch: str = None

    def __post_init__(self):
        if not self.clusters:
            self.clusters = []

    # Checks if similar references already exist in clusters
    # by matching with first sample in a cluster or with all samples in a cluster
    def get_ref_cluster(self, ref: BaseReference, match_all: bool = False) -> Optional[BaseCluster]:
        if not self.clusters:
            return None
        for cluster in self.clusters:
            avg_ratio = cluster.ref_lev_ratio(ref, match_all)
            if avg_ratio > self.threshold:
                return cluster
        return None

    def clear(self):
        self.clusters = []

    def remove_reference(self, ref: BaseReference) -> bool:
        for cluster in self.clusters:
            if cluster.remove_reference_by_uuid(ref.uuid):
                return True
        return False

    # Compute editing distance for local clustering of similar references
    def add_references(self, refs: [BaseReference]):
        if refs is not None:
            for ref in refs:
                cluster = self.get_ref_cluster(ref)
                if cluster is not None:
                    cluster.add_reference(ref)
                else:
                    self.clusters.append(BaseCluster(refs=[ref], batch=self.batch))

    @property
    def num_clusters(self) -> int:
        return len(self.clusters) if self.clusters is not None else 0
