#!/usr/bin/env bash 

for f in *.dat ; do echo "$f" ; ./plot-ordered.py $f > /dev/null ; done
