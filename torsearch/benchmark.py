#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''a very simple way to benchmark a (e.g.) ORM that is generic enough to be (maybe) reused for multiple projects and problem domains.
note that profiler.py contains ways to extract much more information about low-level bottlenecks. here, we are simply concerned with the overall query time.
if we want, we can also run our EXPLAIN ANALYZEr.
if we specify not to use it (default when instantiating Benchmark objects), the tool is generic enough to be used outside of an ORM context.
'''

import os
import sys
import time
import logging
from logging import Formatter, FileHandler
from torsearch import query_info, onionoo_api
from config import basedir

def get_logger(filename, absolute_path=False):
  logger = logging.getLogger('torsearch.benchmark')
  log_handler = FileHandler(
    (os.path.join(basedir, filename)) if not absolute_path else filename
  )
  log_formatter = Formatter('%(asctime)s %(levelname)s %(message)s')
  log_handler.setFormatter(log_formatter)
  logger.addHandler(log_handler)
  logger.setLevel(logging.DEBUG)
  return logger

class Benchmark(object):
  '''a simple placeholder + benchmarker that stores:
  name -- a title / short description of this benchmark.
  testfunc -- the thing to be benchmarked.
  params -- a list of lists of parameters.
    each external list is a different way to call the testfunc. to run only a single case of testfunc, params should be [[param1, param2, ...]]
  output_filename -- filename to write output to.
  n_runs -- how many times to run each case of testfunc. default = n_runs will be supplied in run().
  run_in_order -- whether to run each case in the order specified in params.
    if False, will run as (e.g. if n_runs=3) [case1, case1, case1, case2, case2, case2, . . .]
  run_explain -- whether to expect a query object as the return value, and to feed it into torsearch.query_info.run_explain()
  '''

  default_output_filename = 'benchmarks.log'

  def __init__(self, name, testfunc, params=[[]], output_filename=default_output_filename, n_runs=None, run_in_order=True, run_explain=False):
    self.name = name
    self.testfunc = testfunc
    self.params = params
    self.n_runs = n_runs
    self.run_in_order = run_in_order
    self.run_explain = run_explain
    self.logger = get_logger(output_filename)

  def run(self, run_name, n_runs=None, run_in_order=None):
    '''run the benchmark (all the testfunc cases.)
    run_name -- the name of this particular run.
    the idea is to call this benchmark multiple times, perhaps on different machines, or with different test conditions (e.g. run_name='fresh database restart')
    '''
    if n_runs == None: # explicit check
      n_runs = self.n_runs
    if run_in_order == None:
      run_in_order = self.run_in_order

    self.logger.info('### Benchmark: ' + self.name + ' (%s)', self.testfunc.__name__)
    self.logger.info('Run case: ' + run_name)
    total_time = 0.0
    for n, paramset in enumerate(self.params):
      self.logger.info('%d) Parameters: ' + str(paramset), n+1)
      if 1: #run_in_order: # TODO: we're not using differences in run_in_order for torsearch
                           # but it would be good idea to try that. TODO: Implement both run_in_order cases.
        for i in range(n_runs):
          t1 = time.time()
          result = self.testfunc(*paramset)
          if run_explain: # True => the actual execution is upon result.all()
            # (we want the buffer info every time we run this, but let's output the query statement only once)
            query_info.run_explain(result, analyze=True, buffers=True, output_statement=(i==0), output_explain=True,\
              debug_log=self.logger.info, warning_log=self.logger.warning)
          t2 = time.time()
          total_time += (t2 - t1)
          self.logger.info(' ==> %d) %d) time: %s', n+1, i+1, t2 - t1)
    logger.info('End of benchmark. Total time: %s', total_time)
    return total_time


# here we define a simple way of constructing a list of the benchmarks we actually want to run.
torsearch_orm_benchmarks =\
  {
    'raw sql - search for nickname': # name of the benchmark to test
      [
        # each benchmark contains the function to call as its first item in the external list
        onionoo_api.sql_search_nickname,
        # the remainder of the list is parameter lists / call cases (each internal list can contain any number of items)
        ['moria2'], ['moria1'], ['gabelmoo'], ['cekuolis'], ['torland1'], ['unknown'], ['default']
      ] # /benchmark
  }

def get_torsearch_benchmarks(benchmarks=torsearch_orm_benchmarks):
  '''useful for manual inspection / tinkering from the console:
  >>> from torsearch import benchmark as b
  >>> bmarks = b.get_torsearch_benchmarks()
  >>> for bmark in bmarks:
  >>>   print 'Running', bmark.name, '...',
  >>>   time = bmark.run('test run', n_runs=5)
  >>>   print time, '(', time / (float) 5, 'per run )'
  '''

  objects = []
  for name, data in benchmarks.iteritems():
    func = data[0]
    paramlists = data[1:]
    #yield Benchmark(name, func, params=paramlists, run_explain=True)
    objects.append(Benchmark(name, func, params=paramlists, run_explain=True))
  return objects

def run_torsearch_benchmarks(run_name, n_runs, run_in_order=True, benchmarks=torsearch_orm_benchmarks):
  for benchmark in get_torsearch_benchmarks(benchmarks):
    print 'Running benchmark:', benchmark.name
    benchmark.run(run_name, n_runs=n_runs, run_in_order=run_in_order)

if __name__ == '__main__':
  # TODO: provide a --help menu, etc. if we end up using this outside of (pre)alpha-version development
  #run_torsearch_benchmarks(sys.argv[1] if len(sys.argv) > 1 else 'test run', sys.argv[2] if len(sys.argv) > 2 else 5)
  # better simply use
  # >>> from torsearch import benchmark
  # >>> benchmark.run_torsearch_benchmarks('my test run case', 5)
  pass

