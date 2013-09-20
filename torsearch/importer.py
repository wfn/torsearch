#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torsearch import db, debug_logger
log = debug_logger.info
from torsearch.models import Descriptor, Consensus, StatusEntry, Fingerprint
from sqlalchemy import func
from stem.descriptor import DocumentHandler
from stem.descriptor.reader import DescriptorReader
from config import COMMIT_AFTER
import gc
import os
from multiprocessing import Process

def get_subdirectories(dirname):
  return [name for name in os.listdir(dirname)
    if os.path.isdir(os.path.join(dirname, name))]

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

def import_consensus(document, import_statuses=True,
    delete_statuses_later=True, check_if_exists=True, upsert_check_va=True):
  if check_if_exists:
    # this is needed if the persistence file may contain different paths to
    # the same documents. there are multiple ways of getting around this.

    # this is the easiest way to solve things, and the query is fast and will
    # be run only once per a whole consensus document.
    # we need this when we switch to the 'recent' folder in rsync after having
    # imported most of our stuff from the metrics archives.
    # the archives and the rsync'ed 'recent' may overlap.

    if Consensus.query.filter(Consensus.valid_after==document.valid_after).count():
      log('Consensus document with valid-after %s already in database '
          '- skipping this document.',
          document.valid_after.strftime('%y-%m-%d %H:%M:%S'))
      del document
      return False

  doc_model = Consensus(document)
  db.session.add(doc_model)

  if import_statuses:
    for status in document.routers.values():
      stat_model = StatusEntry(status, document.valid_after)
      db.session.add(stat_model)
      db.session.flush() # so we can get the new id attribute

      # update/insert relevant entry in the Fingerprint table.
      # we could simply query Fingerprint to see if there's already an entry
      # for this particular fingerprint there (and depending on result, either
      # update or insert), but it is much more efficient
      # to do a kind of an 'upsert' in one transaction.
      # to do this, we use a raw SQL query.

      if not upsert_check_va:

        # this query silently fails if there's no match in WHERE.
        db.session.execute(db.text("UPDATE fingerprint SET "
          "digest=:digest, nickname=:nickname, address=:address, "
          "last_va=:last_va, sid=:sid WHERE fp12=:fp12"),
          {'digest': stat_model.digest, 'nickname': stat_model.nickname,
            'address': stat_model.address, 'last_va': stat_model.validafter,
            'sid': stat_model.id, # the ORM will have assigned an id before
                                  # our later commit - ORMs are useful
            'fp12': stat_model.fingerprint[0:(Fingerprint.FP_SUBSTR_LEN-1)]})

      else: # only UPDATE when the last entry's last_va is < our new one.

        db.session.execute(db.text("UPDATE fingerprint SET "
          "digest=:digest, nickname=:nickname, address=:address, "
          "last_va=:last_va, sid=:sid "
          "WHERE fp12=:fp12 AND EXISTS ("
          "  SELECT 1 FROM fingerprint "
          "    WHERE fp12=:fp12 AND last_va < :last_va)"),
          {'digest': stat_model.digest, 'nickname': stat_model.nickname,
            'address': stat_model.address, 'last_va': stat_model.validafter,
            'sid': stat_model.id,
            'fp12': stat_model.fingerprint[0:(Fingerprint.FP_SUBSTR_LEN-1)]})

      # this query will also silently fail (in this case, if our fp is already
      # in the table.)
      db.session.execute(db.text("INSERT INTO fingerprint (fp12, sid, "
        "fingerprint, digest, nickname, address, last_va, first_va) SELECT "
        "  :fp12, :sid, :fingerprint, :digest, :nickname, :address, :last_va,"
        "  :first_va "
        "WHERE NOT EXISTS (SELECT 1 FROM fingerprint WHERE fp12=:fp12)"),
          {'digest': stat_model.digest, 'nickname': stat_model.nickname,
            'address': stat_model.address, 'last_va': stat_model.validafter,
            'sid': stat_model.id, 'first_va': stat_model.validafter,
            'fp12': stat_model.fingerprint[0:(Fingerprint.FP_SUBSTR_LEN-1)],
            'fingerprint': stat_model.fingerprint, 'sid': stat_model.id})

    if delete_statuses_later:
      del document.routers

  db.session.commit()
  return True

def import_consensuses(wherefrom, persistence_file, import_statuses=True):
  if not gc.isenabled():
    gc.enable()

  reader = DescriptorReader(wherefrom, persistence_path=persistence_file, document_handler = DocumentHandler.DOCUMENT)
  iterated_over_something = False
  with reader:
    i = 0

    for i, doc in enumerate(reader):
      if import_consensus(doc, import_statuses):
        log('Document %d (valid-after %s) committed.', i+1, doc.valid_after)
        iterated_over_something = True
      gc.collect()
  gc.collect() # calling again just in case: reader is now closed, can gc it (and docs)
  if iterated_over_something:
    log('Iterated over %d documents', i+1)
  else:
    log('No documents at %s were (re-)imported.', wherefrom)

def batch_import_consensuses(consensus_dir, single_dir=False):
  '''a simple high-level function to import consensuses and network statuses.
  garbage allocation does not happen on objects in an iterable while it's being iterated, this is a simple but more memory-efficient way to import larger amounts of consensuses (including network statuses)
  '''

  def do_import(import_dir):
    log('Importing from directory %s..', import_dir)
    p = Process(target=import_consensuses, args=(import_dir, os.path.join(import_dir, 'imported.persistence')))
    p.start()
    p.join()

  if single_dir or not get_subdirectories(consensus_dir): # nowhere to recurse
                                                          # into (last level)
    do_import(consensus_dir)
    return

  for dirname, dirnames, filenames in os.walk(consensus_dir): # FIXME: os.listdir() would be enough here.
                                                              # normally, here we'd iterate over os.walk()
                                                              # we should not recurse (done by DescriptorReader).
    for subdir in dirnames:
      dir_to_import = os.path.join(dirname, subdir)
      #import_consensuses(dir_to_import, os.path.join(dir_to_import, 'imported.persistence'))

      # not only does this (lazily) avoid possible memory leaks, but it's also one step towards parallelized import.
      # no parallelization right now (lots of global state), but this is worth it in any case.
      #p = Process(target=import_consensuses, args=(dir_to_import, os.path.join(dir_to_import, 'imported.persistence')))
      do_import(dir_to_import)
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
