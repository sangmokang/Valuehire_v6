#!/usr/bin/env bash
found=""
if false; then
  found=$(find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \))
fi
