#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torsearch import db
from torsearch.models import Descriptor, Consensus, StatusEntry
from stem.descriptor import DocumentHandler
from stem.descriptor.reader import DescriptorReader
from config import COMMIT_AFTER
from torsearch import debug_logger
log = debug_logger.info
import gc
import os
from multiprocessing import Process

def import_descriptors(wherefrom, persistence_file):
  if not gc.isenabled():
    gc.enable()

  reader = DescriptorReader(wherefrom, persistence_path=persistence_file)
  log('recalled %d files processed from my source(s) provided', len(reader.get_processed_files()))
  with reader:
    i = 0 # need due to for() scope
    for i, desc in enumerate(reader):
      desc_model = Descriptor(desc)
      db.session.add(desc_model)
      if (i+1) % COMMIT_AFTER == 0:
        log('row %d: committing.', i+1)
        db.session.commit()
        gc.collect()
  log('iterated over %d files', i+1)
  db.session.commit()

def import_consensus(document, import_statuses=True, delete_statuses_later=True):
  doc_model = Consensus(document)
  db.session.add(doc_model)
  if import_statuses:
    for status in document.routers.values():
      stat_model = StatusEntry(status, document.valid_after)
      db.session.add(stat_model)
    if delete_statuses_later:
      del document.routers
  db.session.commit()

def import_consensuses(wherefrom, persistence_file, import_statuses=True):
  if not gc.isenabled():
    gc.enable()

  reader = DescriptorReader(wherefrom, persistence_path=persistence_file, document_handler = DocumentHandler.DOCUMENT)
  with reader:
    i = 0

    for i, doc in enumerate(reader):
      import_consensus(doc, import_statuses)
      log('document %d committed.', i+1)
      gc.collect()
  gc.collect() # calling again just in case: reader is now closed, can gc it (and docs)
  log('iterated over %d documents', i+1)

def batch_import_consensuses(consensus_dir):
  '''a simple high-level function to import consensuses and network statuses.
  garbage allocation does not happen on objects in an iterable while it's being iterated, this is a simple but more memory-efficient way to import larger amounts of consensuses (including network statuses)
  '''

  for dirname, dirnames, filenames in os.walk(consensus_dir): # FIXME: os.listdir() would be enough here.
                                                              # normally, here we'd iterate over os.walk()
                                                              # we should not recurse (done by DescriptorReader).
    for subdir in dirnames:
      dir_to_import = os.path.join(dirname, subdir)
      log('importing from directory %s..', dir_to_import)
      #import_consensuses(dir_to_import, os.path.join(dir_to_import, 'imported.persistence'))

      # not only does this (lazily) avoid possible memory leaks, but it's also one step towards parallelized import.
      # no parallelization right now (lots of global state), but this is worth it in any case.
      p = Process(target=import_consensuses, args=(dir_to_import, os.path.join(dir_to_import, 'imported.persistence')))
      p.start()
      p.join()
    break

def batch_import_descriptors(descriptor_dir):
  '''a simple high-level function to import server descriptors.
  descriptor import is less cannibalistic in terms of memory usage, but subprocess isolation still makes sense.
  '''

  for dirname, dirnames, filenames in os.walk(descriptor_dir): # FIXME: os.listdir() would be enough here.
    for subdir in dirnames:
      dir_to_import = os.path.join(dirname, subdir)
      log('importing from directory %s..', dir_to_import)
      import_descriptors(dir_to_import, os.path.join(dir_to_import, 'imported.persistence'))

      p = Process(target=import_descriptors, args=(dir_to_import, os.path.join(dir_to_import, 'imported.persistence')))
      p.start()
      p.join()
    break

if __name__ == '__main__':
  pass
