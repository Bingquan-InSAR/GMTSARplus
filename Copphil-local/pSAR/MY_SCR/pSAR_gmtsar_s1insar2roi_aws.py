#!/usr/bin/env python
#
#
import pSAR
import os
import sys
import multiprocessing as mp
import numpy as np
import glob
import shutil
#
def log2roi(inlog):
    #
    with open(inlog,'r') as fid:
        #
        for cline in fid:
            cline = cline
        #
    #
    roi = ''
    tmp = cline.split()
    for i,key in enumerate(tmp):
        if key == '-roi':
            roi = tmp[i+1]
        #
    #
    return roi
def run_conversion(in_subdir):
    #
    os.chdir(in_subdir)
    if gowrap:
        gowrapSTR = '-gowrap'
    else:
        gowrapSTR = ''
    print(" Progress: now working in %s " % in_subdir)
    #
    gmtsar_pair = in_subdir.split('/')[-2]
    # print(gmtsar_pair)
    gmtsar_d1 = gmtsar_pair.split('_')[0]
    gmtsar_d2 = gmtsar_pair.split('_')[1]
    roi_d1 = pSAR.ts.dayofyear2yyyymmdd(gmtsar_d1,gmtsar=True)
    roi_d2 = pSAR.ts.dayofyear2yyyymmdd(gmtsar_d2,gmtsar=True)
    #
    roi_pair = 'geo_%s_%s' % (roi_d1,roi_d2)
    targetphs = glob.glob('%s/%s*.phs' % (outdir,roi_pair))
    #
    if amp:
        amp_str = '-amp'
    else:
        amp_str = ''
    #
    if prmFolder is None:
      goStr = 'pSAR_gmtsar_dir2roi_aws.py %s -zipdir %s %s %s' % \
              (outdir,zipdir,gowrapSTR,amp_str)
    else:
      goStr = 'pSAR_gmtsar_dir2roi_aws.py %s -zipdir %s -prmFolder %s %s %s' % \
              (outdir,zipdir,prmFolder,gowrapSTR,amp_str)
    #
    print(" Progress: %s in %s" % (goStr,in_subdir))

    if len(targetphs)>0:
        # print(roi_pair,outdir,len(targetphs))
        os.chdir(topdir)
        return True
    os.system(goStr)
    os.chdir(topdir)
    #
    return True
#
##################################################################
if len(sys.argv)<5:
    helpstr = \
        '''
        %s <in_dir> <out_dir> <zip_dir> <n_njob> -prmFolder [None default] -gowrap
                                                 -amp [False in default]
        ++++++++++++++++++++++++++++++++++++++++++++++
        To prepare ROI_PAC results from GMTSAR with explicit metadata information...
        in parallel...
        
        -amp, if given, amp will be set as "True"
        
        Written by Wanpeng Feng, @SYSU, Guangzhou, 2020/04/20
        
        Updated by Wanpeng Feng, @SYSU, 2021/12/24
        -amp   is added since this version.

        '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
#
#################################################################
#
pSAR.util.log(sys.argv)
#
#
global zipdir, outdir, amp, topdir, prmFolder,gowrap
indir  = sys.argv[1]
outdir = sys.argv[2]
prmFolder = None
zipdir    = os.path.abspath(sys.argv[3])
#
amp       = False
gowrap    = False
njob      = int(sys.argv[4])
#
#
for i,key in enumerate(sys.argv):
    #
    if key == '-amp':
        amp = True
    if key == '-gowrap':
        gowrap = True
    if key == '-prmFolder':
        prmFolder = os.path.abspath(sys.argv[i+1])
    #
#
outdir = os.path.abspath(outdir)
if not os.path.exists(outdir):
    os.makedirs(outdir)
#
#
if True:
    topdir = os.getcwd()
    dirs = glob.glob(indir+'/2*_2*/')
    #
    cpool   = mp.Pool(processes=njob)
    results = cpool.map(run_conversion, dirs)
    #
    cpool.close()
    cpool.join()
    #
    os.chdir(topdir)
    #
    # figures for spatial coverage
    figures = glob.glob('Fig_spatial_coverage_withROI.*')
    for cfigure in figures:
        bname = os.path.basename(cfigure)
        shutil.copyfile(cfigure, outdir+'/%s' % bname)
    #
    # pSAR_gmtsar_s1.log
    if os.path.exists('pSAR_gmtsar_s1_aws.log'):
        roi = log2roi('pSAR_gmtsar_s1_aws.log')
        os.system('echo %s > %s/roi.info' % (roi,outdir))

    # 
    # super master applied during the procesing
    #
    master = glob.glob('master.in')
    if len(master)>0:
        shutil.copyfile(master[0],outdir+'/master.in')
    #
    iws = glob.glob('iws.in')
    if len(iws)>0:
        shutil.copyfile(iws[0],outdir+'/iws.in')
    #
    #
    baseline_pdf = glob.glob('F*/baseline_table.dat.pdf')
    if len(baseline_pdf)>=1:
        #
        shutil.copyfile(baseline_pdf[0],outdir+'/baseline_table.dat.pdf')
    #
    baseline_dat = glob.glob('F*/baseline_table.dat')
    #
    if len(baseline_dat) >= 1:
        shutil.copyfile(baseline_dat[0], outdir+'/baseline_table.dat')
    #
    # updating perpendicular baseline and azimuth angle
    #
    geoinc = glob.glob('%s/geo_*.inc' % outdir)
    geoazi = glob.glob('%s/geo_*.azi' % outdir)
    if len(geoinc) > 0 and len(geoazi)>0:
       inc = pSAR.roipac.roi_read(geoinc[0])
       azi = pSAR.roipac.roi_read(geoazi[0])
       inc[np.isnan(inc)] = 0
       azi[np.isnan(azi)] = 0
       inc = inc[inc!=0]
       azi = azi[azi!=0]
       meaninc = inc.mean()
       meanazi = azi.mean()
       print(" Mean inc and azi: %f,%f\n" %  (meaninc,meanazi));
       #
       rscs = glob.glob('%s/geo*.rsc' % outdir)
       for crsc in rscs:
           info,ext = pSAR.roipac.rsc_read(crsc)
           print(" Updating %s from %s,%s to %f,%f\n" % \
                   (crsc,info['HEADING_DEG'],info['INCIDENCE'],meanazi,meaninc))
           info['HEADING_DEG'] = meanazi
           info['INCIDENCE'] = meaninc
           pSAR.roipac.info_to_rsc(info,crsc)

