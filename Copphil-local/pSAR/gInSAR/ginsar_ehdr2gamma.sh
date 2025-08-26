#!/usr/bin/env bash 
#
# Created by Feng,W.P.,@UoG, 2012-09-27
####################################################################
# Main code
####################################################################
if [ $# -lt 2 ]; then
   cat << END
   $0 <dem_hdr> <dem_file> [outname, root] 
   ++++++++++++++++++++++++++++++++++++++++++++++
   In default, INTEGER*2 will be suggested to apply to the input file
   #
   by Feng, W.P. @NRCan, 2015-12-10

END
exit -1
fi
#
demrsc=$1
demfile=$2
#
if [ $# -ge 3 ]; then
   #
   demoutroot=$3
   #
else
   demoutroot="gdem"
fi
#
demout=$demoutroot".dem"
dempar=$demout"_par"
#
ext=`echo $demfile | gawk 'BEGIN {FS="."}{print $NF}'`
#
if [ "$ext" == "tif" ]; then
   # 
   # Convert Geotiff to EHdr format
   #
   gdal_translate -of EHdr $demfile EHDr.img
   demrsc=EHDr.hdr
fi
#
dataformat="INTEGER*2"
flag=2
width=`grep NCOLS  $demrsc  | gawk '{print $2}'`
length=`grep NROWS  $demrsc | gawk '{print $2}'`
xsize=`grep XDIM   $demrsc  | gawk '{printf "%30.20f \n", $2}'`
ysize=`grep YDIM   $demrsc  | gawk '{printf "%30.20f \n", -1*$2}'`
xpos=`grep ULXMAP $demrsc   | gawk '{printf "%30.20f \n", $2}'`
ypos=`grep ULYMAP $demrsc   | gawk '{printf "%30.20f \n", $2}'`
informat=`grep PIXELTYPE $demrsc| gawk '{print $2}'`
#
if [ "$informat" == "FLOAT" ]; then
   dataformat="REAL*4"
   flag=4
fi
echo " swap_bytes $demfile $demout $flag"
swap_bytes $demfile $demout $flag
#
cat >$dempar <<EOL
Gamma DIFF&GEO DEM/MAP parameter file
title: EQA
DEM_projection:          EQA	 
data_format:             $dataformat 
DEM_hgt_offset:          0 
DEM_scale:               1.00000
width:                  $width 
nlines:                 $length 
corner_lat:     $ypos  decimal degrees
corner_lon:     $xpos  decimal degrees
post_lat:       $ysize  decimal degrees
post_lon:       $xsize  decimal degrees

ellipsoid_name: WGS 84
ellipsoid_ra:        6378137.000   m
ellipsoid_reciprocal_flattening:  298.2572236

datum_name: WGS 1984
datum_shift_dx:              0.000   m
datum_shift_dy:              0.000   m
datum_shift_dz:              0.000   m
datum_scale_m:         0.00000e+00
datum_rotation_alpha:  0.00000e+00   arc-sec
datum_rotation_beta:   0.00000e+00   arc-sec
datum_rotation_gamma:  0.00000e+00   arc-sec
datum_country_list Global Definition, WGS84, World
EOL
