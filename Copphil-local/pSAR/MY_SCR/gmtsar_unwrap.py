#!/usr/bin/env python 

###############################################################################
# Wrapped Phase Unwrapping Script (FLS/SNAPHU)
# Created by Wanpeng Feng (FWP) @ SYSU on February 9, 2021
# Updated and maintained by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose:
#   Perform 2D phase unwrapping for InSAR data using SNAPHU or FLS methods,
#   with automated configuration generation, correlation masking, and
#   patch-based processing to support large-scale interferograms.
###############################################################################

import os
import subprocess
import sys
import pGMT
import pSAR
import datetime
#
def create_conf_snaphu(outname,length,mode='DEFO',alg='MCF',row=8,col=8,ovr=128,nproc=8):
    #
    gmtsar_home = os.environ['GMTSAR_HOME']
    # default_conf = gmtsar_home+'/share/gmtsar/snaphu/config/snaphu.conf.brief'
    settings = \
    '''
# snaphu configuration file
#
# Lines with fewer than two fields and lines whose first non-whitespace
# characters are not alphnumeric are ignored.  For the remaining lines,
# anything after the first two fields (delimited by whitespace) is
# also ignored.  Inputs are converted in the order they appear in the file;
# if multiple assignments are made to the same parameter, the last one
# given is the one used.  Parameters in this file will be superseded by
# parameters given on the command line after the -f flag specifying this
# file.  Multiple configuration files may be given on the command line.



#############################################
# File input and output and runtime options #
#############################################

# See section below for file format configuration options.

# Input file name
# INFILE        snaphu.in

# Input file line length
LINELENGTH   %s 

# Output file name
# OUTFILE       snaphu.out

# Amplitude file name(s)
# AMPFILE       snaphu.amp.in   # Single file containing amplitude images

# Correlation file name
CORRFILE      corr.in

# Statistical-cost mode (TOPO, DEFO, SMOOTH, or NOSTATCOSTS)
STATCOSTMODE %s 

# Initialize-only mode (TRUE or FALSE)
# INITONLY      FALSE

# Algorithm used for initialization of wrapped phase values.  Possible
# values are MST and MCF.
INITMETHOD   %s

# Verbose-output mode (TRUE or FALSE)
# VERBOSE       FALSE


################
# File formats #
################
#
#INFILEFORMAT           COMPLEX_DATA
INFILEFORMAT            FLOAT_DATA

# Output file format
# Allowable formats:
#   ALT_LINE_DATA       (interferogram magnitude in channel 1,
#                        unwrapped phase in radians in channel 2; default)
#   ALT_SAMPLE_DATA     (interferogram magnitude in channel 1,
#                        unwrapped phase in radians in channel 2)
#   FLOAT_DATA          (unwrapped phase in radians)
#
#OUTFILEFORMAT          ALT_LINE_DATA
OUTFILEFORMAT           FLOAT_DATA

# Amplitude or power file format
# Units should be consistent with interferogram.  Allowable formats:
#   ALT_LINE_DATA       (first image amplitude in channel 1,
#                        second image amplitude in channel 2)
#   ALT_SAMPLE_DATA     (first image amplitude in channel 1,
#                        second image amplitude in channel 2; default)
#   FLOAT_DATA          (square root of average power of two images)
#
#AMPFILEFORMAT          ALT_SAMPLE_DATA
AMPFILEFORMAT           FLOAT_DATA

# Correlation file format
# Allowable formats:
#   ALT_LINE_DATA       (channel 1 ignored; correlation values
#                        between 0 and 1 in channel 2; default)
#   ALT_SAMPLE_DATA     (channel 1 ignored; correlation values
#                        between 0 and 1 in channel 2)
#   FLOAT_DATA          (correlation values between 0 and 1)
#
#CORRFILEFORMAT         ALT_LINE_DATA
CORRFILEFORMAT          FLOAT_DATA
#
######################################
# Input file of signed binary byte (signed char) values.  Values in
# the file should be either 0 or 1, with 0 denoting interferogram
# pixels that should be masked out and 1 denoting valid pixels.  The
# array should have the same dimensions as the input wrapped phase
# array.
# BYTEMASKFILE mask.in 

###############################
# SAR and geometry parameters #
###############################

# Orbital radius (double, meters) or altitude (double, meters).  The
# radius should be the local radius if the orbit is not circular.  The
# altitude is just defined as the orbit radius minus the earth radius.
# Only one of these two parameters should be given.
ORBITRADIUS             7153000.0
#ALTITUDE               775000.0

# Local earth radius (double, meters).  A spherical-earth model is
# used.
EARTHRADIUS             6378000.0

# The baseline parameters are not used in deformation mode, but they
# are very important in topography mode.  The parameter BASELINE
# (double, meters) is the physical distance (always positive) between
# the antenna phase centers.  The along-track componenet of the
# baseline is assumed to be zero.  The parameter BASELINEANGLE_DEG
# (double, degrees) is the angle between the antenna phase centers
# with respect to the local horizontal.  Suppose the interferogram is
# s1*conj(s2).  The baseline angle is defined as the angle of antenna2
# above the horizontal line extending from antenna1 towards the side
# of the SAR look direction.  Thus, if the baseline angle minus the
# look angle is less than -pi/2 or greater than pi/2, the topographic
# height increases with increasing elevation.  The units of
# BASELINEANGLE_RAD are radians.
# BASELINE                150.0
# BASELINEANGLE_DEG       225.0
# BASELINEANGLE_RAD      3.92699

# If the BPERP parameter is given, the baseline angle is taken to be
# equal to the look angle (mod pi) at midswath, and the length of the
# baseline is set accordingly.  Particular attention must be paid to
# the sign of this parameter--it should be negative if increasing
# phase implies increasing topographic height.
#BPERP          -150.0

# The transmit mode should be either REPEATPASS or PINGPONG if both
# antennas transmitted and both received (REPEATPASS and PINGPONG have
# the same effect); the transmit mode should be SINGLEANTENNATRANSMIT
# if only one antenna was used to transmit while both antennas
# received.  In single-antenna-transmit mode, the baseline is
# effectively halved.  This parameter is ignored for cost modes other
# than topography.
TRANSMITMODE    REPEATPASS

# Slant range from platform to first range bin in input data file
# (double, meters).  Be sure to modify this parameter if the input
# file is extracted from a larger scene.  The parameter does not need
# to be modified is snaphu is unwrapping only a subset of the input file.
NEARRANGE       831000.0

# Slant range and azimuth pixel spacings of input interferogram after
# any multilook averaging.  This is not the same as the resolution.
# (double, meters).
DR              8.0
DA              20.0

# Single-look slant range and azimuth resolutions.  This is not the
# same as the pixel spacing.  (double, meters).
RANGERES        10.0
AZRES           6.0

# Wavelength (double, meters).
LAMBDA          0.0565647

# Number of real (not necessarily independent) looks taken in range and
# azimuth to form the input interferogram (long).
NLOOKSRANGE     4 
NLOOKSAZ        1

# Number of looks (assumed independent) from nonspatial averaging (long).
NLOOKSOTHER     1

# Equivalent number of independent looks (double, dimensionless) that were
# used to generate correlation file if one is specified.  This parameter
# is ignored if the correlation data are generated by the interferogram
# and amplitude data.
#
# The equivalent number of independent looks is approximately equal to the
# real number of looks divided by the product of range and azimuth
# resolutions, and multiplied by the product of the single-look range and
# azimuth pixel spacings.  It is about 0.53 times the number of real looks
# for ERS data processed without windowing.
NCORRLOOKS      23.8

# Number of looks that should be taken in range and azimuth for estimating
# the correlation coefficient from the interferogram and the amplitude
# data.  These numbers must be larger than NLOOKSRANGE and NLOOKSAZ.
# The actual numbers used may be different since we prefer odd integer
# multiples of NLOOKSRANGE and NLOOKSAZ (long).  These numbers are ignored
# if a separate correlation file is given as input.
NCORRLOOKSRANGE 10
NCORRLOOKSAZ    2


###############################
# Scattering model parameters #
###############################

# Threshold brightness (normalized) for layover height integration
# (double, dimensionless)
LAYMINEI        1.25


##################################
# Decorrelation model parameters #
##################################

# Here, rho is the magnitude of the complex correlation coefficient
# between the two observations forming the interferogram (0<=rho<=1)
# See Zebker & Villasenor, 1992

# Default value to use uniformly for true, unbiased correlation if no
# correlation file is specified and correlation cannot be generated
# from the available data (double).
DEFAULTCORR     0.025

# Factor applied to expected minimum measured (biased) correlation.
# Values smaller than the threshold rhominfactor*rho0 are assumed to
# come from zero statistical correlation because of estimator bias (double).
# This is used only in topo mode; for defo mode, use DEFOTHRESHFACTOR.
RHOMINFACTOR    1.3


########################
# PDF model parameters #
########################

# Algorithm costs are based on the negative log pdf:
#
#   cost = -log(f(phi | EI, rho))

# Factor applied to range layover probability density to get azimuth
# layover probability density (double).
AZDZFACTOR      0.99

# Ratio of layover probability density to peak probability density
# for non-layover slopes expected (double).
LAYCONST        0.9


###############################
# Deformation mode parameters #
###############################

# Factor applied to range discontinuity probability density to get
# corresponding value for azimuth (double).
DEFOAZDZFACTOR  0.0

# Factor applied to rho0 to get threshold for whether or not phase
# discontinuity is possible (double).  rho0 is the expected, biased
# correlation measure if true correlation is 0.
DEFOTHRESHFACTOR 0.2

# Maximum phase discontinuity likely (double).  Units are radians or cycles.
# If abrupt phase discontinuities are not expected, this paramter can be
# set to zero.
DEFOMAX_CYCLE 0 
#DEFOMAX_RAD    7.5398

# Ratio of phase discontinuity probability density to peak probability
# density expected for discontinuity-possible pixel differences (double).
# Value of 1 means zero cost for discontinuity, 0 means infinite cost.
DEFOCONST      0.1 


########################
# Algorithm parameters #
########################

# Maximum flow increment (long) for solver.  Not the same as maximum
# flow possible.
MAXFLOW         4

# Scaling constant factor applied to double precision costs to get
# integer costs (double).
COSTSCALE       100.0

################
# Tile control #
################

#NTILEROW           %d 
#NTILECOL           %d

#ROWOVRLP           %d
#COLOVRLP           %d

#NPROC              %d
# End of snaphu configuration file
    '''
    with open(outname,'w') as fid:
        fid.write('%s\n' % (settings % (length,mode,alg,row,col,ovr,ovr,nproc)))
    if os.path.exists(outname):
        return True
    else:
        return False
    #share/gmtsar/snaphu/config/snaphu.conf.brief
