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
            ref_label = next((item.label for item in ref.refs if len(item.label) > 3), None)
            if ref_label and len(self.refs) > 0:
                for cluster_ref in self.refs:
                    cluster_label = next((item.label for item in cluster_ref.refs if len(item.label) > 3), None)
                    if cluster_label:
                        return lev.ratio(cluster_label, ref_label)
        return 0


@dataclass_json
@dataclass
class IndexClusterSet(BaseClusterSet):
    # Compute editing distance for local clustering of similar references
    def add_references(self, refs: [IndexReference]):
        if refs is not None:
            for ref in refs:
                cluster = self.get_ref_cluster(ref)
                if cluster is not None:
                    cluster.add_reference(ref)
                else:
                    self.clusters.append(IndexCluster(refs=[ref], batch=self.batch))
