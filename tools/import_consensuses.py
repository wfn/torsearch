#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A semi-stub (to be called from shell, etc.) for importing our consensus documents (including status entries)
'''

import sys
sys.path.append('..')
from torsearch.importer import batch_import_consensuses

def main(args):
  path = args[1] if len(args) > 1 else '/home/kostas/priv/tordev/data/consensuses-2013-04'
  batch_import_consensuses(path)

if __name__ == '__main__':
  sys.exit(main(sys.argv))
