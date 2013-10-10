# NOTE: for many intents and purposes, torsearch/benchmark.py serves as a good
# reference and ground for unit-like tests. We use benchmark.py to inspect the
# backend.
# Here is more of a (useful) stub for proper unit tests, to be expanded later.

import unittest
from torsearch import onionoo_api as oapi

class TestOnionooAPISearch(unittest.TestCase):
  def setUp(self):
    self.fingerprints = []

  def test_default_search(self):
    consensus, results = oapi.get_results(args={'bogus': True})
    results = list(results) # iterator=>list
    self.assertEqual(len(results), oapi.UPPER_LIMIT)
    self.assertEqual(results[0].last_va, consensus.valid_after)

  def test_known_relays_in_results(self):
    known_relay_nicks = ['moria1', 'faravahar']
    for nick in known_relay_nicks:
      consensus, results = oapi.get_results(args={'search': nick})
      last_count = len(self.fingerprints)
      for r in results:
        if r.last_va == consensus.valid_after:
          self.fingerprints.append(r)
      self.assertTrue(last_count < len(self.fingerprints))

if __name__ == '__main__':
  unittest.main()
