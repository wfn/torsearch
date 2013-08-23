#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Response, request, jsonify, abort, redirect
from sqlalchemy import func, select, distinct
from sqlalchemy.sql.expression import Select
from torsearch import app, db
from torsearch.models import Descriptor, Consensus, StatusEntry, Fingerprint
from torsearch.query_info import run_explain
from torsearch.profiler import profile

UPPER_LIMIT = 500 # max number of results per query, for now
                  # this can go into config.py

def sql_search_nickname(nickname):
  '''executes a raw SQL query returning a result set matching a particular nickname.
  no longer used - keep this for now nevertheless.
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
  #raw_sql = raw_sql.format(nickname=nickname.lower())
  return db.session.query('fingerprint', 'descriptor', 'nickname', 'address', 'or_port', 'dir_port', 'published', 'validafter')\
      .from_statement(raw_sql).params(nickname=nickname)

def search_nickname_summary(nickname):
  '''we are using this kind of query, more or less.
  we simply translated the SQL into modular/pluggable SQLAlchemy primitives, which directly translate to good, raw SQL. (confirmed.)
  we no longer use this function - keeping for now.
  '''
  raw_sql = (
      "SELECT nickname, fingerprint, address, last_va FROM fingerprint "
      "  WHERE lower(nickname) = :nickname "
      "  ORDER BY last_va DESC "
      "  LIMIT 100 ")
  return db.session.query('nickname', 'fingerprint', 'address', 'last_va').from_statement(raw_sql)\
      .params(nickname=nickname)

def search_nickname_details(nickname):
  '''we are using this kind of query, more or less.
  we simply translated the SQL into modular/pluggable SQLAlchemy primitives, which directly translate to good, raw SQL. (confirmed.)
  we no longer use this function - keeping for now.
  '''
  raw_sql = (
      "SELECT fingerprint.nickname, fingerprint.fingerprint, statusentry.address, or_port, dir_port, published, validafter "
      "  FROM fingerprint, statusentry "
      "  WHERE lower(fingerprint.nickname) = :nickname "
      "    AND statusentry.id = fingerprint.sid "
      "  ORDER BY validafter DESC "
      "  LIMIT 100 ")
  q = select([Fingerprint.nickname, Fingerprint.fingerprint, StatusEntry.address, StatusEntry.or_port, StatusEntry.dir_port, StatusEntry.published, StatusEntry.validafter])
  q = q.where(func.lower(Fingerprint.nickname) == nickname)
  q = q.where(Fingerprint.sid == StatusEntry.id)
  q = q.order_by('validafter DESC')
  q = q.limit(100)
  return q
  #return db.session.query('nickname', 'fingerprint', 'address', 'or_port', 'dir_port', 'published', 'validafter')\
  #    .from_statement(raw_sql).params(nickname=nickname)

def offset_limit(query, upper_limit=UPPER_LIMIT, args=None):
  if not args:
    args = request.args
  limit = min(upper_limit, max(int(args['limit']), 0) if 'limit' in args else upper_limit)
  offset = int(args['offset']) if 'offset' in args else 0
  if offset > 0:
    query = query.offset(offset)
  query = query.limit(limit)
  return query

def do_search(last_validafter, args=None):
  '''this is our current, generalized database querying method.
  '''

  if not args:
    args = request.args
  lookup = args['lookup'] if 'lookup' in args and len(args['lookup']) == Fingerprint.FP_LEN else None
  term = args['search'] if 'search' in args and args['search'] else None
  if lookup:
    term = lookup
  running = args['running'] if 'running' in args and args['running'] else None
  if running is not None: # check explicitly
    running = {
        'condition': False if running.lower() in ('0', 'false') else True,
        'do_query' : True
        }
  else:
    running = {'do_query': False}

  if not term:
    q = Fingerprint.query
    if running['do_query']:
      if running['condition']:
        q = q.filter(Fingerprint.last_va == last_validafter)
      else:
        q = q.filter(Fingerprint.last_va != last_validafter).order_by(Fingerprint.last_va.desc())
    if not running['do_query']:
      q = q.order_by(Fingerprint.last_va.desc()) # we do an inner ORDER BY, so we can internally LIMIT => our JOIN will be easier
    # if there's an OFFSET, we have to put it here.
    # + do an inner LIMIT at this point, before the JOIN - we'll only need to JOIN <= UPPER_LIMIT rows
    q = offset_limit(q, args=args)

    q = q.from_self(Fingerprint.fingerprint, Fingerprint.first_va, Fingerprint.last_va, StatusEntry.or_port, StatusEntry.address,\
        StatusEntry.validafter, StatusEntry.dir_port, StatusEntry.nickname)\
        .join(StatusEntry, Fingerprint.sid == StatusEntry.id)

    if not (running['do_query'] and running['condition']):
      q = q.order_by(StatusEntry.validafter.desc()) # the JOIN itself will leave the rows disordered again

  else:

    q = select([Fingerprint.nickname, Fingerprint.fingerprint, Fingerprint.first_va, Fingerprint.last_va, StatusEntry.address,\
        StatusEntry.or_port, StatusEntry.dir_port, StatusEntry.published, StatusEntry.validafter])

    if running['do_query']:
      if running['condition']:
        q = q.where(Fingerprint.last_va == last_validafter)
      else:
        q = q.where(Fingerprint.last_va != last_validafter)
    if len(term) > 19 or term.startswith('$'): # fingerprint
      term = term[1:] if term.startswith('$') else term
      if lookup: # exact match
        q = q.where(Fingerprint.fingerprint == term)
      else: # search
        q = q.where(Fingerprint.fingerprint.like(term + '%'))
        #q = q.where(func.substr(Fingerprint.fingerprint, 0, Fingerprint.FP_SUBSTR_LEN) == term[:Fingerprint.FP_SUBSTR_LEN-1])
    elif '.' in term: # FIXME: primitive heuristics
      # TODO: probably have a distinct 'address' table with a unique address column
      #q = q.where(StatusEntry.address.like(term + '%')) # the WHERE filtering would happen after the WHERE clause
      #q = q.where(StatusEntry.address.like(term)) # this actually executes rather decently - TODO: benchmark this
      q = q.where(Fingerprint.address.like(term + '%')) # this gets the job done, but we lose a subset of addresses!
    else:
      q = q.where(func.lower(Fingerprint.nickname).like(term.lower() + '%'))
    q = q.where(Fingerprint.sid == StatusEntry.id) # implicit inner join
    if not (running['do_query'] and running['condition']):
      q = q.order_by(StatusEntry.validafter.desc())
    # we didn't OFFSET/LIMIT before the JOIN, do it now
    q = offset_limit(q)

  return q


#@profile # uncomment to get info on how much time is spent and where it's being spent
def get_results(query_type='details'):
  last_consensus = Consensus.query.order_by(Consensus.valid_after.desc()).first()

  #q = StatusEntry.query.order_by('substr(fingerprint, 0, 12)').distinct('substr(fingerprint, 0, 12)')
  #q = apply_filters(q, last_consensus)
  #entries = q.all()

  #s = request.args['search'] if 'search' in request.args and request.args['search'] else None
  #if s:
  #  query = search_nickname_details(s.lower()) if query_type == 'details' else search_nickname_summary(s.lower())
  #  #query = sql_search_nickname(s.lower())
  #else:
  #  query = StatusEntry.query.order_by('validafter desc').limit(200)

  query = do_search(last_consensus.valid_after)
  print str(query)
  run_explain(query, output_statement=True, output_explain=True) # do an EXPLAIN, report any Seq Scans to log
  if isinstance(query, Select):
    entries = db.session.execute(query)
  else:
    entries = query.all() # higher-level Query object
  return last_consensus, entries

@app.route('/')
def index():
  #return 'Placeholder index page.'
  #return redirect('https://github.com/wfn/torsearch/blob/master/docs/onionoo_api.md')
  return 'Placeholder index page. Try /summary, /details, /statuses. <a href="https://github.com/wfn/torsearch/blob/master/docs/onionoo_api.md">API documentation/summary.</a>'

@app.route('/summary')
def summary():
  last_consensus, entries = get_results('summary')
  data = {'relays_published': last_consensus.valid_after.strftime('%Y-%m-%d %H:%M:%S'), 'relays': []}
  for e in entries:
    data['relays'].append({
      'f': e.fingerprint,
      'a': [e.address],
      'r': e.last_va == last_consensus.valid_after
    })
    if e.nickname != 'Unnamed':
      data['relays'][-1]['n'] = e.nickname

  data['count'] = len(data['relays'])
  resp = jsonify(data)
  resp.status_code = 200
  return resp

@app.route('/details')
def details():
  last_consensus, entries = get_results('details')
  data = {'relays_published': last_consensus.valid_after.strftime('%Y-%m-%d %H:%M:%S'), 'relays': []}
  for e in entries:
    data['relays'].append({
      'fingerprint': e.fingerprint,
      #'or_addresses': [e.address + ':' + str(e.or_port)],
      'exit_addresses': [e.address],
      'running': e.last_va == last_consensus.valid_after,
      'last_seen': e.validafter.strftime('%Y-%m-%d %H:%M:%S'),
      'first_seen': e.first_va.strftime('%Y-%m-%d %H:%M:%S')
    })
    #if e.dir_port:
    #  data['relays'][-1]['dir_addresses'] = [e.address + ':' + str(e.dir_port)]
    if e.nickname != 'Unnamed':
      data['relays'][-1]['nickname'] = e.nickname

  data['count'] = len(data['relays'])
  resp = jsonify(data)
  resp.status_code = 200
  return resp

@app.route('/statuses')
def statuses():
  '''placeholder API point to be able to externally test the backend for status entry lists given some fingerprint.
  '''

  lookup = request.args['lookup'] if 'lookup' in request.args else None
  if not lookup or len(lookup) != Fingerprint.FP_LEN:
    return abort(400)

  data = {'entries': []}
  q = StatusEntry.query.filter\
      (func.substr(StatusEntry.fingerprint, 0, Fingerprint.FP_SUBSTR_LEN) == lookup[:Fingerprint.FP_SUBSTR_LEN-1])
  q = q.order_by(StatusEntry.validafter.desc())
  entries = offset_limit(q)

  for e in entries:
    data['entries'].append({
      'fingerprint': e.fingerprint,
      'exit_addresses': [e.address],
      'valid_after': e.validafter.strftime('%Y-%m-%d %H:%M:%S'),
    })
    if e.nickname != 'Unnamed':
      data['entries'][-1]['nickname'] = e.nickname

  data['count'] = len(data['entries'])
  resp = jsonify(data)
  resp.status_code = 200
  return resp


if __name__ == '__main__':
  pass
