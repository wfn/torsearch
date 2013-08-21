#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pformat
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement, _literal_as_text
from torsearch import db
from torsearch import debug_logger

class Explain(Executable, ClauseElement):
  def __init__(self, statement, analyze=False, buffers=False):
    self.statement = _literal_as_text(statement)
    self.analyze = analyze
    self.buffers = buffers

@compiles(Explain, 'postgresql')
def pg_explain(element, compiler, **kwargs):
  text = "EXPLAIN "
  if element.analyze:
    text += "(ANALYZE"
    if element.buffers: # BUFFERS requires ANALYZE
      text += ", BUFFERS"
    text += ") "
  text += compiler.process(element.statement)
  return text

def run_explain(query, analyze=False, buffers=False, output_statement=False, output_explain=False,\
    debug_log=debug_logger.info, warning_log=debug_logger.warning):

  warning_conditions = { # key = name of condition, value = evaluator of condition
    'Sequential Scan detected': lambda info: 'Seq Scan' in info
  }

  info = db.session.execute(Explain(query, analyze, buffers)).fetchall()

  warning = False
  for condition, eval_condition in warning_conditions.iteritems():
    if eval_condition(info):
      warning_log(condition)
      warning = True

  if output_statement or warning:
    debug_log('Query statement:')
    debug_log(query.statement)
  if output_explain or warning:
    debug_log('EXPLAIN results:')
    debug_log(pformat(info))

if __name__ == '__main__':
  pass
