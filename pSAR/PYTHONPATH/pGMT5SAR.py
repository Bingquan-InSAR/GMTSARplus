#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import glob
import os
import pSAR
import numpy as np
import pGMT
import random
import pDATA
from scipy.constants import speed_of_light
"""
fucntions for use in GMT5SAR
Created on Mon May 14 15:08:30 2018

@author: wafeng
"""
def gmtsar_prm2res(prm):
    #
    info = prm2info(prm)
    #
    earth_radius = float(info['earth_radius'])
    SC_vel = float(info['SC_vel'])
    SC_height = float(info['SC_height'])
    prf = float(info['PRF'])
    rng_samp_rate = float(info['rng_samp_rate'])
    near_range = float(info['near_range'])
    num_rng_bins = float(info['num_rng_bins'])
    #
    azi_px_size = SC_vel / np.sqrt(1 + SC_height / earth_radius) / prf
    rng_px_size = speed_of_light / rng_samp_rate / 2.0
    #
    # compute the cosine of the looking angle and the surface deviate angle
    #
    a = SC_height + earth_radius
    far_range = near_range + rng_px_size * num_rng_bins
    rng = (near_range + far_range) / 2.0
    cost = (np.power(a, 2.0) + np.power(rng, 2.0) - np.power(earth_radius, 2.0)) / 2.0 / a / rng
    cosa = (np.power(a, 2.0) + np.power(earth_radius, 2.0) - np.power(rng, 2.0)) / 2.0 / a / earth_radius
    #
    # compute the ground range pixel size
    #
    rng_px_size_gnd = rng_px_size / np.sin(np.arccos(cost) + np.arccos(cosa))
    #
    return [rng_px_size,azi_px_size,rng_px_size_gnd]
#
def gmtsar_prm2corners(PRM,dem,unwrap):
    # dem in grd format
    #
    info,ext,_ = pDATA.grd_read(dem)
    lons = np.linspace(ext[0],ext[1],num=20000)
    lats = np.linspace(ext[2],ext[3],num=20000)
    #
    ll = np.vstack([lons,lats]).T
    np.savetxt('_llroi.xy',ll,fmt='%f %f')
    flag,data,err = pGMT.gmt_grdtrack(dem,'_llroi.xy')
    #
    ratdata = None
    if flag == 0 or flag:
       tmp_out2 = 'topo.llt'
       np.savetxt(tmp_out2,data,fmt='%f %f %f')
       ij_out2 = 'topo.ratll'
       goStr = 'SAT_llt2rat %s 1 < %s > %s' % (PRM,tmp_out2,ij_out2)
       print(" GMTSAR: %s" % goStr)
       os.system(goStr)
       ratdata = np.loadtxt(ij_out2)
    #
    if ratdata is not None:
        #
        rngs = ratdata[:,0]
        azis = ratdata[:,1]
        #
        _, grdext,_ = pDATA.grd_read(unwrap)
        #
        polys = pSAR.roipac.ext2polygon(grdext)
        for i in range(polys.shape[0]):
            #
            ind1 = rngs>polys[i,0]
            ind2 = rngs<=polys[i,0]
            rflag = ind1 * ind2
            #
            a1 = azis >  polys[i,1]
            a2 = azis <= polys[i,1]
            aflag = a1 * a2
            flag = rflag * aflag
            #
            print(ratdata[flag,:])
def gmtsar_lls2ij(PRM,llroi,dem,rmax=True):
    #
    # dem is in gmt format
    #
    info = prm2info(PRM)
    maxrng = int(info['num_rng_bins'])
    maxrow = int(info['nrows'])
    #
    #
    polys = pSAR.roipac.ext2polygon(llroi)
    # dems = pSAR.br.brlllist(dem, polys)
    np.savetxt('_llroi.xy',polys,fmt='%f %f')
    flag,data,err = pGMT.gmt_grdtrack(dem,'_llroi.xy')
    ratdata = None
    #
    if flag == 0 or flag:
       tmp_out2 = 'topo.llt'
       np.savetxt(tmp_out2,data,fmt='%f %f %f')
       ij_out2 = 'topo.ratll'
       goStr = 'SAT_llt2rat %s 1 < %s > %s' % (PRM,tmp_out2,ij_out2)
       print(" GMTSAR: %s" % goStr)
       os.system(goStr)
       ratdata = np.loadtxt(ij_out2)
       # print(ratdata)
       os.system('rm %s -f' % ij_out2)
       os.system('rm %s -f' % tmp_out2)
    #
    if ratdata is not None:
        #
        # bytes in defaults for ranges
        rminv = ratdata[:,0].min()/4
        rmaxv = ratdata[:,0].max()/4
        if rmaxv > maxrng - 1:
            rmaxv = maxrng - 1
        if rminv < 0:
            rminv = 0
        azmin = ratdata[:,1].min()
        azmax = ratdata[:,1].max()
        #
        if azmax > (maxrow-1):
            azmax = maxrow-1
        if azmin < 0:
            azmin = 0
        #
        if rmax:
           in_range = '%d/%d/%d/%d' % (0,maxrng-1,\
                                       azmin,azmax) 
        else:
           in_range = '%d/%d/%d/%d' % (rminv,rmaxv,\
                                       azmin,azmax)
           #
    return in_range
