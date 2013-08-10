#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pformat
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement, _literal_as_text
from torsearch import db
from torsearch import debug_logger
log = debug_logger.info

class Explain(Executable, ClauseElement):
  def __init__(self, statement, analyze=False):
    self.statement = _literal_as_text(statement)
    print 'statement:', self.statement
    self.analyze = analyze

@compiles(Explain, 'postgresql')
def pg_explain(element, compiler, **kwargs):
  text = "EXPLAIN "
  if element.analyze:
    text += "ANALYZE "
  text += compiler.process(element.statement)
  return text

def run_explain(query, analyze=False):
  print 'query:', query
  info = db.session.execute(Explain(query, analyze)).fetchall()
  #log('EXPLAIN =>\n' + pformat(info))
  if 'Seq Scan' in info:
    debug_logger.warning('Sequential Scan detected!')
    debug_logger.warning('Query statement:')
    log(query.statement)
    debug_logger.warning('EXPLAIN results:')
    log(pformat(info))

if __name__ == '__main__':
  pass
