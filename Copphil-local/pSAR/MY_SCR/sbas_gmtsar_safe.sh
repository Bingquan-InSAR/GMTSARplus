#!/bin/bash

###############################################################################
# SBAS Processing Script for GMTSAR
# Created by Bingquan Li and Ling Chang on July 10, 2025
# Purpose: Perform SBAS time-series processing using GMTSAR and export CSV results
###############################################################################

# Step 1: Create SBAS processing directory and move into it
rm -rf sbas
rm -rf proj_ra2ll.info.sh
mkdir sbas
cd sbas

# Step 2: Copy necessary configuration files
# proj_ra2ll.info.sh is used later for geocoding results
cp ../merge/proj_ra2ll.info.sh ../
cp ../merge/batch_config.cfg ./

# Step 3: Generate intf.tab and scene.tab using prep_sbas.csh
# Inputs include interferogram list, baseline table, and unwrapped/correlation file names
prep_sbas.csh ../F2/intf.in ../F2/baseline_table.dat ../merge/ unwrap_detrended.grd corr.grd

# Step 4: Sort scene.tab by time
sort -n scene.tab -o scene.tab

# Step 5: Filter intf.tab to remove lines corresponding to non-existent directories
valid_dirs=$(ls -d ../merge/20*_* 2>/dev/null | xargs -n1 basename)
> tmp

while read -r line; do
    dir_name=$(echo "$line" | grep -oE '20[0-9]{5}_20[0-9]{5}')

    if echo "$valid_dirs" | grep -qx "$dir_name"; then
        echo "$line" >> temp
    fi
done < intf.tab

mv temp intf.tab

# Step 6: Count number of interferograms and scenes
intf_num=$(wc -l < intf.tab)
scene_num=$(wc -l < scene.tab)

# Step 7: Get grid size (nx, ny) from the first corr.grd file listed in intf.tab
first_line=$(head -n 1 intf.tab)
corr_grd=$(echo "$first_line" | awk '{print $2}')
read nx ny <<< $(gmt grdinfo "$corr_grd" -C | awk '{print $10, $11}')

# Step 8: Run SBAS processing
sbas intf.tab scene.tab $intf_num $scene_num $nx $ny -wavelength 0.0554658 -atm 1

# Step 9: Project velocity map to geographic coordinates
GMTSAR_proj_ra2ll.csh ../merge/topo/trans.dat vel.grd vel_ll.grd

# Step 10: Export results to CSV format (assumes these scripts are in $PATH or current directory)
sbas2xyz_safe.sh
export_csv.py


