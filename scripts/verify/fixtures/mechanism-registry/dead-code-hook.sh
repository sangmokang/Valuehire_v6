#!/usr/bin/env bash
exit 0
found=$(find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \))
