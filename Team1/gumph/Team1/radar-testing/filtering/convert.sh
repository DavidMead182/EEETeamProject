#!/usr/bin/env bash 


for f in *.csv ; do nf=`echo $f | cut -d '.' -f 1` ; sed 's/,/ /g' $f | tail -n +10 > "$nf.dat" ; done
