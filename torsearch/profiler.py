#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cProfile as profiler
import gc, pstats, time

def profile(fn):
  def wrapper(*args, **kw):
    elapsed, stat_loader, result = _profile("profiler_output.log", fn, *args, **kwargs)
    stats = stat_loader()
    stats.sort_stats('cumulative')
    stats.print_stats()
    #stats.print_callers()
    return result
  return wrapper

def _profile(filename, fn, *args, **kwargs):
  load_stats = lambda: pstats.Stats(filename)
  gc.collect()

  began = time.time()
  profiler.runctx('result = fn(*args, **kw)', globals(), locals(),
                  filename=filename)
  ended = time.time()

  return ended - began, load_stats, locals()['result']

if __name__ == '__main__':
  pass
