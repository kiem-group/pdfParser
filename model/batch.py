# author: Natallia Kokash, natallia.kokash@gmail.com

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from os.path import join
import zipfile
import os
from model.publication import Publication
from model.cluster_bibliographic import ClusterSet
from model.cluster_index import IndexClusterSet
import logging
import uuid

@dataclass_json
@dataclass
class Batch:
    """A class for holding information about a batch of publications"""
    zip_path: str
    publications: [Publication]
    cluster_set_bib: ClusterSet = None
    cluster_set_index: IndexClusterSet = None
    extract_bib: bool = True
    extract_index: bool = False
    start: int = 0
    size: int = 0
    count_idx: int = 0
    count_bib: int = 0
    errors_xml: int = 0
    errors_other: int = 0
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())
        self.logger = logging.getLogger('pdfParser.batch.' + self.__class__.__name__)

    def add_publication(self, pub):
        if pub is None:
            return
        self.publications.append(pub)
        self.count_idx += len(pub.index_files) if pub.index_files else 0
        if pub.bib_file:
            self.count_bib += 1
        else:
            self.errors_xml += 1

    def cluster(self):
        # Cluster bibliographic references
        self.logger.info("Started bibliography clustering")
        self.cluster_set_bib = ClusterSet(batch=self.UUID)
        for pub in self.publications:
            self.cluster_set_bib.add_references(pub.bib_refs)
        self.logger.info("\tNumber of bib clusters: %d", self.cluster_set_bib.num_clusters)
        # Cluster index references
        self.logger.info("Started index clustering")
        self.cluster_set_index = IndexClusterSet(batch=self.UUID, threshold=0.9)
        for pub in self.publications:
            self.cluster_set_index.add_references(pub.index_refs)
        self.logger.info("\tNumber of index clusters: %d", self.cluster_set_index.num_clusters)

    def disambiguate(self):
        for pub in self.publications:
            pub.disambiguate_bib()
            pub.disambiguate_index()

    def log_info(self):
        self.logger.info("Created batch from zip file: %s", self.zip_path)
        self.logger.info("\tStart and end indices: %d - %d", self.start, self.start + self.size)
        self.logger.info("\tParsed bibliography: %r", self.extract_bib)
        self.logger.info("\tParsed indices: %r", self.extract_index)
        self.logger.info("\tNumber of publications: %d", self.pub_count)
        self.logger.info("\tNumber of collections: %d", self.collection_count)
        self.logger.info("\tNumber of pages: %d", self.page_count)
        self.logger.info("\tAverage publication length: %d", self.avg_page_count)
        self.logger.info("\tMax number of index files in a publication: %d", self.max_idx_count)
        self.logger.info("\tNumber of bibliography files: %d", self.count_bib)
        self.logger.info("\tNumber of index files: %d", self.count_idx)
        self.logger.info("\tFailed to process XML files: %d", self.errors_xml)
        self.logger.info("\tFailed to process publications: %d", self.errors_other)

    @property
    def pub_count(self) -> int:
        return len(self.publications or [])

    @property
    def page_count(self) -> int:
        if self.pub_count > 0:
            return sum([p.page_count if p.page_count is not None else 0 for p in self.publications])
        return 0

    @property
    def avg_page_count(self) -> int:
        if self.pub_count > 0:
            num_no_page_count = sum([1 if p.page_count is None else 0 for p in self.publications])
            num_page_info = self.pub_count - num_no_page_count
            return self.page_count / num_page_info if num_page_info > 0 else 0
        return 0

    @property
    def max_idx_count(self) -> int:
        if self.pub_count > 0:
            return max([len(p.index_files or []) for p in self.publications])
        return 0

    @property
    def collection_count(self) -> int:
        if self.pub_count > 0:
            return sum([1 if p.is_collection else 0 for p in self.publications])
        return 0

    # Extract information about a batch of publications
    @classmethod
    def from_zip(cls, zip_path, extract_bib: bool = True, extract_index: bool = False, start: int = 0, size: int = -1):
        batch_zip = zipfile.ZipFile(zip_path)
        m = len(batch_zip.namelist())
        end = m if size < 0 else min(start + size, m)
        if m < start or end > m:
            return None
        batch = Batch(zip_path=zip_path, publications=[], start=start,
                      size=end-start, extract_bib=extract_bib, extract_index=extract_index)
        batch_dir_path = os.path.splitext(zip_path)[0]
        for i in range(start, end):
            pub_zip_name = batch_zip.namelist()[i]
            pub_dir_name = os.path.splitext(pub_zip_name)[0]
            pub_dir_path = join(batch_dir_path, pub_dir_name)
            batch_zip.extract(pub_zip_name, pub_dir_path)
            pub_zip_path = join(pub_dir_path, pub_zip_name)
            try:
                pub = Publication.from_zip(pub_zip_path, extract_bib=batch.extract_bib, extract_index=batch.extract_index)
                batch.add_publication(pub)
                os.remove(pub_zip_path)
                os.rmdir(pub_dir_path)
            except:
                batch.errors_other += 1
        batch.log_info()
        return batch