#
def gmtsar_baseline2master(inbaseline,mode=1):
    #
    # written by FWP, for an optimal master return
    #
    datapath,dinfo = gmtsar_baseline(inbaseline,mode=mode)
    # print(dinfo)
    outdata,master = pSAR.ts.baselineinfo2master(dinfo,Tc=1000,Bc=2000)
    #
    return outdata,master
    
#
def gmtsar_baseline(inbaseline,mode=1):
    # mode, 
    #   1 means that one works in F*/raw/*...
    #   2 means that one works in raw/tmpPRMs/...
    #
    datapath = []
    dinfo = []
    #
    with open(inbaseline,'r') as fid:
        for line in fid:
            tmp = line.split('\n')[0].split()
            datapath.append(tmp[0])
            #
            if mode == 1:
               slave_date = tmp[0].split('_')[1]
            else:
               slave_date = tmp[0].split('-')[4][0:8]
            #
            if len(tmp) > 4:
               try:
                   sdate = float(slave_date)
               except:
                   sdate = 0
               dinfo.append([float(tmp[4]),0.,sdate])
            else:
               dinfo.append([0,0.,float(slave_date)])
    # print(dinfo) 
    dinfo = np.array(dinfo)
    #
    index = np.where(dinfo[:,0]==0)[0]
    if len(index) == 0:
        master = ['99999999']
    else:
        master = dinfo[dinfo[:,0]==0,2]
    dinfo[:,1] = master[0]
    # 
    if dinfo[:,0].sum() == 0:
        for i in range(1,dinfo.shape[0]):
          dinfo[i,0] = random.randint(0,10)/10.0
    #
    return datapath,dinfo
#    
def gmtsar_dir2batchcfg(iws,target_dir=os.getcwd()):
    iws = np.array(iws)
    index = np.where(iws!=0)[0]
    # in default, F1, F2 or F3 should be in the local folder...
    #
    cfgs = glob.glob(target_dir+'/F%d/batch_config.cfg' % (index[0]+1))
    if len(cfgs) == 0:
        return None
    else:
        return cfgs[0]
def gmtsar_batchcfg2info(incfg):
    #
    info = {}
    with open(incfg,'r') as fid:
        for cline in fid:
            cline = cline.strip()
            if len(cline)>0 and cline[0]!='#':
                info[cline.split("=")[0].strip()] = \
                                   cline.split("=")[1].strip()  
    return info
def gmtsar4batchconf(outfile,step=1,master='',unwrap=0.05,switch_land=0,\
                    toposhift=0,flength=200,rlook=8,azlook=2,interp_flag=0):
    '''
    

    Parameters
    ----------
    outfile : TYPE
        DESCRIPTION.
    master : TYPE, optional
        DESCRIPTION. The default is ''.
    unwrap : TYPE, optional
        DESCRIPTION. The default is 0.05.

    Returns
    -------
    None.

    '''
    config_str=\
'''
#######################################
# processing stage for intf_batch.csh #
#######################################
# 1 - start from make topo_ra
# 2 - start from make and filter interferograms, unwrap and geocode
proc_stage = %d

# the namestem of the master image - REQUIRED
master_image = %s

#########################################
#   parameters for preprocess           #
#   - pre_proc_batch.csh                #
#   following 4 parameters are OPTIONAL #
#########################################
# num of patches
num_patches =

# earth radius
earth_radius =

#
# near_range
near_range =

# Doppler centroid
fd1 =

#####################################
#   parameters for make topo_ra     #
#   - dem2topo_ra.csh               #
#####################################
# subtract topo_ra from the phase
#  (1 -- yes; 0 -- no)
topo_phase = 1
#
# topo_ra shift (1 -- yes; 0 -- no)
shift_topo = %d 
####################################################
#   parameters for make and filter interferograms  #
#   - intf.csh                                     #
#   - filter.csh                                   #
####################################################
# region to process in radar coordinates (leave it blank if to process the whole region)
#  example format 500/10800/500/27200  - OPTIONAL
region_cut =

# filters
# look at the filter/ folder to choose other filters
filter_wavelength = %d

# decimation of images
# decimation control the size of the amplitude and phase images. It is either 1 or 2.
# Set the decimation to be 1 if you want higher resolution images.
# Set the decimation to be 2 if you want images with smaller file size.
#
dec_factor = 1
# for tops processing, to force the decimation factor
# recommended range decimation to be 8, azimuth decimation to be 2
range_dec = %d
azimuth_dec = %d
#####################################
#   parameters for unwrap phase     #
#   - snaphu.csh                    #
#####################################
# correlation threshold for snaphu.csh (0~1)
# set it to be 0 to skip unwrapping.
threshold_snaphu = %s

# interpolate masked or low coherence pixels with their nearest neighbors, 1 means interpolate,
# others or blank means using original phase, see snaphu.csh and snaphu_interp.csh for details
# this could be very slow in case a large blank area exist
near_interp = %d

# use landmask (1 -- yes; else -- no)
switch_land = %d
# Allow phase discontinuity in unrapped phase. This is needed for interferograms having sharp phase jumps.
# defo_max = 0 - used for smooth unwrapped phase such as interseismic deformation
# defo_max = 65 - will allow a phase jump of 65 cycles or 1.82 m of deformation at C-band
#
defomax = 0

#####################################
#   parameters for geocode          #
#   - geocode.csh                   #
#####################################
# correlation threshold for geocode.csh (0~1)
threshold_geocode = .0
'''
    if unwrap < 0.000001:
        unwrap_str = '0'
    else:
        unwrap_str = str(unwrap)
    #
    with open(outfile,'w') as fid:
       fid.write(config_str % (step,master,toposhift,flength,rlook,azlook,unwrap_str,interp_flag,switch_land))
    #
    if os.path.exists(outfile):
        return True
    else:
        return False
