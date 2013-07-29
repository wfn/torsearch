#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A semi-stub (to be called from shell, etc.) for importing our server descriptors
'''

import sys
sys.path.append('..')
from torsearch.importer import batch_import_descriptors

def main(args):
  path = args[1] if len(args) > 1 else '/home/kostas/priv/tordev/data/server-descriptors-2013-04'
  batch_import_descriptors(path)

if __name__ == '__main__':
  sys.exit(main(sys.argv))
