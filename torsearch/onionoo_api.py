#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torsearch import app, db
from torsearch.models import Descriptor, Consensus, StatusEntry
from flask import Response, request, jsonify
from sqlalchemy import func, select, distinct

UPPER_LIMIT = 50 # max number of results per query, for now

def apply_filters(query, base_model=StatusEntry, source=None, exclude=[]):
  if not source:
    source = request.args
  if 'search' in source and 'search' not in exclude:
    term = source['search']
    if len(term) == 40 or term.startswith('$'):
      query = query.filter(base_model.fingerprint.like(
        (term[1:] if term.startswith('$') else term) + '%')) # start / or the whole of the fingerprint
    elif '.' in term: # a primitive heuristic for now
      query = query.filter(base_model.address.like(term + '%')) # start / or the whole of IPv4 address
    else:
      query = query.filter(func.lower(base_model.nickname).like('%' + func.lower(term) + '%'))
  query = query.limit(min(UPPER_LIMIT, int(source['limit']) if 'limit' in source and 'limit' not in exclude else UPPER_LIMIT))
  if 'offset' in source and 'offset' not in exclude:
    offset = int(source['offset'])
    query = query.offset(offset)
  return query

@app.route('/')
def index():
  return 'Placeholder index page.'

@app.route('/summary')
def summary():
  last_consensus = Consensus.query.order_by('valid_after desc').first()
  q = StatusEntry.query.order_by(StatusEntry.fingerprint, 'validafter desc').distinct(StatusEntry.fingerprint)
  #q = StatusEntry.query.filter_by(validafter = last_consensus.valid_after)
  q = apply_filters(q)
  #entries = q.all()
  entries = q

  #data = {
  #  'relays_published': last_consensus.valid_after,
  #  'relays': [
  #    {
  #      'n': e.nickname if e.nickname != 'Unnamed' else '', # leaves "n": "" entries
  #      'f': e.fingerprint,
  #      'a': [e.address],
  #      'r': e.isRunning
  #    } for e in entries
  #  ]
  #}

  data = {'relays_published': last_consensus.valid_after, 'relays': []}
  for e in entries:
    data['relays'].append({
      'f': e.fingerprint,
      'a': [e.address],
      'r': e.validafter == last_consensus.valid_after
    })
    if e.nickname != 'Unnamed':
      data['relays'][-1]['n'] = e.nickname

  resp = jsonify(data)
  resp.stats_code = 200
  return resp

@app.route('/details')
def details():
  last_consensus = Consensus.query.order_by('valid_after desc').first()
  q = StatusEntry.query.order_by(StatusEntry.fingerprint, 'validafter desc').distinct(StatusEntry.fingerprint)
  q = apply_filters(q)
  entries = q

  data = {'relays_published': last_consensus.valid_after, 'relays': []}
  for e in entries:
    data['relays'].append({
      'fingerprint': e.fingerprint,
      'or_addresses': [e.address + ':' + str(e.or_port)],
      'running': e.validafter == last_consensus.valid_after,
      'last_seen': e.validafter
    })
    if e.dir_port:
      data['relays'][-1]['dir_addresses'] = [e.address + ':' + str(e.dir_port)]
    if e.nickname != 'Unnamed':
      data['relays'][-1]['nickname'] = e.nickname
    data['relays'][-1]['first_seen'] = db.session.query(StatusEntry.validafter).filter_by(fingerprint=e.fingerprint).order_by(StatusEntry.validafter).first()[0]

  resp = jsonify(data)
  resp.stats_code = 200
  return resp

if __name__ == '__main__':
  pass
