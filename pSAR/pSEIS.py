#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 29 22:47:32 2017

@author: wafeng
"""
import numpy as np
import scipy
import math
#
#
#
# Function to estimate b-value using maximum likelihood method (Aki, 1965), original Aki error estimate (Aki, 1965), and Shi & Bolt (1982) improved uncertainty estimate:
# mag: catalogue of magnitudes
# mbin: magnitude bin size
# mc: completeness magnitude

def b_est(mag, mbin, mc):
    #
    mag_above_mc = mag[np.where(mag > round(mc,1)-mbin/2)[0]] # Magnitudes for events larger than cut-off magnitude mc
    n = mag_above_mc.shape[0] # No of. events larger than cut-off magnitude mc
    
    #
    if n < 2:
        a = np.nan
        b = np.nan
        aki_unc = np.nan
        shibolt_unc = np.nan
    else:
        #
        # print(np.mean(mag_above_mc),np.median(mag_above_mc))
        # mbar = np.mean(mag_above_mc) # Mean magnitude for events larger than cut-off magnitude mc
        # median is proofed better than mean
        # improved by FWP, @SYSU, Guangzhou, 2022/06/05
        #
        mbar = np.median(mag_above_mc)
        # b = math.log10(math.exp(1)) / (mbar - (mc - mbin/2)) # b-value from Eq 3
        # a = math.log10(n) + b * mc # 'a-value' for Eq 2
        #
        # we used linear least-square method to estiamte a and b...
        #
        mi,nbmag,cumnbmag = fmd(mag_above_mc, mbin)
        cumnbmag[np.isnan(cumnbmag)] = 0
        mi = mi[cumnbmag!=0]
        cumnbmag = cumnbmag[cumnbmag!=0]
        #
        index = np.where(cumnbmag <= 10)[0]
        maxmag = np.min(mi[index])
        mag_above_mc = mag_above_mc[np.where(mag_above_mc <= maxmag)[0]]
        #
        cumnbmag = cumnbmag[(mi+mbin/2)<=maxmag]
        mi = mi[(mi+mbin/2)<=maxmag]
        #
        D = np.log10(cumnbmag)
        A = np.zeros([D.shape[0],2])
        A[:,0] = 1
        A[:,1] = mi * -1
        #
        est_ab,res,rnks,s = np.linalg.lstsq(A,D,rcond=0.01)
        # print(est_ab,[a,b])
        a = est_ab[0]
        b = est_ab[1]
        #
        aki_unc = b / math.sqrt(n) # Uncertainty estimate from Eq 4
        shibolt_unc = 2.3 * b**2 * math.sqrt(sum((mag_above_mc - mbar)**2) / (n * (n-1))) # Uncertainty estimate from Eq 5

    return a, b, aki_unc, shibolt_unc # Return b-value and estimates of uncertainty
#
# Function to get completeness magnitude with maxc method
# 
def get_maxc(mag, mbin):
    this_fmd = fmd(mag, mbin) # FMD
    maxc = this_fmd[0][np.argmax(this_fmd[1])] # Mag bin with highest no. of events
    return round(maxc, 1)
#
# Frequency-magnitude distribution function (Mignan & Woessner article)

# mag: catalogue of magnitudes
# mbin: magnitude bin size
#
def fmd(mag, mbin):
    minmag = math.floor(min(mag/mbin)) * mbin # Lowest magnitude bin
    maxmag = math.ceil(max(mag/mbin)) * mbin # Highest magnitude bin
    mi = np.arange(minmag, maxmag + mbin, mbin) # Sequence of magnitude bins
    nbm = len(mi) # No. of magnitude bins
    cumnbmag = np.zeros(nbm) # Pre-allocate array for cumulative no. of events in mag bin and higher

    # Get cumulative no. of events in mag bin and higher
    for i in range(nbm):
        cumnbmag[i] = np.where(mag > mi[i] - mbin/2)[0].shape[0]

    # Get no. of events in each mag bin:
    nbmag = abs(np.diff(np.append(cumnbmag, 0)))

    return mi, nbmag, cumnbmag # Return magnitude bins, no. of events in bin, and cumulative no. of events
#

#
def func_p(x,k,c,p):
    #
    # Utsu, 1964
    # Omori, 1894
    return k/(x+c)**p
#
def afts_gr(mags):
    #
    umag = np.sort(np.unique(mags))
    #
    data = []
    for mag in umag:
        #
        index = np.where(mags>=mag)[0]
        data.append([mag,index.shape[0]])
        #
    return np.array(data)
    #
def omori_est(x,y,p0=None,theilsen=False):
    #
    if p0 is not None:
       paras, para_cov = scipy.optimize.curve_fit(func_p,x,y)
    else:
       paras, para_cov = scipy.optimize.curve_fit(func_p,x,y,p0)
    #
    out_index = None
    if theilsen:
        #
        res = (y - func_p(x,paras[0],paras[1],paras[2]))**2
        sort_res = np.sort(res)
        n_res = sort_res.shape[0]
        #
        index = int(n_res * 0.1)
        threshold_res = sort_res[index*-1]
        x1 = x[res<=threshold_res]
        y1 = y[res<=threshold_res]
        out_index = np.where(res>threshold_res)[0]
        paras, para_cov = scipy.optimize.curve_fit(func_p,x1,y1,paras)
        

    return paras,para_cov,out_index
#
def afts_omori(jdtimes,twindows):
    #
    t_int = jdtimes.astype('int')
#     

    min_date = np.min(t_int)
    max_date = np.max(t_int)
    #
    outdata = []
    times = np.array(range(min_date,max_date,twindows))
    for i in range(times.shape[0]-1):
        #
        d1 = t_int>=times[i]
        if i < times.shape[0]-1:
          d2 = t_int<times[i+1]
        else:
          d2 = t_int * 0 + 1
        #
        ttimes = d1 * d2 
        index = np.where(ttimes>0)[0]
        outdata.append([times[i],index.shape[0]])
    #
    return np.array(outdata)
#
def psmeca2ntb(psmeca):
    #
    mstrike  = psmeca[:,3]
    mdip     = psmeca[:,4]
    mrake    = psmeca[:,5]
    # print(mrake)
    mn = np.zeros([mstrike.shape[0],2])
    mt = np.zeros([mstrike.shape[0],2])
    mp = np.zeros([mstrike.shape[0],2])
    for i in range(mstrike.shape[0]):
        pbt, tmp = focal2pbt(mstrike[i],mdip[i],mrake[i])
        mn[i,:] = pbt[1,:]
        mt[i,:] = pbt[2,:]
        mp[i,:] = pbt[0,:] 
    return mn,mt,mp
#
def arr_mecsort(mstr,mdip,mrake):
    # array version for mecsort()
    # 
    # mflag = np.zeros(mstr.shape[0])
    #
    mflag = [mecsort(mstr[i],mdip[i],mrake[i]) for i in range(mstr.shape[0])]
    return np.array(mflag)
#
def mecsort(strike,dip,rake):
    #
    # learnt from a matlab-based code, written by Xu Zhang
    # flag for mechanisms based on plunge angles of P,B and T axies.
    # created by FWP, @SYSU, Guangzhou, 2020/10/11
    #
    # note that flag means...
    # 1, strike-slip
    # 2, normal-faulting
    # 3, thrust-faulting
    # 0, oblique slip
    #
    ptb,_ = focal2pbt(strike,dip,rake)
    plg = ptb[:,1]
    #
    flag = 0
    if plg[1] >= 45 and plg[0] < 45 and plg[2] < 45:
        flag = 1
    elif plg[2] >= 45 and plg[0] < 45 and plg[1] < 45:
        flag = 2
    elif plg[0] >= 45 and plg[2] < 45 and plg[1] < 45:
        flag = 3
    #
    return flag
    #
def focal2pbt(strike,dip,rake):
    #
    # from a set of plane parameters to derive p,b,t axises
    # by Wanpeng Feng, @Ottawa
    #
    mt,M = fault2mt(strike,dip,rake)
    # print(mt)
    pbt,value = mt2azi(mt)
    return pbt,value
#     
def dir_cosin_xyz2trendplunge(l,m,n):
    #
    # l,m,n correspond to x,y,z
    #
    if n < 0:
       l = -1. * l
       m = -1. * m
       n = -1. * n
    #
    mag = np.sqrt(l**2+m**2+n**2)
    l   = l/mag
    m   = m/mag 
    n   = n/mag
    #
    plunge  = 90-180/np.pi*np.arctan2(np.sqrt(l**2+m**2),n) # degrees(plunge_radians);
    #
    azimuth = np.arctan2(m,l)*180/np.pi
    if azimuth < 0:
        azimuth = azimuth + 360.
    if plunge < 0:
       plunge = plunge*-1.
       azimuth  = azimuth+180
       if azimuth > 360:
        azimuth = azimuth-360
    #
    return azimuth,plunge

def nodal1TOnodal2(strike,dip,rake):
    #
    '''
    Calculate another nodal plane from the given geometry parameters:
        strike,dip and rake, which are all in degree 
    by Wanpeng Feng, @NRcan, 2017-11-09
    '''
    mt,M   = fault2mt(strike,dip,rake)
    faults = mt2faults(mt)
    diffs  = np.zeros(faults.shape[0])
    infault = np.array([strike,dip,rake])
    #
    for i in range(faults.shape[0]):
        diffs[i] = np.sum((faults[i,:]-infault)**2)
    index = np.where(diffs == np.max(diffs))[0][0]
    return faults[index,:]
#
def mt2faults(mt):
    '''
    Moment tensor to fault plane solutions
    The python code is based on a matlab code made by Prof. Lisheng Xu
    by Wanpeng Feng, @CCRS/NRCan, 2017-11-09
    '''
    tbpvec,tbpval = mt2axis(mt)
    #
    tvec = tbpvec[:,0]
    pvec = tbpvec[:,2]
    flag = np.sum(np.iscomplex(tbpval))
    #
    if flag > 0:
       print(" Errors: a complex number is detected !!!!") 
       return None
    #
    # plane I
    uone=np.sqrt(2)*(tvec+pvec)/2
    vone=np.sqrt(2)*(tvec-pvec)/2
    if vone[2]>0:
        vone=-vone
        uone=-uone
    #
    # Plane II
    #
    utwo=np.sqrt(2)*(tvec-pvec)/2
    vtwo=np.sqrt(2)*(tvec+pvec)/2
    #
    if vtwo[2]>0:
       vtwo=-1.*vtwo
       utwo=-1.*utwo
    #
    u=np.hstack((np.reshape(uone,[3,1]),np.reshape(utwo,[3,1])))
    v=np.hstack((np.reshape(vone,[3,1]),np.reshape(vtwo,[3,1])))
    #
    # calculate the fault parameters
    faults=np.zeros([2,3])
    #
    for kk in range(2):
      dip    = np.arccos(-v[2,kk])
      strike = np.arctan2(-v[0,kk],v[1,kk])
      rake   = np.arctan2(-u[2,kk]/np.sin(dip),\
                          u[0,kk]*np.cos(strike)+u[1,kk]*np.sin(strike))
      faults[kk,:] = [strike,dip,rake]
    #
    faults = faults * 180 / np.pi
    faults[faults[:,0]<0,0] = 360 + faults[faults[:,0]<0,0]
    return faults
#
###############################################################################   
#
def mt2azi(mt):
    vec,val = mt2axis(mt)
    azi = np.zeros([3,2])
    for i in range(azi.shape[0]):
        t,p = dir_cosin_xyz2trendplunge(vec[0,i],vec[1,i],vec[2,i])   
        azi[i,:] = [t,p]
    return azi,val
#
###############################################################################
#
def mt2axis(mt):
    '''
    Calculate coordinates of axises, P,B and T
    by Wanpeng Feng, @NRCan, 2017-11-09
    '''
    meigval,eigvec = np.linalg.eig(mt)
    #
    eigval = meigval # np.diag(meigval)
    #
    #
    ott  = [i for i in range(3)]
    tval = np.where(eigval==np.max(eigval))[0]  # maximum
    pval = np.where(eigval==np.min(eigval))[0]  # minimum
    #
    if len(tval) == 2:
        pval = tval[0]
        tval = tval[1]
    else:
        tval = tval[0]
    if len(pval) == 2:
        tval = pval[0]
        pval = pval[1]
    else:
        pval = pval[0]
    #
    odex = [tval,pval]
    bval = np.array([tmp not in odex for tmp in ott])
    bval = ott[np.where(bval)[0][0]]
    #
    # Separate the coordinates of T,B and P axis in order
    # of x,y and z
    #
    taxis=np.reshape(eigvec[:,tval],[3,1])
    baxis=np.reshape(eigvec[:,bval],[3,1])
    paxis=np.reshape(eigvec[:,pval],[3,1])
    #
    # Only for output
    tbpvec=np.hstack((taxis,baxis)) 
    tbpvec=np.hstack((tbpvec,paxis))
    tbpval=np.array([eigval[tval],eigval[bval],eigval[pval]])
    #
    return tbpvec,tbpval

def fault2mt(strike,dip,rake):
    '''
    Calculate moment tensor from a nodal plane solution
    by Wanpeng Feng, @CCRS/NRCan, 2017-11-08
    
    '''
    pi     = np.arctan(1)*4;
    DEG    = pi/180;
    strike = DEG*strike;
    dip    = DEG*dip;
    rake   = DEG*rake;
    #
    M0  =    1;
    m11 =   -1*M0*(np.sin(dip)*np.cos(rake)*np.sin(2*strike) + \
                   np.sin(2*dip)*np.sin(rake)*np.sin(strike)**2)
    m12 =    1*M0*(np.sin(dip)*np.cos(rake)*np.cos(2*strike) + \
                   0.5*np.sin(2*dip)*np.sin(rake)*np.sin(2*strike))
    m13 =   -1*M0*(np.cos(dip)*np.cos(rake)*np.cos(strike) + \
                   np.cos(2*dip)*np.sin(rake)*np.sin(strike))
    m22 =    1*M0*(np.sin(dip)*np.cos(rake)*np.sin(2*strike) - \
                   np.sin(2*dip)*np.sin(rake)*np.cos(strike)**2)
    m23 =   -1*M0*(np.cos(dip)*np.cos(rake)*np.sin(strike) - \
                   np.cos(2*dip)*np.sin(rake)*np.cos(strike))
    m33 =    1*M0*np.sin(2*dip)*np.sin(rake)
    #
    M   = [m11,m12,m13,m22,m23,m33]
    mt  = [m11,m12,m13,m12,m22,m23,m13,m23,m33]
    mt  = np.reshape(np.array(mt),[3,3])
    return mt,M
#
#
