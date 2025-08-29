#!/usr/bin/env bash
###############################################################################
# SBAS Processing Script for GMTSAR (Parameterized Version)
# Usage: bash run_sbas_f.sh <F_index_or_IW>
# Example: bash run_sbas_f.sh 2   # will use F2 directory and proj_ra2ll_iw2.info.sh
#
# Author: Bingquan Li & Ling Chang
# Date:   Parametrized version - August 2025
###############################################################################

set -euo pipefail

########################################
# 1. Read arguments and basic checks
########################################
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <F_index_or_IW>   # Example: 2 for F2 / iw2"
  exit 1
fi

IDX="$1"                      # Example: 2
F_DIR="../F${IDX}"            # e.g., ../F2
IW_INFO="proj_ra2ll_iw${IDX}.info.sh"   # proj_ra2ll_iw2.info.sh
TRANS_DAT="${F_DIR}/topo/trans.dat"

########################################
# 2. Prepare working directory
########################################
rm -rf sbas
mkdir -p sbas
cd sbas

# Check existence of essential input files
required_files=(
  "${F_DIR}/intf.in"
  "${F_DIR}/baseline_table.dat"
  "${F_DIR}/batch_config.cfg"
  "${TRANS_DAT}"
)
for f in "${required_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: Required file not found: $f"
    exit 2
  fi
done



# Copy batch_config.cfg from F directory to current sbas directory
cp -f "${F_DIR}/batch_config.cfg" ./

########################################
# 3. Generate SBAS input tables
########################################
# prep_sbas.csh arguments:
#   <intf.in> <baseline_table.dat> <path_to_interferograms> <unwrap_file> <correlation_file>
prep_sbas.csh \
  "${F_DIR}/intf.in" \
  "${F_DIR}/baseline_table.dat" \
  "${F_DIR}/intf_all/" \
  unwrap_detrended.grd \
  corr.grd

# Sort scene.tab by acquisition time
sort -n scene.tab -o scene.tab



########################################
# 5. Count number of interferograms/scenes and get grid size
########################################
intf_num=$(wc -l < intf.tab)
scene_num=$(wc -l < scene.tab)
if (( intf_num == 0 || scene_num == 0 )); then
  echo "ERROR: intf.tab or scene.tab is empty."
  exit 3
fi

# Get the correlation grid file path from the first interferogram
first_line=$(head -n 1 intf.tab)
corr_grd=$(echo "$first_line" | awk '{print $2}')
if [[ ! -f "$corr_grd" ]]; then
  # If path is relative, try adding the F_DIR prefix
  if [[ -f "${F_DIR}/${corr_grd}" ]]; then
    corr_grd="${F_DIR}/${corr_grd}"
  else
    echo "ERROR: Correlation grid not found: ${corr_grd}"
    exit 4
  fi
fi

# Extract grid size (nx, ny) from correlation grid
read -r nx ny <<< "$(gmt grdinfo -C "$corr_grd" | awk '{print $10, $11}')"
if [[ -z "${nx:-}" || -z "${ny:-}" ]]; then
  echo "ERROR: Failed to read nx/ny from $corr_grd"
  exit 5
fi

########################################
# 6. Run SBAS processing
########################################
# Sentinel-1 wavelength = 0.0554658 m
# -atm 1 enables atmospheric filtering
sbas intf.tab scene.tab "$intf_num" "$scene_num" "$nx" "$ny" -wavelength 0.0554658 -atm 1

########################################
# 7. Project velocity map to geographic coordinates
########################################
GMTSAR_proj_ra2ll.csh "${TRANS_DAT}" vel.grd vel_ll.grd

########################################
# 8. Export results to CSV
########################################
# sbas2xyz_aws.sh: Convert SBAS result grids to XYZ format
# export_csv.py: Convert XYZ to CSV format
sbas2xyz_burst.sh F${IDX}
export_csv.py
