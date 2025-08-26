#!/bin/csh -f
#       $Id$
#
# Xiaohua(Eric) Xu, Feb 26 2016
# Take previous code, make it work with multiple frames
# Take previous code, make it work with bursts mismatch

# Preprocess and align tops image stacks
# used for time series analysis

# Xiaohua(Eric) Xu, Jan 19 2016
#

  if ($#argv != 3) then
    echo ""
    echo "Usage: preproc_tops_batch.csh data.in dem.grd mode"
    echo "  preprocess and align a set of tops images in data.in, precise orbits required"
    echo ""
    echo "  format of data.in:"
    echo "    image_name:orbit_name"
    echo ""
    echo "  example of data.in"
    echo "    s1a-iw1-slc-vv-20150626...001:s1a-iw1-slc-vv-20150626...001:s1a-iw1-slc-vv-20150626...001:S1A_OPER_AUX_POEORB_V20150601_20150603.EOF"
    echo "    s1a-iw1-slc-vv-20150715...001:s1a-iw1-slc-vv-20150715...001:s1a-iw1-slc-vv-20150715...001:S1A_OPER_AUX_POEORB_V20150625_20150627.EOF"
    echo ""
    echo "  outputs:"
    echo "    baseline.ps align_table.ra (contains info for precise geomatric alignment)"
    echo "    *.PRM *.LED *.SLC(mode 2)"
    echo ""
    echo "  Note:"
    echo "    The names must be in time order in each line to be stitched together"
    echo ""
    exit 1
  endif

  # set up some parameters
  set mode = $3
  set sl = `echo "1"`
  
  # sample the dem
  # Modified, there is no need to re-do dem filtering if topo.llt exists.
  # by FWP, @SYSU, 2020/04/13
  # 
  if ($mode == 2 && -e ../topo.llt) then
     if (! -e topo.llt) then
         ln -s $PWD/../topo.llt .
     endif 
  endif
  #
  if ($mode == 2 && ! -e topo.llt) then
    echo " now filtering dem data... using grdfilter and grd2xyz"
    gmt grdfilter $2 -D2 -Fg2 -I12s -Gflt.grd -x20
    gmt grd2xyz --FORMAT_FLOAT_OUT=%lf flt.grd -s > topo.llt
    mv topo.llt ../.
    ln -s $PWD/../topo.llt .
  endif

  # first line is the super-master, all images aligned to it
  set master = `awk -F: 'NR==1 {print $1}' $1 | awk '{ print "S1_"substr($1,16,8)"_"substr($1,25,6)"_F"substr($1,7,1)}'` 
  set mmaster = `awk -F: 'NR==1 {print $1}' $1 | awk '{ print "S1_"substr($1,16,8)"_ALL_F"substr($1,7,1)}'`
  #
  set ALL_SLC_n = `ls S1_*_ALL*.SLC |wc -l`
  set data_n = `cat $1|wc -l`
  if ( "$data_n" > "$ALL_SLC_n" ) then
     echo "  Redo: master of $mmaster"
     rm $mmaster*.SLC -f
  endif 
  # clean up a little bit
  # a sequential insar processing chain need to update processing for new data only...
  # rm  *.PRM* *.SLC *.LED *tmp*
  # 
  if (-f baseline_table.dat) rm baseline_table.dat
  if (-f masterlist) rm masterlist
  set sharedir = `gmtsar_sharedir.csh`

  # loop over all the acquisitions
  # 
  foreach line (`awk '{print $0}' $1`)
    # record the first one as the stem_master
    set stem_master = `echo $line | awk -F: '{print $1}' | awk '{ print "S1_"substr($1,16,8)"_"substr($1,25,6)"_F"substr($1,7,1)}'`
    set m_stem_master = `echo $line | awk -F: '{print $1}' | awk '{ print "S1_"substr($1,16,8)"_ALL_F"substr($1,7,1)}'`
    #
    if (-e $m_stem_master.SLC) then
       set sl = `echo $sl | awk '{print $1+1}'`
       # set earth_radius = `grep earth_radius $m_stem_master.PRM | awk '{print $3}'`
       continue
    endif
    #
    if($mode == 1) then

      # for mode 1, generate baseline_plots
      set image = `echo $line | awk -F: '{print $1}'`
      set orbit = `echo $line | awk -F: '{print $NF}'`
     
      # generate prms and leds
      make_s1a_tops $image.xml $image.tiff $m_stem_master 0
      ext_orb_s1a $m_stem_master.PRM $orbit $m_stem_master
      
      # get the height and baseline info
      cp $m_stem_master.PRM junk1
      calc_dop_orb junk1 junk2 0 0
      cat junk1 junk2 > $m_stem_master.PRM

      baseline_table.csh $mmaster.PRM $m_stem_master.PRM >> baseline_table.dat
      baseline_table.csh $mmaster.PRM $m_stem_master.PRM GMT >> table.gmt

      # clean up the mess
      rm junk1 junk2
    else if($mode == 2) then
      # for mode 2, stitch and align all the images

      # find the files to be stitched
      echo $line | awk -F: '{for (i=1;i<NF;i++) print $i}' > tmp.filelist
      set orbit = `echo $line | awk -F: '{print $NF}'`

      if (-f tmp.stitchlist) then 
        rm tmp.stitchlist
      endif
      set tmp_da = 0

      # loop over all the files in this line
      rm *par*
      set count = 0
      #
      #
      foreach file (`awk '{print $0}' tmp.filelist`)
        # generate prms and leds
        set count = `echo $count | awk '{print $1+1}'`
        set stem = `echo $file | awk '{ print "S1_"substr($1,16,8)"_"substr($1,25,6)"_F"substr($1,7,1)}'`
        #
        # add lines below by FWP, @SYSU, Guangzhou, 2020/04/20
        set stemALL = `echo $line | awk -F: '{print $1}' | awk '{ print "S1_"substr($1,16,8)"_ALL_F"substr($1,7,1)}'`
        #
        if (-f $stemALL.PRM && -f $stemALL.SLC) then
           echo " $stem.SLC is ready..."
           continue
        endif
        #
        # get images aligned
        # set sl = 2
        if($sl == 1) then
          # sl=1 means processing the super_master image, simpley generate images and stitch them together
          echo " make_s1a_tops: using $sl mode to generate SLCs"
          make_s1a_tops $file.xml $file.tiff $stem 1
          # make_s1a_tops $file.xml $file.tiff $stem 2
          ext_orb_s1a $stem.PRM $orbit $stem
          echo $stem >> masterlist
          echo $stem >> tmp.stitchlist
          #
        else
          #  
          # sl>1 measn processing slave images, point-by-point alignment and corregistration is required 
          echo " make_s1a_tops: using $sl mode to coregistration"
          make_s1a_tops $file.xml $file.tiff $stem 0
          ext_orb_s1a $stem.PRM $orbit $stem

          # compute the time difference between first frame and the rest frames
          set tmp_master = `awk 'NR == '$count' {print $0}' < masterlist`
          echo " make_s1a_tops: $tmp_master is selected ..."
          #
          if ($tmp_master == "") set tmp_master = `awk 'NR == '$count'-1 {print $0}' < masterlist`          
          if ($tmp_master == "") set tmp_master = `awk 'NR == '$count'-2 {print $0}' < masterlist`
           
          cp $tmp_master.PRM tmp.PRM
          set t1 = `grep clock_start $master.PRM | grep -v SC_clock_start | awk '{printf("%.13f", $3)}'`
          set t2 = `grep clock_start $tmp_master.PRM | grep -v SC_clock_start | awk '{printf("%.13f", $3)}'`
          set prf = `grep PRF $master.PRM | awk '{printf("%.6f",$3)}'`
          set nl = `echo $t1 $t2 $prf | awk '{printf("%d",($2 - $1)*$3*86400.0+0.2)}'`

          # compute whether there are any image offset
          if ($tmp_da == 0) then
            cp tmp.PRM junk1.PRM
            cp $stem.PRM junk2.PRM
            calc_dop_orb junk1.PRM junk $earth_radius 0
            cat junk >> junk1.PRM
            calc_dop_orb junk2.PRM junk $earth_radius 0
            cat junk >> junk2.PRM
            set lontie = `SAT_baseline junk1.PRM junk2.PRM | grep lon_tie_point | awk '{print $3}'`
            set lattie = `SAT_baseline junk1.PRM junk2.PRM | grep lat_tie_point | awk '{print $3}'`
            set tmp_am = `echo $lontie $lattie 0 | SAT_llt2rat tmp.PRM 1 | awk '{print $2}'`
            set tmp_as = `echo $lontie $lattie 0 | SAT_llt2rat $stem.PRM 1 | awk '{print $2}'`
            set tmp_da = `echo $tmp_am $tmp_as | awk '{printf("%d",$2 - $1)}'`
            rm junk1.PRM junk2.PRM junk
          endif

          # in case the images are offset by more than a burst, shift the super-master's PRM again so SAT_llt2rat gives precise estimate
          if ($tmp_da > -1000 && $tmp_da < 1000) then
            cp tmp.PRM junk1
            calc_dop_orb junk1 junk2 $earth_radius 0
            cat junk1 junk2 > tmp.PRM
            cp $stem.PRM junk1
            calc_dop_orb junk1 junk2 $earth_radius 0
            cat junk1 junk2 > $stem.PRM
            rm junk1 junk2

            SAT_llt2rat tmp.PRM 1 < topo.llt > tmpm.dat &
            SAT_llt2rat $stem.PRM 1 < topo.llt > tmp1.dat &
	    wait
          else
            echo "Modifying master PRM by $tmp_da lines..."
            set prf = `grep PRF tmp.PRM | awk '{print $3}'`
            set ttmp = `grep clock_start tmp.PRM | grep -v SC_clock_start | awk '{print $3}' | awk '{printf ("%.12f",$1 - '$tmp_da'/'$prf'/86400.0)}'`
            update_PRM tmp.PRM clock_start $ttmp
            set ttmp = `grep clock_stop tmp.PRM | grep -v SC_clock_stop | awk '{print $3}' | awk '{printf ("%.12f",$1 - '$tmp_da'/'$prf'/86400.0)}'`
            update_PRM tmp.PRM clock_stop $ttmp
            set ttmp = `grep SC_clock_start tmp.PRM | awk '{print $3}' | awk '{printf ("%.12f",$1 - '$tmp_da'/'$prf'/86400.0)}'`
            update_PRM tmp.PRM SC_clock_start $ttmp
            set ttmp = `grep SC_clock_stop tmp.PRM | awk '{print $3}' | awk '{printf ("%.12f",$1 - '$tmp_da'/'$prf'/86400.0)}'`
            update_PRM tmp.PRM SC_clock_stop $ttmp

            cp tmp.PRM junk1
            calc_dop_orb junk1 junk2 $earth_radius 0
            cat junk1 junk2 > tmp.PRM
            cp $stem.PRM junk1
            calc_dop_orb junk1 junk2 $earth_radius 0
            cat junk1 junk2 > $stem.PRM
            rm junk1 junk2
            
            #SAT_llt2rat tmp.PRM 1 < topo.llt > tmp_tmp.dat &
            SAT_llt2rat tmp.PRM 1 < topo.llt > tmpm.dat &
            SAT_llt2rat $stem.PRM 1 < topo.llt > tmp1.dat &
            wait
          endif

          # get r, dr, a, da, SNR table to be used by fitoffset.csh
          paste tmpm.dat tmp1.dat | awk '{printf("%.6f %.6f %.6f %.6f %d\n", $1, $6 - $1, $2, $7 - $2, "100")}' > tmp.dat
          set rmax = `grep num_rng_bins $stem.PRM | awk '{print $3}'`
          set amax = `grep num_lines $stem.PRM | awk '{print $3}'`
          awk '{if($1 > 0 && $1 < '$rmax' && $3 > 0 && $3 < '$amax') print $0 }' < tmp.dat > offset.dat
         
          # prepare the offset parameters for the stitched image 
          if ($tmp_da > -1000 && $tmp_da < 1000) then
            awk '{printf("%.6f %.6f %.6f %.6f %d\n", $1, $2, $3 + '$nl', $4, $5)}' < offset.dat >> par_tmp.dat
          else
            awk '{printf("%.6f %.6f %.6f %.6f %d\n", $1, $2, $3 + '$nl' - '$tmp_da', $4 + '$tmp_da', $5)}' < offset.dat >> par_tmp.dat
          endif

          # prepare the rshift and ashift look up table to be used by make_s1a_tops
          awk '{ printf("%.6f %.6f %.6f \n",$1,$3,$2) }' < offset.dat > r.xyz
          awk '{ printf("%.6f %.6f %.6f \n",$1,$3,$4) }' < offset.dat > a.xyz
          #
          #
          gmt blockmedian r.xyz -R0/$rmax/0/$amax -I8/4 -r -bo3d > rtmp.xyz
          gmt blockmedian a.xyz -R0/$rmax/0/$amax -I8/4 -r -bo3d > atmp.xyz
          gmt surface rtmp.xyz -bi3d -R0/$rmax/0/$amax -I8/4 -Grtmp.grd -T0.1 -N1000  -r &
          gmt surface atmp.xyz -bi3d -R0/$rmax/0/$amax -I8/4 -Gatmp.grd -T0.1 -N1000  -r &
          #
          wait
          gmt grdmath rtmp.grd FLIPUD = r.grd
          gmt grdmath atmp.grd FLIPUD = a.grd          
          #
          #
          cp atmp.xyz $stem.a.xyz 
          cp offset.dat $stem.offset.dat
          cp r.grd $stem.r_withoutESD.grd
          cp a.grd $stem.a_withoutESD.grd
          # generate the image with point-by-point shifts
          make_s1a_tops $file.xml $file.tiff $stem 1 r.grd a.grd
          ext_orb_s1a $stem.PRM $orbit $stem
          # 
          # fitoffset.csh 1 1 offset.dat >> $stem.PRM
          fitoffset.csh 3 3 offset.dat >> $stem.PRM
          echo $stem >> tmp.stitchlist
          rm r.grd a.grd -f
        endif
      end
      # 
      set nf = `wc -l tmp.stitchlist | awk '{print $1}'`
      # get the name for stitched file
      set stem = `echo $line | awk -F: '{print $1}' | awk '{ print "S1_"substr($1,16,8)"_ALL_F"substr($1,7,1)}'`
      #
      # stitch images together and get the precise orbit
      if ($nf > 1) then
        stitch_tops tmp.stitchlist $stem
      else
        set tmp_stem = `cat tmp.stitchlist`
        if (-e $stem.SLC) then
           continue
        endif
        cp $tmp_stem.PRM $stem.PRM
        cp $tmp_stem.LED $stem.LED
        mv $tmp_stem.SLC $stem.SLC

        update_PRM $stem.PRM input_file $stem.raw
        update_PRM $stem.PRM SLC_file $stem.SLC
        update_PRM $stem.PRM led_file $stem.LED
      endif 
      ext_orb_s1a $stem.PRM $orbit $stem

      # for images except the super-master
      if ($sl != 1) then    
        cp $stem.PRM $stem.PRM0
        #if ($bshift != 0) echo "Updated shift caused by burst offset is $bshift"
        if ($tmp_da > -1000 && $tmp_da < 1000) then
          update_PRM $stem.PRM ashift 0
        else
          update_PRM $stem.PRM ashift $tmp_da
          echo "Restoring $tmp_da lines shift to the image..."
        endif
        update_PRM $stem.PRM rshift 0
        
        resamp $mmaster.PRM $stem.PRM $stem.PRMresamp $stem.SLCresamp 1
        mv $stem.PRMresamp $stem.PRM
        mv $stem.SLCresamp $stem.SLC 

        fitoffset.csh 3 3 par_tmp.dat >> $stem.PRM
      endif
       
       cp $stem.PRM junk1
       if ($sl == 1) then
         calc_dop_orb junk1 junk2 0 0
         set earth_radius = `grep earth_radius junk2 | awk '{print $3}'`
       else
         calc_dop_orb junk1 junk2 $earth_radius 0
       endif
       cat junk1 junk2 > $stem.PRM
       rm junk1 junk2
       set sl = `echo $sl | awk '{print $1+1}'`
    endif
  end

  # for mode 1, plot the time-baseline figure
  if($mode == 1) then
    awk '{print 2014+$1/365.25,$2,$7}' < table.gmt > text
    set region = `gmt gmtinfo text -C | awk '{print $1-0.5, $2+0.5, $3-50, $4+50}'`
    gmt pstext text -JX8.8i/6.8i -R$region[1]/$region[2]/$region[3]/$region[4] -D0.2/0.2 -X1.5i -Y1i -K -N -F+f8,Helvetica+j5 > baseline.ps
    awk '{print $1,$2}' < text > text2
    gmt psxy text2 -Sp0.2c -G0 -R -JX -Ba0.5:"year":/a50g00f25:"baseline (m)":WSen -O >> baseline.ps
    rm text text2 table.gmt
  endif

  # clean up a little bit
  # topo.llt and flt.grd should be kept...
  # #
  if($mode == 2) rm atmp* rtmp* *SLCL *SLCH *BB

