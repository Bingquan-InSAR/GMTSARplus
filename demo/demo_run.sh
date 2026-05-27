#!/usr/bin/env bash
set -e

run_sbas.sh \
  --kml demo/example_aoi.kml \
  --st 20240101 \
  --ed 20240131 \
  --rel_orbit 11 \
  --tmpbase 12 \
  --rlook 20 \
  --azlook 4
