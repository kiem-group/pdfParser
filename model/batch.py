# author: Natallia Kokash, natallia.kokash@gmail.com

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from os.path import join
import zipfile
import os
from model.publication import Publication
from model.cluster_bibliographic import ClusterSet
from model.cluster_index import IndexClusterSet


@dataclass_json
@dataclass
class Batch:
    """A class for holding information about a batch of publications"""
    # TODO add collected stats to the logs
    zip_path: str
    publications: [Publication]
    cluster_set_bib: ClusterSet = None
    cluster_set_index: IndexClusterSet = None
    extract_bib: bool = True
    extract_index: bool = False
    start: int = 0
    size: int = 0
    count_index: int = 0
    count_bib: int = 0
    errors_xml: int = 0
    errors_format: int = 0
    errors_other: int = 0

    def add_publication(self, pub):
        if pub is None:
            return
        self.publications.append(pub)
        self.count_index += len(pub.index_files) if pub.index_files else 0
        if pub.bib_file:
            self.count_bib += 1
        else:
            self.errors_xml += 1

    def cluster(self):
        self.cluster_set_bib = ClusterSet()
        for pub in self.publications:
            self.cluster_set_bib.add_references(pub.bib_refs)
        self.cluster_set_index = IndexClusterSet()
        for pub in self.publications:
            self.cluster_set_index.add_references(pub.index_refs)

    def disambiguate(self):
        pass

    # Extract information about a batch of publications
    @classmethod
    def from_zip(cls, zip_path, extract_bib=True, extract_index=False, start=0, size=-1):
        batch_zip = zipfile.ZipFile(zip_path)
        m = len(batch_zip.namelist())
        if m < start:
            return
        end = m if size < 0 else min(start + size, m)
        batch = Batch(zip_path=zip_path, publications=[], start=start,
                      size=end-start, extract_bib=extract_bib, extract_index=extract_index)
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
                batch.errors_other += 1
        return batch