#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Response, request, jsonify
from sqlalchemy import func, select, distinct
from torsearch import app, db
from torsearch.models import Descriptor, Consensus, StatusEntry
from torsearch.query_info import run_explain
from torsearch.profiler import profile

UPPER_LIMIT = 10 # max number of results per query, for now

def apply_filters(query, last_consensus, base_model=StatusEntry, source=None, exclude=[]):
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
  if 'running' in source and 'running' not in exclude:
    running = False if source['running'].lower() in ('0', 'false') else True
    query = query.filter((base_model.validafter == last_consensus.valid_after) if running\
      else (base_model.validafter < last_consensus.valid_after))
  if 'offset' in source and 'offset' not in exclude:
    offset = int(source['offset'])
    query = query.offset(offset)
  query = query.limit(min(UPPER_LIMIT, int(source['limit']) if 'limit' in source and 'limit' not in exclude else UPPER_LIMIT))
  return query

def sql_search_nickname(nickname):
  '''executes a raw SQL query returning a result set matching a particular nickname.
  '''

  raw_sql = (
  "select * from"
  "("
  "  select distinct on (fingerprint)" # outer distinct on statusentry
  "  * from"
  "  ("
  "    select descriptor.*, statusentry.validafter from"
  "    ("
  "      select distinct on (fingerprint)" # inner distinct on descriptor
  "      fingerprint, descriptor, nickname, address, or_port, dir_port, published"
  "      from descriptor where"
  "        lower(nickname) = :nickname"
  "        order by fingerprint, published desc" # first, let's get distinct most recently published fingerprints from descriptor table
  "    ) as descriptor,"
  "    statusentry where"                        # and join them with statusentry using a near-unique key (fingerprint+descriptor)
  "      substr(statusentry.fingerprint, 0, 12) = substr(descriptor.fingerprint, 0, 12)"
  "      and substr(lower(statusentry.digest), 0, 12) = substr(descriptor.descriptor, 0, 12)"
  "  ) as everything"                       # statusentry will still return lots of rows per a single descriptor
  "  order by fingerprint, validafter desc" # (that was unique in the descr.table) - therefore, need to re-select distinct again,
  ") as sorted "                            # this time distinguishing on those fingerprints with the latest validafter.
  "order by validafter desc limit 200;")    # the rows returned will have the latest fingerprints, but we still need to (re-)sort.
  return db.session.execute(raw_sql, {'nickname': nickname.lower()})

#@profile # uncomment to get info on how much time is spent and where it's being spent
def get_results(query_type='details'):
  # in the future, only select the appropriate fields depending on query type
  last_consensus = Consensus.query.order_by('valid_after desc').first()
  #q = StatusEntry.query.order_by('substr(fingerprint, 0, 12)').distinct('substr(fingerprint, 0, 12)')
  #q = apply_filters(q, last_consensus)
  #entries = q.all()
  s = request.args['search'] if 'search' in request.args and request.args['search'] else None
  if s:
    query = sql_search_nickname(s.lower())
  else:
    query = StatusEntry.query.order_by('validafter desc').limit(200)
  #run_explain(query) # do an EXPLAIN, report any Seq Scans to log
  entries = query.all()
  return last_consensus, entries

@app.route('/')
def index():
  return 'Placeholder index page.'

@app.route('/summary')
def summary():
  last_consensus, entries = get_results('summary')
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
  last_consensus, entries = get_results('summary')
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
    #for row in db.session.execute('select validafter from statusentry where substr(fingerprint, 0, 12) = substr(:fingerprint, 0, 12) and substr(lower(digest), 0, 12) = substr(:descriptor, 0, 12) order by validafter limit 1', {'fingerprint': e.fingerprint, 'descriptor': e.descriptor}):
    #for row in db.session.execute('select validafter from statusentry where substr(fingerprint, 0, 12) = substr(:fingerprint, 0, 12) order by validafter limit 1', {'fingerprint': e.fingerprint, 'descriptor': e.descriptor}):
    #  data['relays'][-1]['first_seen'] = row.validafter

  resp = jsonify(data)
  resp.stats_code = 200
  return resp

if __name__ == '__main__':
  pass
