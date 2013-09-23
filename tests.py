# NOTE: for many intents and purposes, torsearch/benchmark.py serves as a good
# reference and ground for unit-like tests. We use benchmark.py to inspect the
# backend.
# Here is more of a (useful) stub for proper unit tests, to be expanded later.

import unittest
from torsearch import onionoo_api as oapi

class TestOnionooAPISearch(unittest.TestCase):
  def setUp(self):
    pass

  def test_default_search(self):
    consensus, results = oapi.get_results(args={'bogus': True})
    results = list(results) # iterator=>list
    self.assertEqual(len(results), oapi.UPPER_LIMIT)
    self.assertEqual(results[0].last_va, consensus.valid_after)

if __name__ == '__main__':
  unittest.main()