def create_conf_fls(outname,length,delta=2,maxc=1000,unwrap='unwrap.bin'):
    #
    # wid = 17197
    with open(outname,'w') as fid:
        fid.write('PHASEFILE   phase.in\n')
        fid.write('QUALFILE    corr.in\n')
        fid.write('OUTFILE     %s\n' % unwrap)
        fid.write('XSIZE       %d \n' % length)
        fid.write('LOWDIS      1\n')
        fid.write('HIGHDIS     5\n')
        fid.write('DELTA       %d\n' % delta)
        fid.write('MAXCLUSTER  %d\n' % maxc)
    #
    if os.path.exists(outname):
        return True
    else:
        return False
#
if len(sys.argv)<2:
    helpstr = \
        '''
        %s <threshold_cor> -s [spatial_coverage] -o [unwrap.grd] -i 0
           -delta 2 -m [fls or snaphu,snaphu in default]
           -snaphu_mode [DEFO in default]
           -snaphu_alg [MCF in default]
           -in [phasefilt.grd in default]
           -update
           -phase [phase.grd]
           -cor   [corr.grd]
           -maxc [300 in default]
           -u [None in default]
           -row 4 in default
           -col 4 in default
           -ovr 128 in default
           -nproc 8 in default
        ++++++++++++++++++++++++++++++++++++++++++++++
        To unwrap a wrapped phase file in 2D using a FLS algorithm
        
        -s , <sub_range> None in default
        -o , output file name, unwrap.grd is in default
        -i , flag of interpolation before unwrapping, 0 in default
        -delta, 2 in default for use in the algorithm FLS
        -m , unwrapping method, fls in default.
        -snaphu_mode, modes applied in SNAPHU, e.g. TOPO, DEFO, SMOOTH, NOSTATCOSTS. DEFO in default
        -snaphu_alg, Algorithm used for initialization of wrapped phase values, MST(default) or MCF.
        -update, once given, phase.in, corr.in and [unwrap.grd] will be deleted if they exist.
        -u a reference unwrapped phase, none in default
        -in input filtered phase, phasefilt.grd in default
        #
        if -row is given 0 (zero), automatic patch number calculation will be triggered, and 1000*1000 will be suggested as individual size...

        Developed by FWP, @SYSU, Guangzhou, 2021/02/09

        '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
#
pSAR.util.log(sys.argv)
#
threshold_cor = float(sys.argv[1])
#
row = 4 
col = 4
nproc = 4
ovr = 256 
inphs = 'phasefilt.grd'
incor = 'corr.grd'
inmask = 'mask.grd'
#
update = False
sub_range  = None
unwrap_grd = 'unwrap.grd'
interp = 0
delta = 2
method = 'snaphu'
phase = 'phase'
maxc = 1000 
snaphu_mode = 'DEFO'
u=None
#
# change MCF to MST back by Wanpeng Feng, @2021/03/29
#
snaphu_alg  = 'MCF' # could be "MCF"
#
for i,key in enumerate(sys.argv):
    if key == '-phase':
        inphs = sys.argv[i+1]
    if key == '-cor':
        incor = sys.argv[i+1]
    if key == '-row':
        row = int(sys.argv[i+1])
    if key == '-col':
        col = int(sys.argv[i+1])
    if key == '-nproc':
        nproc = int(sys.argv[i+1])
    if key == '-ovr':
        ovr = int(sys.argv[i+1])
    if key == '-in':
       inphs = sys.argv[i+1]
    if key == '-u':
       u = sys.argv[i+1]
    if key == '-maxc':
       maxc = int(sys.argv[i+1])
    if key == '-update':
       update = True
    if key == '-snaphu_mode':
       snaphu_mode = sys.argv[i+1]
    if key == '-snaphu_alg':
       snaphu_alg = sys.argv[i+1]
    if key == '-m':
        method = sys.argv[i+1]
    if key == '-delta':
        delta = int(sys.argv[i+1])
    if key == '-i':
        interp = int(sys.argv[i+1])
    if key == '-o':
        unwrap_grd = sys.argv[i+1]
    if key == '-s':
        sub_range = sys.argv[i+1]
    #
#
if row == 0:
    #
    ginfo,gerror = pGMT.gmt_grdinfo(inphs)
    width = int(ginfo['WIDTH'])
    file_length = int(ginfo['FILE_LENGTH'])
    #
    row = int(file_length/1000)
    col = int(width/1000)
#
#
if update:
    #
    if os.path.exists('%s.in' % phase):
       os.system('rm %s.in -f' % phase)
    #
    if os.path.exists('corr.in'):
       os.system('rm corr.in -f')
    if os.path.exists('corr_patch.grd'):
       os.system('rm corr_patch.grd -f')
    if os.path.exists('phase_patch.grd'):
       os.system('rm phase_patch.grd -f')
    #
    if os.path.exists(unwrap_grd):
       os.system('rm %s -f' % unwrap_grd)
    #
if not os.path.exists(unwrap_grd):
  # prepare the files adding the correlation mask
  if True:
    #
    if incor != 'corr.grd':
        inmask = '%s.MSK.grd' % incor.split('.grd')[0]
        if not os.path.exists(inmask):
            #
            gostr = 'grdmath %s %f GE = %s' % (incor, threshold_cor,inmask)
            print(gostr)
            os.system(gostr)
            #
    if not os.path.exists('mask.grd'):
       goStr = 'gmt grdmath %s %f GE 0 NAN = mask.grd' % (incor, threshold_cor)
       print(goStr)
       os.system(goStr)
    #
    if sub_range is not None:
       GoStr = ['gmt grdcut %s -R%s -Gmask_patch.grd' % (inmask,sub_range),\
                'gmt grdcut %s -R%s -Gcorr_patch.grd' % (incor,sub_range),\
                'gmt grdcut %s -R%s -Gphase_patch.grd' % (inphs,sub_range)]
       if not os.path.exists('mask_patch.grd') or \
          not os.path.exists('corr_patch.grd') or \
          not os.path.exists('phase_patch.grd'):
          #
          for cstr in GoStr:
             print(cstr)
             os.system(cstr)
    else:
       GoStr = ['rm mask_patch.grd -f','rm corr_patch.grd -f','rm phase_patch.grd -f']
       for cstr in GoStr:
         print(cstr)
         os.system(cstr)
       #
       GoStr = ['ln -s %s  mask_patch.grd' % inmask,\
               'gmt grdmath %s 0 EQ 0 EQ %s MUL = corr_patch.grd' % (inphs,incor),
                'ln -s %s phase_patch.grd' % inphs]
       for cstr in GoStr:
         print(cstr)
         os.system(cstr)
  #
  #
  info,err = pGMT.gmt_grdinfo(inphs)
  # print(info)
  # create landmask
  #
  landmask_ra = 'landmask_ra.grd'
  if not os.path.exists(landmask_ra):
    result = subprocess.run(['gmt', 'grdinfo', 'phasefilt.grd', '-I-'], capture_output=True, text=True)
    output = result.stdout.strip()
    region_cut = output[2:20]
    os.system('ln -s ../topo/trans.dat .')
    subprocess.run(['landmask.csh', region_cut], check=True)

    if os.path.exists(landmask_ra):
        if sub_range is not None: 
          GoStr = 'gmt grdsample landmask_ra.grd -R%s `gmt grdinfo -I phase_patch.grd` -Glandmask_ra_patch.grd'
          print(GoStr % sub_range)
          os.system(GoStr % sub_range)
        else:
          GoStr = 'gmt grdsample landmask_ra.grd `gmt grdinfo -I phase_patch.grd` -Glandmask_ra_patch.grd'
          print(GoStr)
          os.system(GoStr)
    #
    GoStr = 'gmt grdmath phase_patch.grd landmask_ra_patch.grd MUL = phase_patch.grd -V'
    print(GoStr)
    os.system(GoStr)
  #
  if os.path.exists('mask.grd'):
     os.system('gmt grdmath %s %f GE 0 NAN = mask.grd' % (incor, threshold_cor))
  #
  if os.path.exists('%s.in' % phase):
      os.system('rm %s.in -f' % phase)
  if os.path.exists('corr.in'):
      os.system('rm corr.in -f')
  #
  if not os.path.exists('%s.in' % phase) or \
     not os.path.exists('corr.in'):
     GoStr = \
     '''