#
#
def dayofyear2yyyymmdd(dayofyear):
    #
    mydt = datetime.datetime(int(dayofyear[0:4]),1,1)
    days = int(dayofyear[4::])
    mydt = mydt + datetime.timedelta(days=days )
    return mydt.strftime('%Y%m%d')
#
###############################################################################
def prm2yyyymmdd(in_prm):
    #
    dateofyear = prm2date(in_prm)
    return dayofyear2yyyymmdd(dateofyear)
###############################################################################
def s1_subswaths_azi_offs(prm1,prm2):
    #
    info1 = prm2info(prm1)
    info2 = prm2info(prm2)
    #
    # print(info1)
    off1 = (float(info2['clock_start']) - float(info1['clock_start'])) * \
            86400.0 * float(info1['PRF'])
    return round(off1)
#
def s1_subswaths_rng_offs(prm1,prm2):
    #
    c_speed = 299792458.0
    info1 = prm2info(prm1)
    info2 = prm2info(prm2)
    #
    # rng_samp_rate is renamed to fs in gmt5sar
    #
    off1 = (float(info2['near_range']) - float(info1['near_range'])) / \
            (c_speed/float(info1['rng_samp_rate'])/2)
    #
    return round(off1)    
#
def prm2info(in_prm):
    #
    # 
    info = {}
    with open(in_prm,'r') as fid:
        for cline in fid:
            cline = cline.split('\n')[0]
            if '=' in cline:
               tmp = cline.split('=')
               if tmp[0] not in info:
                  str_iterm = tmp[0].split('\t')[0]
                  info[str_iterm.strip()] = tmp[1].strip()
    return info
#
def prm2wavelength(in_prm):
    info = prm2info(in_prm)
    return info['radar_wavelength']
def prm2time(in_prm):
    info = prm2info(in_prm)
    return info['SC_clock_start']
def prm2date(in_prm):
    #
    yearofdate = []
    #
    with open(in_prm,'r') as fid:
        #
        for cline in fid:
            cline = cline.split('\n')[0]
            if 'SC_clock_start' in cline:
                yearofdate = cline.split()[2].split('.')[0]
            #
        #
    #
    return yearofdate
#
###############################################################################
#
def s1TOstatevector(intime,mission,model='RESORB',\
                    orbdir='/home/wafeng/soft/InSAR/ORB/Sentinel_1/aux_resorb/',\
                    fmt='%Y-%m-%dT%H:%M:%S.%f'):
    #
    tinfo = datetime.datetime.strptime(intime,fmt)
    cyear = tinfo.year
    #
    stas  = glob.glob(orbdir+'/*_V%s*.EOF' % cyear)
    if tinfo.month < 10:
        cmonth = '0%d' % tinfo.month
    else:
        cmonth = '%d' % tinfo.month
    #
    stas  = glob.glob(orbdir+'/S1%s_*_V%s%s*.EOF' % (mission,cyear,cmonth))
    #
    outsta = 'None'
    if len(stas) > 0:
      times = [[pSAR.ts.timestr2jd(\
              os.path.basename(cfile).split('.')[0].split('_')[6][1::],\
              fmt='%Y%m%dT%H%M%S'),\
              pSAR.ts.timestr2jd(\
              os.path.basename(cfile).split('.')[0].split('_')[7],\
              fmt='%Y%m%dT%H%M%S')] for cfile in stas]
      times = np.array(times)
      reftimes = pSAR.ts.timestr2jd(intime,fmt=fmt)
      flag1 = times[:,0] <= reftimes
      flag2 = times[:,1] >= reftimes
      flag = flag1*flag2
      outsta = stas[flag]
    return outsta
        
    
