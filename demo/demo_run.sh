#!/usr/bin/env bash
set -e

run_sbas.sh \
  --kml demo/example_aoi.kml \
  --st 20220101 \
  --ed 20220501 \
  --rel_orbit  \
  --tmpbase 32 \
  --rlook 20 \
  --azlook 4
