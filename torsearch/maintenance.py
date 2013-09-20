#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torsearch import db, debug_logger

def exec_transactionless_query(query):
  '''DB operations like VACUUM ANALYZE require to be executed outside of
  "BEGIN TRANSACTION" / "END TRANSACTION" blocks.
  '''

  conn = db.session.connection()
  #conn.autocommit(False)
  orig_ilevel = conn.isolation_level
  try:
    conn.set_isolation_level(0)
    debug_logger.info('Running maintenance operation: %s', query)
    db.session.execute(query)
    debug_logger.info('Done running maintenance (%s)\nNotices: %s', query,
      conn.notices)
  except Exception as e:
    debug_logger.error('Failed with error: %s', str(e))
  finally:
    #conn.autocommit(True)
    conn.set_isolation_level(orig_ilevel)

def vacuum_full_analyze(table):
  exec_transactionless_query('VACUUM FULL ANALYZE VERBOSE ' + table)

if __name__ == '__main__':
  pass
