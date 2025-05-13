#!/usr/bin/env bash 

for f in *.dat ; do echo "$f" ; ./plot.py $f > /dev/null ; done
