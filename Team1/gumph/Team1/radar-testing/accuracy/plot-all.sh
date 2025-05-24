#!/usr/bin/env bash 

for f in *.dat ; do echo "$f" ; ./$1 $f > /dev/null ; done
