#!/bin/csh -f
#       $Id$
#
#
#    Xiaohua(Eric) XU, July 7, 2016
#
# Script for merging 3 subswaths TOPS interferograms and then unwrap and geocode. 
#
  if ($#argv != 2) then
    echo ""
    echo "Usage: merge_wrap_geocode_tops.csh inputfile config_file"
    echo ""
    echo "Note: Inputfiles should be as following:"
    echo ""
    echo "      Swath1_Path:Swath1_master.PRM:Swath1_repeat.PRM"
    echo "      Swath2_Path:Swath2_master.PRM:Swath2_repeat.PRM"
    echo "      Swath3_Path:Swath3_master.PRM:Swath3_repeat.PRM"
    echo "      (Use the repeat PRM which contains the shift information.)"
    echo "      e.g. ../F1/intf/2015016_2015030/:S1A20151012_134357_F1.PRM"
    echo ""
    echo "      Make sure under each path, the processed phasefilt.grd, corr.grd and mask.grd exist."
    echo "      Also make sure the dem.grd is linked. "
    echo ""
    echo "      config_file is the same one used for processing."
    echo ""
    echo "Example: merge_unwrap_geocode_tops.csh filelist batch.config"
    echo ""
    exit 1
  endif

  if (-f tmp_phaselist) rm tmp_phaselist
  if (-f tmp_corrlist) rm tmp_corrlist
  if (-f tmp_masklist) rm tmp_masklist

  if (! -f dem.grd ) then
    echo "Please link dem.grd to current folder"
    exit 1
  endif

  set region_cut = `grep region_cut $2 | awk '{print $3}'`

  # Creating inputfiles for merging
  foreach line (`awk '{print $0}' $1`)
    set now_dir = `pwd`
    set pth = `echo $line | awk -F: '{print $1}'`
    set prm = `echo $line | awk -F: '{print $2}'`
    set prm2 = `echo $line | awk -F: '{print $3}'`
    cd $pth
    set rshift = `grep rshift $prm2 | tail -1 | awk '{print $3}'`
    set fs1 = `grep first_sample $prm | awk '{print $3}'`
    set fs2 = `grep first_sample $prm2 | awk '{print $3}'`
    cp $prm tmp.PRM
    if ($fs2 > $fs1) then
      update_PRM tmp.PRM first_sample $fs2
    endif
    update_PRM tmp.PRM rshift $rshift
    cd $now_dir
    #
    echo $pth"tmp.PRM:"$pth"phasefilt.grd" >> tmp_phaselist
    echo $pth"tmp.PRM:"$pth"corr.grd" >> tmp_corrlist
    echo $pth"tmp.PRM:"$pth"mask.grd" >> tmp_masklist
    echo $pth"tmp.PRM:"$pth"display_amp.grd" >> tmp_amplist
    #
  end 

  set pth = `awk -F: 'NR==1 {print $1}' $1`
  set stem = `awk -F: 'NR==1 {print $2}' $1 | awk -F"." '{print $1}'`
  #echo $pth $stem

  echo ""
  echo "Merging START"
  #
  # updated by FWP, @SYSU, Guangzhou, 2021/06/08
  # 
  gmtsar_merge_redo.py $stem
  #
  #
  echo "Merging END"
  echo ""
  # 
  set iono = `grep correct_iono $2 | awk '{print $3}'`
  set skip_iono = `grep iono_skip_est $2 | awk '{print $3}'`
  if ($iono != 0 & $skip_iono == 0) then
    if (! -f ph_iono_orig.grd) then
      echo "Need ph_iono_orig.grd to correct ionosphere ..."
    else
      echo "Correcting ionosphere ..."
      gmt grdsample ph_iono_orig.grd -Rphasefilt.grd -Gtmp.grd
      gmt grdmath phasefilt.grd tmp.grd SUB PI ADD 2 PI MUL MOD PI SUB = tmp2.grd
      mv phase.grd phase_orig.grd
      mv tmp2.grd phasefilt.grd
      rm tmp.grd
    endif
  endif

  exit 0 
  #
  # below will be required saperatelly when all interferograms were merged...