gmt grdmath corr_patch.grd %s GE 0 NAN mask_patch.grd MUL = mask2_patch.grd
gmt grdmath corr_patch.grd 0. XOR 1. MIN  = corr_patch.grd
gmt grdmath mask2_patch.grd corr_patch.grd MUL = corr_tmp.grd 
gmt grdmath phase_patch.grd mask2_patch.grd MUL = phase_tmp.grd
     '''
     print(GoStr % sys.argv[1])
     os.system(GoStr % sys.argv[1]) 
     #
     if interp != 0:
        #
        # nearest_grid phase_tmp.grd tmp.grd 300
        # GoStr = 'nearest_grid phase_tmp.grd tmp.grd 300'
        #
        # replace neareast_grid by using gdal_fillnodata.py, the later is 100 time faster than the former one.
        #
        # GoStr = 'pSAR_gmtsar_fillnondata.py phase_tmp.grd tmp.grd -md 150'
        # 
        # raterio seems working for filling nodata holes perfectly...
        #
        # updated by FWP, @SYSU, Guangzhou, 2021/10/14 
        # using rasterio
        GoStr = 'pSAR_rasterio_fillnodata.py phase_tmp.grd tmp.grd -mdist 150'
        #
        print(GoStr)
        os.system(GoStr)
        GoStr = 'mv tmp.grd phase_tmp.grd'
        print(GoStr)
        os.system(GoStr)
     #
     GoStr = \
     '''
