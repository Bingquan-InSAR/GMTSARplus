#!/bin/csh -f
###############################################################################
# Sentinel-1 TOPS Merge & Unwrap Script for SBAS Interferograms
# Created by Xiaohua (Eric) Xu on July 7, 2016
# Updated by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose:
#   Merge Sentinel-1 TOPS-mode interferograms from three subswaths (F1/F2/F3)
#   and perform phase unwrapping and geocoding for each interferometric pair,
#   supporting SBAS time-series InSAR processing.
###############################################################################

  if ($#argv != 4 && $#argv != 5) then
    echo ""
    echo "Usage: merge_batch.csh inputfile config_file [det_stitch]"
    echo ""
    echo "Note: Inputfiles should be as following:"
    echo ""
    echo "      IF1_Swath1_Path:master.PRM:repeat.PRM,IF1_Swath2_Path:master.PRM:repeat.PRM,IF1_Swath3_Path:master.PRM:repeat.PRM"
    echo "      IF2_Swath1_Path:master.PRM:repeat.PRM,IF2_Swath2_Path:master.PRM:repeat.PRM,IF1_Swath3_Path:master.PRM:repeat.PRM"
    echo "      (Use the repeat PRM which contains the shift information.)"
    echo "      e.g. ../F1/intf_all/2015092_2015128/:S1A20150403_ALL_F1.PRM:S1A20150509_ALL_F1.PRM,../F2/intf_all/2015092_2015128/:S1A20150403_ALL_F2.PRM:S1A20150509_ALL_F2.PRM,../F3/intf_all/2015092_2015128/:S1A20150403_ALL_F3.PRM:S1A20150509_ALL_F3.PRM"
    echo ""
    echo "      Make sure under each path, the processed phasefilt.grd, corr.grd and mask.grd exist."
    echo "      Also make sure the dem.grd is linked. "
    echo "      If trans.dat exits, recomputation of projection matrix will not proceed."
    echo "      The master image of firet line should be the super_master."
    echo ""
    echo "      config_file is the same one used for processing."
    echo ""
    echo "      set det_stitch to 1 if you want to calculate stitching position based on the NaN area in the grids"
    echo ""
    echo "Example: merge_batch.csh filelist batch.config"
    echo ""
    exit 1
  endif

  if (! -f dem.grd) then
    echo "dem.grd is required ..."
    exit 1
  endif
  if ($#argv == 6) then
    set det_stitch = 1
  else
    set det_stitch = ""
  endif
  set master = $5
  set input_file = $1
  awk 'END{print $0}' $input_file | awk -F, '{for (i=1;i<=NF;i++) print "../"$i}' | awk -F: '{print $1$2}'> tmpm.filelist 

  set now_dir = `pwd`


  foreach line (`awk '{print $0}' $input_file`)
    set dir_name = `echo $line | awk -F, '{print $1}' | awk -F: '{print $1}' | awk -F"/" '{print $(NF-1)}'`

    rm -rf $dir_name
    mkdir $dir_name
    cd $dir_name
    
    echo $line | awk -F, '{for (i=1;i<=NF;i++) print "../"$i}' > tmp.filelist
    paste ../tmpm.filelist tmp.filelist | awk '{print $1","$2}' > tmp
    rm tmp.filelist
    
    foreach f_name (`awk '{print $0}' < tmp`)
        set mm = `echo $f_name | awk -F, '{print $1}'`
        set pth = `echo $f_name | awk -F, '{print $2}' | awk -F: '{print $1}'`
        set f1 = `echo $f_name | awk -F, '{print $2}' | awk -F: '{print $2}'`
        set f2 = `echo $f_name | awk -F, '{print $2}' | awk -F: '{print $3}'`
        
        cp $mm ./supermaster.PRM
        set rshift = `grep rshift $pth$f1 | tail -1 | awk '{print $3}'`
        update_PRM supermaster.PRM rshift $rshift
        set fs1 = `grep first_sample supermaster.PRM | awk '{print $3}'`
        set fs2 = `grep first_sample $pth$f1 | awk '{print $3}'`
        if ($fs2 > $fs1) then
          update_PRM supermaster.PRM first_sample $fs2
        endif
        cp supermaster.PRM $pth
        echo $pth":supermaster.PRM:"$f2 >> tmp.filelist
    end
    
    if (-f ../trans.dat) ln -s ../trans.dat .
    if (-f ../raln.grd) ln -s ../raln.grd .
    if (-f ../ralt.grd) ln -s ../ralt.grd .
    ln -s ../dem.grd .
    ln -s ../$2 .
    rm tmp
    if ("$3" != "None") then
       echo "merge_unwrap_geocode_tops_ps.csh tmp.filelist $dir_name $det_stitch $master"
       merge_unwrap_geocode_tops_ps.csh tmp.filelist $dir_name $master
    else
       cp ../../$4/stamps/$dir_name/real.grd ../"real_"$dir_name".grd"
       cp ../../$4/stamps/$dir_name/imag.grd ../"imag_"$dir_name".grd"
       cp ../../$4/topo/trans.dat ../trans.dat
       cp ../../$4/topo/master.PRM ../master.PRM
    endif
       
    if (! -f ../trans.dat && -f trans.dat) then
      mv trans.dat ../
      ln -s ../trans.dat .
    endif
    
    if (! -f ../raln.grd && -f raln.grd) then
      mv raln.grd ../
      ln -s ../raln.grd .
    endif
    if (! -f ../ralt.grd && -f raln.grd) then
      mv ralt.grd ../
      ln -s ../ralt.grd .
    endif

    cd $now_dir

  end
  

