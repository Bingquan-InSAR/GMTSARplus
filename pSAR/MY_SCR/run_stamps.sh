#!/usr/bin/bash

# STAMPS Time-Series InSAR Processing Script with Optional Atmospheric Correction
# Author: Bingquan Li and Ling Chang
# Created on: August 19, 2025
#
# Description:
#   This script automates time-series InSAR processing using STAMPS.
#   It supports optional atmospheric correction using either the linear model
#   or the GACOS model.
#
# Usage:
#   ./run_stamps.sh -a <method> [-g <gacos_path>] [-u <utc_time>]
#     -a : Atmospheric correction method (e.g., gacos or linear)
#     -g : Path to GACOS data (required if method is 'gacos')
#     -u : UTC time of satellite pass (required if method is 'gacos')
#
# Dependencies:
#   - STAMPS must be installed and configured
#   - GACOS data must be prepared if GACOS correction is selected
#
# Notes:
#   - The script runs STAMPS steps 1 to 5 for core processing
#   - Then applies atmospheric correction (GACOS or linear)
#   - Finally plots results and exports CSV output
###############################################################################usage() {
  echo "Usage: $0 [-a <atmo_correction_method>] [-g <gacos_path>] [-u <utc_time>]"
  echo "  -a: Atmospheric correction method (e.g., gacos)"
  echo "  -g: Path to GACOS data (required if -a is gacos)"
  echo "  -u: UTC time for the satellite pass (required if -a is gacos)"
  exit 1
}

# Default values
atmo_correction=""
gacos_path=""
utc_time=""

# Parse input arguments
while getopts ":a:g:u:" opt; do
  case ${opt} in
    a )
      atmo_correction=$OPTARG
      ;;
    g )
      gacos_path=$OPTARG
      ;;
    u )
      utc_time=$OPTARG
      ;;
    \? )
      usage
      ;;
  esac
done

# Check if required arguments are provided
if [ -z "$atmo_correction" ]; then
  usage
fi

# Check for GACOS-specific arguments if "gacos" is selected
if [ "$atmo_correction" == "gacos" ]; then
  if [ -z "$gacos_path" ] || [ -z "$utc_time" ]; then
    echo "Error: -g and -u options are required when -a is set to 'gacos'."
    usage
  fi
fi

cd merge_stamps/PS/
getparm
setparm density_rand 1
setparm n_cores 128
setparm unwrap_time_win 365
setparm scla_deramp y
stamps 1 5

echo "Atmospheric correction method: $atmo_correction"

if [ "$atmo_correction" == "gacos" ]; then
  echo "GACOS path: $gacos_path"
  echo "UTC time: $utc_time"
  setparm subtr_tropo y
  setparm tropo_method a_gacos
  getparm_aps
  setparm_aps UTC_sat $utc_time
  setparm_aps gacos_datapath $gacos_path
  aps_weather_model gacos 0 3
  stamps 6 8
  ps_plot_v v-dao a_gacos
  ps_plot_v vs-dao a_gacos
  ps_plot v-dao a_gacos ts
  export_csv
else
  setparm subtr_tropo y
  setparm tropo_method a_l
  aps_linear
  stamps 6 8
  ps_plot_v v-dao a_linear
  ps_plot_v vs-dao a_linear
  ps_plot v-dao a_linear ts
  export_csv
fi
