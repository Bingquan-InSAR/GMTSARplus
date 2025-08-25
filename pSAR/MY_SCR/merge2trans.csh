#!/bin/csh -f
#       $Id$
#
#
#    Xiaohua(Eric) XU, July 7, 2016
#
# Script for merging 3 subswaths TOPS interferograms and then unwrap and geocode. 
#
  if ($#argv != 1) then
    echo ""
    echo "Usage: merge2trans.csh config_file unwrapping_threshold"
    echo ""
    echo "Note: Inputfiles should be as following:"
    echo ""
    echo "      (Use the repeat PRM which contains the shift information.)"
    echo "      e.g. ../F1/intf/2015016_2015030/:S1A20151012_134357_F1.PRM"
    echo ""
    echo "      Make sure under each path, the processed phasefilt.grd, corr.grd and mask.grd exist."
    echo "      Also make sure the dem.grd is linked. "
    echo ""
    echo "      config_file is the same one used for processing."
    echo ""
    echo "Example: merge2trans.csh filelist batch.config"
    echo ""
    exit 1
  endif


  if (! -f dem.grd ) then
    echo "Please link dem.grd to current folder"
    exit 1
  endif
  #
  set region_cut = `grep region_cut $1 | awk '{print $3}'`
  # ionospheric correction
  #
  # settings below are for specifying the paths of files that will be required in the following sections
  # 
  set in_list = 'tmp.filelist'
  if (-e $in_list) then
     set pth = `head -n 1 $in_list | awk -F: '{print $1}'`
  else
     echo " ERR: No tmpp_phaselist is available!!"
     exit -1
  endif
  #
  # 
  # set stem = `ls -t $pth/supermaster.PRM|head -n 1| awk -F/ '{print $(NF)}' | awk -F.PRM '{print $1}'`
  set stem = 'supermaster'
  if (! -e $stem.PRM ) then
     # cp $pth/$stem.PRM .
     echo " ERR: no $stem.PRM was available!!"
  endif
  
  #
  # echo $pth $stem
  # This step is essential, cut the DEM so it can run faster.
  # 
  if (! -f trans.dat) then
    if (-f ../topo/trans.dat) then
       ln -s ../topo/trans.dat .
    endif
  else
    #
    set fsize = `wc -c trans.dat|awk '{print $1}'`
    if ( "$fsize" == "0" ) then
       echo " ERR: trans.dat is invalid and is being deleted now..."
       rm trans.dat -f
    endif
  endif
  #
  #
  if (! -f trans.dat) then
    #
    set led_swath = `grep led_file $pth$stem".PRM" | awk '{print $3}' |awk -F.LED '{print $1 }'|awk -F_ '{print $(NF)}'`
    set led = `grep led_file $pth$stem".PRM" | awk '{print $3}'`
    set fullpathled = "../../$led_swath/raw/$led"
    #
    cp $fullpathled .
    echo "Recomputing the projection LUT..."
    #
    # Need to compute the geocoding matrix with supermaster.PRM with rshift set to 0
    set rshift = `grep rshift $stem".PRM" | tail -1 | awk '{print $3}'`
    update_PRM $stem".PRM" rshift 0
    gmt grd2xyz --FORMAT_FLOAT_OUT=%lf dem.grd -s | SAT_llt2rat $stem".PRM" 1 -bod > trans.dat
   
    # Set rshift back for other usage
    update_PRM $stem".PRM" rshift $rshift
    #
    if (! -f ../topo/trans.dat) then
       # ln -s $PWD/trans.dat ../topo/.
       mv trans.dat ../topo/.
       ln -s $PWD/../topo/trans.dat .
    endif
  endif


