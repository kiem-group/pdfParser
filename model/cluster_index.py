from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.reference_index import IndexReference
import Levenshtein as lev
from model.cluster_base import BaseCluster, BaseClusterSet


@dataclass_json
@dataclass
class IndexCluster(BaseCluster):

    def ref_lev_ratio(self, ref: IndexReference, match_all=False) -> float:
        if self.refs and ref.refs:
            ref_label = next(item.label for item in ref.refs if item.label is not None)
            if ref_label:
                for cluster_ref in self.refs:
                    cluster_label = next(item.label for item in cluster_ref.refs if item.label is not None)
                    if cluster_label:
                        return lev.ratio(cluster_label, ref_label)
                    # TODO add an option to match with all labels, return average ratio
        return 0


@dataclass_json
@dataclass
class IndexClusterSet(BaseClusterSet):
    # Compute editing distance for local clustering of similar references
    def add_references(self, refs: [IndexReference]):
        n = len(refs)
        for i in range(n):
            ref = refs[i]
            cluster = self.get_ref_cluster(ref)
            if cluster is not None:
                cluster.add_reference(ref)
            else:
                self.clusters.append(IndexCluster(refs=[ref]))
