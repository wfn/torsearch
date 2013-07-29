#!/bin/bash
# ./get_years_data.sh 2013
for i in `seq -f "%02g" 1 12`; do
  echo "=> Getting data for $1-$i..."
  bash ./months_data.sh $1-$i;
done
