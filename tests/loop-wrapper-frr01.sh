#!/usr/bin/env bash

WRAPPER="/home/mickm/git/containerlab/lab-examples/frr01/tests/wrapper-frr01.sh"
INTERVAL=5  # wait 5 seconds 

while true; do
  echo
  echo "****************************"
  echo `date`
  echo "****************************"
  echo
  "$WRAPPER"
  sleep "$INTERVAL"
done
