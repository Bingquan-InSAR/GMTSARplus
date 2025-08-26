#!/bin/csh -f
###############################################################################
# Script for merging and geocoding TOPS interferograms
# Created by Xiaohua (Eric) Xu on July 7, 2016
# Updated by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose: Merge multi-subsample interferograms, unwrap phase, and geocode.
# Used in SBAS processing with Sentinel-1 TOPS data (GMTSAR).
###############################################################################
  set master = $3
  if (-f tmp_imagephaselist) rm tmp_imagphaselist
  if (-f tmp_realphaselist) rm tmp_realhaselist

  if (! -f dem.grd ) then
    echo "Please link dem.grd to current folder"
    exit 1
  endif

  if ($#argv == 4) then
    set det_stitch = $4
    set n1 = 0
    set n2 = 0
  else
    set det_stitch = 0
    set n1 = ""
    set n2 = ""
  endif
 #set det_stitch = 1
 #set region_cut = `grep region_cut $2 | awk '{print $3}'`

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
    
    echo $pth"tmp.PRM:"$pth"imag.grd" >> tmp_imagphaselist
    echo $pth"tmp.PRM:"$pth"real.grd" >> tmp_realphaselist
    

  end 

  set pth = `awk -F: 'NR==1 {print $1}' $1`
  set stem = `awk -F: 'NR==1 {print $2}' $1 | awk -F"." '{print $1}'`
  
  
  echo "Merging START"
  if ($det_stitch == 1) then
    echo "Calculating valid starting columns of data ..."
    set nl = `wc -l $1 | awk '{print $1}'`
    echo $nl
    if ($nl == 2) then
      set pth2 = `head -1 $1 | awk -F: '{print $1}'`
      set near1 = `grep near $pth2"tmp.PRM" | awk '{print $3}'`
      set rng1 = `grep num_rng_bins $pth2"tmp.PRM" | awk '{print $3}'`
      set fs = `grep rng_samp_rate $pth2"tmp.PRM" | tail -1 | awk '{print $3}'`
      gmt grdcut $pth2"real.grd" -Z+N -Gtmp.grd
      set xm1 = `gmt grdinfo $pth2"real.grd" -C | awk '{print $3}'`
      set xc1 = `gmt grdinfo tmp.grd -C | awk '{print $3}'`
      set incx = `gmt grdinfo tmp.grd -C | awk '{print $8}'`
      set n12 = `echo $xm1 $xc1 $incx | awk '{printf("%d",($1-$2)/$3)}'`
      set pth2 = `tail -1 $1 | awk -F: '{print $1}'`
      set near2 = `grep near $pth2"tmp.PRM" | awk '{print $3}'`
      gmt grdcut $pth2"real.grd" -Z+N -Gtmp.grd
      set x01 = `gmt grdinfo tmp.grd -C | awk '{print $2}'`
      set incx = `gmt grdinfo tmp.grd -C | awk '{print $8}'`
      set n21 = `echo $x01 $incx | awk '{printf("%d",$1/$2)}'`
      set ovl12 = `echo $near1 $near2 $fs $rng1 $incx | awk '{printf("%d",($4-($2-$1)/(299792458.0/$3/2))/$5)}'`
      set n1 = `echo $n12 $n21 $ovl12 | awk '{printf("%d",($3-$1-$2)/2+$2)}'`
      set n2 = 0
      if ($n1 <= 0) then
          echo "WARNING: Stitching position estimated to be zero"
          echo "Check merged grids carefully"
          set n1 = ""
          set n2 = ""
      endif
      rm tmp.grd
    else if ($nl == 3) then
      echo "1"
      set pth2 = `head -1 $1 | awk -F: '{print $1}'`
      set near1 = `grep near $pth2"tmp.PRM" | awk '{print $3}'`
      set rng1 = `grep num_rng_bins $pth2"tmp.PRM" | awk '{print $3}'`
      set fs = `grep rng_samp_rate $pth2"tmp.PRM" | tail -1 | awk '{print $3}'`
      gmt grdcut $pth2"real.grd" -Z+N -Gtmp.grd
      set xm1 = `gmt grdinfo $pth2/real.grd -C | awk '{print $3}'`
      set xc1 = `gmt grdinfo tmp.grd -C | awk '{print $3}'`
      set incx = `gmt grdinfo tmp.grd -C | awk '{print $8}'`
      set n12 = `echo $xm1 $xc1 $incx | awk '{printf("%d",($1-$2)/$3)}'`

      set pth2 = `head -2 $1 | tail -1 | awk -F: '{print $1}'`
      set near2 = `grep near $pth2"tmp.PRM" | awk '{print $3}'`
      set rng2 = `grep num_rng_bins $pth2"tmp.PRM" | awk '{print $3}'`
      gmt grdcut $pth2"real.grd" -Z+N -Gtmp.grd
      set x02 = `gmt grdinfo tmp.grd -C | awk '{print $2}'`
      set incx = `gmt grdinfo tmp.grd -C | awk '{print $8}'`
      set n21 = `echo $x02 $incx | awk '{printf("%d",$1/$2)}'`
      set ovl12 = `echo $near1 $near2 $fs $rng1 $incx | awk '{printf("%d",($4-($2-$1)/(299792458.0/$3/2))/$5)}'`
      set n1 = `echo $n12 $n21 $ovl12 | awk '{printf("%d",($3-$1-$2)/2+$2)}'`
      set xm2 = `gmt grdinfo $pth2/real.grd -C | awk '{print $3}'`
      set xc2 = `gmt grdinfo tmp.grd -C | awk '{print $3}'`
      set n22 = `echo $xm2 $xc2 $incx | awk '{printf("%d",($1-$2)/$3)}'`

      set pth2 = `tail -1 $1 | awk -F: '{print $1}'`
      set near3 = `grep near $pth2"tmp.PRM" | awk '{print $3}'`
      gmt grdcut $pth2"real.grd" -Z+N -Gtmp.grd
      set x03 = `gmt grdinfo tmp.grd -C | awk '{print $2}'`
      set incx = `gmt grdinfo tmp.grd -C | awk '{print $8}'`
      set n31 = `echo $x03 $incx | awk '{printf("%d",$1/$2)}'`
      set ovl23 = `echo $near2 $near3 $fs $rng2 $incx | awk '{printf("%d",($4-($2-$1)/(299792458.0/$3/2))/$5)}'`
      set n2 = `echo $n22 $n31 $ovl23 | awk '{printf("%d",($3-$1-$2)/2+$2)}'`
      if ($n2 == 0) then
          echo "WARNING: Stitching positions estimated to be zero"
          echo "Check merged grids carefully"
          set n1 = ""
          set n2 = ""
      endif
      rm tmp.grd
    else
      echo "Incorrect number of records in input filelist .."
      exit 1
    endif
    echo "Stitching postitions set to $n1 $n2"
  endif
  echo $n1
  # for two subswath (n1 >5, n2 =0), for three subswath (n1>5, n2>5) subswath merge with pixel offset computed from det_stich flag
  if ($n1 > 5) then
    merge_swath tmp_realphaselist "real_"$2".grd" $stem $n1 $n2> merge_log
    merge_swath tmp_imagphaselist "imag_"$2".grd" $stem $n1 $n2>> merge_log
    if (! -f ../scatter_SM.grd) then
       echo "merge_swath ADIlist scatter_SM.grd $stem"
       merge_swath ../ADIlist ../scatter_SM.grd $stem $n1 $n2>> merge_log
       cp $stem".PRM" ../master.PRM
    endif
    
    mv "real_"$2".grd" ../
    mv "imag_"$2".grd" ../
 

  else
    merge_swath tmp_realphaselist "real_"$2".grd" $stem > merge_log
    merge_swath tmp_imagphaselist "imag_"$2".grd" $stem >> merge_log
    if (! -f ../scatter_SM.grd) then
       echo "merge_swath ADIlist scatter_SM.grd $stem"
       merge_swath ../ADIlist ../scatter_SM.grd $stem>> merge_log
       cp $stem".PRM" ../master.PRM
    endif
    mv "real_"$2".grd" ../
    mv "imag_"$2".grd" ../
  endif
    
  echo "Merging END"
  echo ""

 echo $pth$stem

 
  # This step is essential, cut the DEM so it can run faster.
  if (! -f trans.dat) then
    set led = `grep led_file $pth$stem".PRM" | awk '{print $3}'`
    echo $pth$led
    cp $pth$led .
    echo "Recomputing the projection LUT..."
  # Need to compute the geocoding matrix with supermaster.PRM with rshift set to 0
    set rshift = `grep rshift $stem".PRM" | tail -1 | awk '{print $3}'`
    update_PRM $stem".PRM" rshift 0
    update_PRM $stem".PRM" ashift 0
    gmt grd2xyz --FORMAT_FLOAT_OUT=%lf dem.grd -s | SAT_llt2rat $stem".PRM" 1 -bod > trans.dat
  # Set rshift back for other usage
    #update_PRM $stem".PRM" rshift $rshift
  endif
  exit 1

