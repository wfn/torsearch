#!/bin/bash
# ./import_year_of_descriptors.sh /path/to/basedir/of/data 2012
# assumes that python's env (e.g. via venv) is properly set
for i in `seq -f "%02g" 1 12`; do
  echo "=> Importing data for $2-$i..."
  python import_descriptors.py $1/server-descriptors-$2-$i;
done
