#!/bin/sh

DEST="/home/z/p/tor/data/recent"
TS="/home/z/p/tor/ts"
VENV_ACTIVATE="/home/z/.virtualenvs/ts/bin/activate"

rsync -az metrics.torproject.org::metrics-recent/relay-descriptors/consensuses $DEST
. $VENV_ACTIVATE
PYTHONPATH=$TS python $TS/tools/import_consensuses.py $DEST
