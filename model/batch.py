from dataclasses import dataclass
from dataclasses_json import dataclass_json
from os.path import join
import zipfile
import os
from model.publication import Publication
from model.cluster_bibliographic import Cluster, ClusterSet


@dataclass_json
@dataclass
class Batch:
    """A class for holding information about a batch of publications"""

    zip_path: str
    extract_bib = True
    extract_index = False
    start = 0
    size = 0
    publications: [Publication]
    cluster_set: ClusterSet = None

    index_count: int = 0
    bibliography_count: int = 0

    xml_parsing_errors: int = 0
    format_errors: int = 0
    other_errors: int = 0

    def add_publication(self, pub):
        if pub is None:
            return
        self.publications.append(pub)
        self.index_count += len(pub.index_files) if pub.index_files else 0
        if pub.bib_file:
            self.bibliography_count += 1
        else:
            self.xml_parsing_errors += 1

    def cluster(self):
        self.cluster_set = ClusterSet()
        for pub in self.publications:
            self.cluster_set.add_references(pub.bib_refs)
        # for cluster in self.cluster_set.clusters:
        #     if len(cluster.refs) > 1:
        #         print("Found cluster")
        #         for ref in cluster.refs:
        #             print("\t" + ref.text)

    def disambiguate(self):
        pass

    # Extract information about a batch of publications
    @classmethod
    def from_zip(cls, zip_path, extract_bib=True, extract_index=False, start=0, size=-1):
        batch_zip = zipfile.ZipFile(zip_path)
        if len(batch_zip.namelist()) < start:
            return
        m = len(batch_zip.namelist())
        end = m if size < 0 else min(start + size, m)

        batch = Batch(zip_path=zip_path, publications=[])
        batch.start = start
        batch.size = end - start
        batch.extract_bib = extract_bib
        batch.extract_index = extract_index

        batch_dir_path = os.path.splitext(zip_path)[0]
        for i in range(start, end):
            pub_zip_name = batch_zip.namelist()[i]
            pub_dir_name = os.path.splitext(pub_zip_name)[0]
            pub_dir_path = join(batch_dir_path, pub_dir_name)
            batch_zip.extract(pub_zip_name, pub_dir_path)
            pub_zip_path = join(pub_dir_path, pub_zip_name)
            batch.add_publication(
                Publication.from_zip(pub_zip_path, extract_bib=batch.extract_bib, extract_index=batch.extract_index))
            try:
                os.remove(pub_zip_path)
                os.rmdir(pub_dir_path)
            except:
                batch.other_errors += 1
        return batch