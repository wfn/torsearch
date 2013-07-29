#!/bin/bash
# ./get_months_data.sh 2013-06
for what in server-descriptors consensuses extra-infos; do
  echo "  => Getting and extracting $what..."
  wget -c https://metrics.torproject.org/data/$what-$1.tar.bz2
  tar xfj $what-$1.tar.bz2
  rm $what-$1.tar.bz2; # comment out if needed (and move the semicolon!)
done