gmt grd2xyz phase_tmp.grd -ZTLf -do0 > %s.in
gmt grd2xyz corr_tmp.grd -ZTLf  -do0 > corr.in
gmt grd2xyz mask2_patch.grd -ZTLc -do0 > mask.in
     '''
     print(GoStr % phase)
     os.system(GoStr % phase)
  #
  # flag, True for exists of FLS_config.cfg
  #       False for non-exists of FLS_config.cfg
  #
  unwrap_bin = '%s.bin' % unwrap_grd.split('.grd')[0]
  #
  ginfo,gerror = pGMT.gmt_grdinfo('phase_tmp.grd')
  width = int(ginfo['WIDTH'])
  file_length = int(ginfo['FILE_LENGTH'])
  #
  if 'fls' in method.lower():
     config = 'FLS_config.cfg'
     tmp_grd = 'fls_tmp.grd'
     flag = create_conf_fls(config,file_length,maxc=maxc,delta=delta,unwrap=unwrap_bin)
  else:
     config = 'SNAPHU_config.cfg'
     tmp_grd = 'snaphu_tmp.grd'
     GMTSAR_HOME = os.environ['GMTSAR_HOME']
     #
     #
     ginfo,gerror = pGMT.gmt_grdinfo('phase_tmp.grd')
     width = int(ginfo['WIDTH'])
     #
     flag = create_conf_snaphu(config,width,mode=snaphu_mode,alg=snaphu_alg,ovr=ovr,row=row,col=col,nproc=nproc)
     #
     if snaphu_mode.upper() == 'TOPO':
         mode_str = '-t'
     else:
         mode_str = '-d'
  #
  if flag:
      #
      if os.path.exists(unwrap_bin):
         os.system('rm %s -f' % unwrap_bin)
      #
      if u is not None:
          gostr = 'gmt grd2xyz %s -ZTLf -do0 > %s.in' % (u,u)
          os.system(gostr)
      #
      dt0 = datetime.datetime.now()
      if 'fls' in method.lower():
         os.system('unwrap_fls')
      else:
         if u is not None:
            snaphuStr = 'snaphu %s -f %s -c corr.in -o %s -v %s -u ' % (u+'.in',config,unwrap_bin,mode_str)
         else:
            snaphuStr = 'snaphu phase.in -f %s -c corr.in -o %s -v %s ' % (config,unwrap_bin,mode_str)
         print(snaphuStr)
         os.system(snaphuStr) 
      #
      dt1 = datetime.datetime.now()
      lasting_T = dt1 - dt0
      print(" +++++++++++++++++++++++++++++++++++++++++++++++++")
      print(" Info: %s using %f seconds to get this done!!!" % (method,lasting_T.total_seconds()))
      print(" +++++++++++++++++++++++++++++++++++++++++++++++++")
  #
  if os.path.exists(unwrap_bin) and not os.path.exists(unwrap_grd):
      #
      GoStr = 'gmt xyz2grd %s -ZTLf -r `gmt grdinfo -I- phase_patch.grd` `gmt grdinfo -I phase_patch.grd` -G%s' % \
              (unwrap_bin,tmp_grd)
      os.system(GoStr)
      # masking unwrappfile..
      if os.path.exists(tmp_grd):
         GoStr = 'gmt grdmath %s mask2_patch.grd MUL = %s' % (tmp_grd,unwrap_grd)
         os.system(GoStr)
         if os.path.exists('landmask_ra.grd'):
            GoStr = 'gmt grdmath %s landmask_ra_patch.grd MUL = %s -V' % (unwrap_grd,unwrap_grd)
            os.system(GoStr)
  # clean up the folder
  #
  if os.path.exists(tmp_grd):
      os.system('rm %s -f' % tmp_grd)
  #
  if os.path.exists('phase_tmp.grd'):
      os.system('rm phase_tmp.grd -f')
  #
  if os.path.exists('corr_tmp.grd'):
      os.system('rm corr_tmp.grd -f')
  #
  sys.exit(-1)
  #
