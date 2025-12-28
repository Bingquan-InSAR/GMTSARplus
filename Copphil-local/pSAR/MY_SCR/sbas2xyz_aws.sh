#!/usr/bin/bash
###############################################################################
# GMTSAR Post-Processing Script
# Created by Bingquan Li and Ling Chang
# Purpose:
#   Extract elevation, coherence, heading, incidence, and time-series displacements,
#   and compute velocity standard deviation for InSAR results.
#   Outputs XYZ files and gridded products for further analysis.
###############################################################################
#gmt grdsample ../topo/dem.grd `gmt grdinfo vel_ll.grd -I3.5s/3s` -Gdem_cut.grd
#gmt grdsample ../topo/dem.grd -Gdem_cut.grd -Rvel_ll.grd -I0.000972222222156/0.000833333333355

inc=$(gmt grdinfo -I vel_ll.grd | sed 's/^-I//' | awk -F/ '{
  x=$1; y=$2;
  if (x ~ /s$/){sub(/s$/,"",x); x=x/3600}
  else if (x ~ /m$/){sub(/m$/,"",x); x=x/60}
  else {sub(/[a-zA-Z]$/,"",x)}
  if (y ~ /s$/){sub(/s$/,"",y); y=y/3600}
  else if (y ~ /m$/){sub(/m$/,"",y); y=y/60}
  else {sub(/[a-zA-Z]$/,"",y)}
  printf "-I%.15f/%.15f", x, y
}')

gmt grdsample ../topo/dem.grd -Gdem_cut.grd -Rvel_ll.grd $inc

gmt grd2xyz vel_ll.grd -s > vel_ll.xyz 

gmt grdtrack vel_ll.xyz -Gdem_cut.grd > height1.xyz
awk '{print $1, $2, $4}' height1.xyz > height.xyz
rm height1.xyz dem_cut.grd

#cohernece
ls ../merge/*/corr_ll.grd > corr_list
stack.csh corr_list 1 corr.grd corr_std.grd
gmt grd2xyz corr.grd  -s > corr.xyz 

#heading and incidence
pSAR_gmtsar_s1insar2roi_aws.py ../merge T0 ../DATA/S1_ZIP_RAW 4
grep "HEADING_DEG" T0/geo_T*.azi.rsc | awk '{print $2}' > heading
grep "INCIDENCE" T0/geo_T*.azi.rsc| awk '{print $2}' >incidence


ls -tdr ../DATA/S1_ZIP_RAW//*SAFE>zip_list
while read -r line; do
    date=$(echo "$line" | sed -E 's/.*_([0-9]{8})T.*/\1/')
    echo "$date"
done < zip_list >date


disp_list=()

# Read through the scene.tab file line by line
while read -r line; do
    # Extract the first column (id)
    id=$(echo $line | awk '{print $1}')
    
    # Create the grd filename
    grd_filename="disp_${id}.grd"
    
    # Add the grd_filename to the disp_list array
    disp_list+=("$grd_filename")
done < scene.tab

# Write the contents of disp_list to a file
for grd_file in "${disp_list[@]}"; do
    echo "$grd_file" >> disp_list
done

# Loop through each .grd file listed in disp_list and data_list
paste disp_list date | while IFS=$'\t' read -r grd_file date; do
    # Check if the .grd file exists
    if [[ -f "$grd_file" ]]; then
        # Call GMTSAR_proj_ra2ll.csh with the .grd file
        GMTSAR_proj_ra2ll.csh ../merge/topo/trans.dat "$grd_file" "${grd_file%.*}_ll.grd"
        
        # Run grd2xyz to convert the new _ll.grd to an XYZ format
        gmt grd2xyz "${grd_file%.*}_ll.grd" -s > "D${date}.xyz"
        
    else
        echo "File $grd_file not found!"
    fi
done

#range and azimuth
proj_ll2ra_ascii.csh ../merge/topo/trans.dat vel_ll.xyz vel_ra.xyz

rmse.py
gmt grd2xyz rmse_ll.nc -s > rmse.xyz
