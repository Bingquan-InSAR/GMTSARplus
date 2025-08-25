#!/bin/csh -f
#       $Id$
#
#  Xiaopeng Tong and David Sandwell 
#  FEB 4 2010
#  Matt Wei May 4 2010, ENVISAT
#  DTS - May 26, 2010, added phase gadient
#  EF, DTS, XT - Jan 10 2014, TSX
#
# Convolve the real.grd and imag.grd with gaussian filters. 
# Form amplitude, phase, phase gradient, and correlation images. 
#
#
  alias rm 'rm -f'
  gmt set IO_NC4_CHUNK_SIZE classic
#
#
# set grdimage options
#
  set scale = "-JX6.5i"
  set thresh = "5.e-21"
  gmt set COLOR_MODEL = hsv
  gmt set PROJ_LENGTH_UNIT = inch

  if ($#argv != 4 && $#argv != 6) then
errormessage:
    echo ""
    echo "Usage: slc2amp_MUL.csh master.PRM <outamp.grd> filter decimation [rng_dec azi_dec]"
    echo ""
    echo " Apply gaussian filter to amplitude and phase images."
    echo " "
    echo " filter -  wavelength of the filter in meters (0.5 gain)"
    echo " decimation - (1) better resolution, (2) smaller files"
    echo " "
    echo "Example: slcamp_MUL.csh IMG-HH-ALPSRP055750660-H1.0__A.PRM amp-ALPSRP055750660_MUL.grd 200  2"
    echo ""
    exit 1
  endif
  echo " slc2amp_MUL.csh"
#
# define filter and decimation variables
#
  set amp_grd = $2
  set sharedir = `gmtsar_sharedir.csh`
  set filter3 = $sharedir/filters/fill.3x3
  set filter4 = $sharedir/filters/xdir
  set filter5 = $sharedir/filters/ydir
  set dec  = $4
  # set rng_lks = $5
  # set az_lks = $6 
  set PRF = `grep PRF *.PRM | awk 'NR == 1 {printf("%d", $3)}'`
  if( $PRF < 1000 && $#argv < 6 ) then
     set az_lks = 1
  else
     set rng_lks = $5
     set az_lks = $6
  endif
  
#
# look for range sampling rate
#
  set rng_samp_rate = `grep rng_samp_rate $1 | awk 'NR == 1 {printf("%d", $3)}'`
#
# set the range spacing in units of image range pixel size
#
  if ($?rng_samp_rate) then
    if ($rng_samp_rate > 110000000) then 
      set dec_rng = 4
      set filter1 = $sharedir/filters/gauss15x5
    else if ($rng_samp_rate < 110000000 && $rng_samp_rate > 20000000) then
      set dec_rng = 2
      set filter1 = $sharedir/filters/gauss15x5
#
# special for TOPS mode
#
      if($az_lks == 1) then
        set filter1 = $sharedir/filters/gauss5x5
      endif
    else  
      set dec_rng = 1
      set filter1 = $sharedir/filters/gauss15x3
    endif
  else
    echo "Undefined rng_samp_rate in the master PRM file"
    exit 1
  endif
#
# set az_lks and dec_rng to 1 for odd decimation
#
  if($#argv == 6) then
    set jud = `echo $6 | awk '{if($1%2 == 0) print 1;else print 0}'`
    if ($jud == 0) then 
      set az_lks = 1
    endif
    set jud = `echo $5 | awk '{if($1%2 == 0) print 1;else print 0}'`
    if ($jud == 0) then 
      set dec_rng = 1 
    endif
  endif

#
#  make the custom filter2 and set the decimation
#
  make_gaussian_filter $1 $dec_rng $az_lks $3 > ijdec
  set filter2 = gauss_$3
  set idec = `cat ijdec | awk -v dc="$dec" '{ print dc*$1 }'`
  set jdec = `cat ijdec | awk -v dc="$dec" '{ print dc*$2 }'`
  if($#argv == 6) then
    set idec = `echo $6 $az_lks | awk '{printf("%d",$1/$2)}'`
    set jdec = `echo $5 $dec_rng | awk '{printf("%d",$1/$2)}'`
    echo "setting range_dec = $5, azimuth_dec = $6"
  endif
  echo "$filter2 $idec $jdec ($az_lks $dec_rng)" 
#
# filter the two amplitude images
#
  echo "making amplitudes..."
  conv $az_lks $dec_rng $filter1 $1 amp1_tmp.grd=bf
  conv $idec $jdec $filter2 amp1_tmp.grd=bf $amp_grd 
  #
  # mv amp1.grd $1.grd
  rm amp1_tmp.grd
