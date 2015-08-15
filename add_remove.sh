#!/bin/bash

while read line
do
  if [ "x$line" != "x" ]; then
    echo "rm -f \"$line\""
  else
    echo ""
  fi
done
