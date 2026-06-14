#!/usr/bin/env bash
set -e

run_sbas.sh \
  --kml example_aoi.kml \
  --st 20220101 \
  --ed 20220501 \
  --rel_orbit  32\
  --tmpbase 24 \
  --rlook 20 \
  --azlook 4
