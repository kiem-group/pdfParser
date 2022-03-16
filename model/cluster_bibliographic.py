# author: Natallia Kokash, natallia.kokash@gmail.com

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.reference_bibliographic import Reference
import Levenshtein as lev
from model.cluster_base import BaseCluster, BaseClusterSet


@dataclass_json
@dataclass
class Cluster(BaseCluster):

    def ref_lev_ratio(self, ref: Reference, match_all=False) -> float:
        avg_ratio = 0
        if self.refs and len(self.refs) > 0:
            ref_title = ref.title.lower()
            if match_all:
                sum_ratio = 0
                for entry in self.refs:
                    same_year = ref.year == entry.year
                    if same_year:
                        entry_title = entry.title.lower()
                        if ref_title == entry_title:
                            sum_ratio += 1.0
                        else:
                            sum_ratio += lev.ratio(ref_title, entry_title)
                avg_ratio = sum_ratio / len(self.refs)
            else:
                same_year = ref.year == self.refs[0].year
                if same_year:
                    avg_ratio = lev.ratio(ref_title, self.refs[0].title.lower())
        return avg_ratio


@dataclass_json
@dataclass
class ClusterSet(BaseClusterSet):
    # Compute editing distance for local clustering of similar references
    def add_references(self, refs: [Reference]):
        if refs is not None:
            for ref in refs:
                cluster = self.get_ref_cluster(ref)
                if cluster is not None:
                    cluster.add_reference(ref)
                else:
                    self.clusters.append(Cluster(refs=[ref], batch=self.batch))
