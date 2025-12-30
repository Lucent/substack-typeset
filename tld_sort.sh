#!/usr/bin/env bash
# sort by TLD, then domain (2nd-level), keeping original lines
awk '{
  u=$1
  sub(/^https?:\/\//,"",u)
  sub(/\/.*/,"",u)          # keep host only
  n=split(u,a,".")
  tld=a[n]
  dom=a[n-1]
  print tld "\t" dom "\t" $0
}' | sort -t $'\t' -k1,1 -k2,2 | cut -f3-

