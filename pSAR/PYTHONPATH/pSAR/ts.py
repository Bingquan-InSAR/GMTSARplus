#!/usr/bin/env python
#
"""
   Reshape a previous module, sbas.py to a new one, ts.py 
   by Wanpeng Feng, @CCRS/NRCan, 2017-03-01
   ---
   SBAS is one of time sereis methods proposed since 2002, in which only small-baseline
   Interferograms were supposed to use for ts analysis. However, since 2014, new generation of
   SAR sensors are available after Sentinel-1 and ALOS2 were successfully sent into orbit.
   All InSAR pairs can have "small" baseline, shorter than 200 m. Optimistically, 50% of potential
   pairs will have baselines < 100m. In general, all ts analysis is based on SBAS in default.
   ---
   Since ts.py is available, sbas.py will not be updated any more. All functions from sbas
   have been adopted into ts.py. 
   Noted by Wanpeng Feng, @CCRS/NRCan, 2017-03-01
   
"""
#
from . import utm_conversion
from . import opt
from . import jdutil
from . import roipac
from . import br
import shutil
import os
import sys
import numpy as np
import scipy.stats
from scipy.optimize import least_squares
from scipy.sparse.linalg import cg
from scipy.sparse.linalg import lsmr
#
import scipy as sc
import platform
import datetime      #from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mt_dates
import multiprocessing as mp
#
# below is first used for passing multiple arguments into multiprocessing
from functools import partial
from scipy.linalg.blas import dgemm
import glob
import pDATA
#
###############################################################################
def def_func_model3(p,x,x0):
    #
    # In default, x  means time series in second or days
    #             x0 means time when the earthquake occurres 
    # 
    # deformation model including annual changes, postseismic (log), coseismic 
    # and interseismic (linear) components
    # by Wanpeng Feng, @SYSU, Zhuhai, 2023/03/07
    # 
    C,A,a1,V,b,a2 = p
    #
    # modified by FWP, 2022/12/30
    #
    outy = np.copy(x)*0
    outy[x>x0]  = (C+A*np.log(1+(x[x>x0]-x0)*a1))+V*x[x>x0]+b+a2*np.sin(2*np.pi*x[x>x0])
    outy[x<=x0] = V*x[x<=x0]+b+a2*np.sin(2*np.pi*x[x<=x0])
    # return H*(C+A*np.log(1+x*a1))+V*x+b
    return outy
#
def s1_dir2dates(in_dir):
    #
    outdates = []
    for czip in glob.glob(in_dir+'/S*.zip'):
        #
        czip = os.path.basename(czip)
        cdate = pDATA.s1zip2date(czip)
        # print(czip,cdate)
        outdates.append(float(cdate))
        #
    return outdates

def dir2dates(in_dir):
    #
    outdates = []
    for czip in glob.glob(in_dir+'/S*.zip'):
        #
        czip = os.path.basename(czip)
        cdate = pDATA.s1zip2date(czip)
        # print(czip,cdate)
        outdates.append(float(cdate))
        #
    return outdates

def ui_ts_dates(dates):
    #
    profdates = dates2interval(dates)
    #
    #
    sdates = dates2dates(profdates[:,0])
    myFmt = mt_dates.DateFormatter('%Y-%m-%d')
    #
    plt.plot(sdates,profdates[:,1],'o-',label='%d Acq.' % dates.shape[0])
    #
    plt.legend()
    ax = plt.gca()
    #
    ax.xaxis.set_major_formatter(myFmt)
    #
    labels = ax.get_xticklabels()
    plt.setp(labels, rotation=20, fontsize=10)
    #
    plt.xlabel(" Time Information (YYYY-MM-DD) ",fontsize=14.5)
    plt.ylabel(" Temporal sampling(days)",fontsize=14.5)
    #
    return True
#
def dates2interval(dates):
    #
    outprof = []
    #
    for i in range(dates.shape[0]-1):
        #
        d1 = str(int(dates[i]))
        d2 = str(int(dates[i+1]))
        inv = diff2dates(d1,d2)
        outprof.append([float(d1),inv])
        outprof.append([float(d2),inv])
    #
    return np.array(outprof)
#
def ex_lsq(a, b, residuals=False):
    """
    Return the least-squares solution to a linear matrix equation.
    Solves the equation `a x = b` by computing a vector `x` that
    minimizes the Euclidean 2-norm `|| b - a x ||^2`.  The equation may
    be under-, well-, or over- determined (i.e., the number of
    linearly independent rows of `a` can be less than, equal to, or
    greater than its number of linearly independent columns).  If `a`
    is square and of full rank, then `x` (but for round-off error) is
    the "exact" solution of the equation.
    Parameters
    ----------
    a : (M, N) array_like
        "Coefficient" matrix.
    b : (M,) array_like
        Ordinate or "dependent variable" values.
    residuals : bool
        Compute the residuals associated with the least-squares solution
    Returns
    -------
    x : (M,) ndarray
        Least-squares solution. The shape of `x` depends on the shape of
        `b`.
    residuals : int (Optional)
        Sums of residuals; squared Euclidean 2-norm for each column in
        ``b - a*x``.
    """
    if type(a) != np.ndarray or not a.flags['C_CONTIGUOUS']:
        print('Matrix a is not a C-contiguous numpy array. The solver will create a copy, which will result' + \
             ' in increased memory usage.')

    a = np.asarray(a, order='c')
    i = dgemm(alpha=1.0, a=a.T, b=a.T, trans_b=True)
    x = np.linalg.solve(i, dgemm(alpha=1.0, a=a.T, b=b)).flatten()

    if residuals:
        return x, np.linalg.norm(np.dot(a, x) - b)
    else:
        return x

def ts_loop2phss(in_loop_filename):
    #
    bname = os.path.basename(in_loop_filename).split('.')[0]
    tmp = bname.split('_')
    phs1 = 'geo_%s_%s' % (tmp[1],tmp[2])
    phs2 = 'geo_%s_%s' % (tmp[1],tmp[3])
    phs3 = 'geo_%s_%s' % (tmp[2],tmp[3])
    return [phs1,phs2,phs3]
#
def ts_pts(cfile,pts):
    #
    data = br.brlllist(cfile,pts)
    info,ext = roipac.rsc_read(cfile+'.rsc')
    data[:,2] = data[:,2] - float(info['Z_SHIFT'])
    #
    return data[:,2]
#
def ts_importpts(filelist, pts, njob):
    
    cpool = mp.Pool(processes=njob)
    ts_pts_partial = partial(ts_pts,pts=pts)
    results = cpool.map(ts_pts_partial,filelist)
    cpool.close()
    cpool.join()
    return np.array(results)
#
#
def doy2time(intime,fmt='%Y%jT%H:%M:%S.%f',of='%Y%m%dT%H%M%s.%f'):
    '''
    
    Parameters
    ----------
    intime : TYPE
        DESCRIPTION.
    fmt : TYPE, optional
        DESCRIPTION. The default is '%Y%m%dT%H:%M:%S.%f'.

    Returns
    -------
    convert a decimal date number, year + day of year + fraction of day
    to standard time info...
    
    Note that the internal function datetime have one day different with the
    day of year...
    
    Below I add 1 more day after the date number....
    by Wapeng Feng, @SYSU, Guangzhou, 2020/04/19
    
    No additional day was added since this version (2020/12/27)
    
    fixed a bug for the first day of year, by FWP, 2021/02/03

    '''
    intime = float(intime)
    year   = int(str(intime)[0:4])
    days   = str(intime).split('.')[0][4::]
    days   = '%03d' % int(days)
    #
    # updated by FWP, @SYSU, Guangzhou, 2021/02/03
    # the first day of year will call some error in the previous version, 
    # which has been fixed sicne this version.
    #
    go_back_1day = False
    if days=='000':
        days = '001'
        go_back_1day = True
    #
    hh     = int((intime - int(intime))*24)
    mm     = int((intime - int(intime))*24*60 - hh*60)
    ss     = (intime - int(intime))*24*60*60 - hh * 60 * 60 - mm * 60
    intime_str ='%d%sT%d:%d:%f' % (year,days,hh,mm,ss)
    #
    dt = datetime.datetime.strptime(intime_str,fmt)
    if go_back_1day:
        dt =  dt + datetime.timedelta(days=-1)
    # 
    return dt.strftime(of)
    
def ts_pariVtodateV(vel):
    #
    dateV = np.zeros(vel.shape[0]+1)
    for i in range(dateV.shape[0]):
        if i > 0:
            dateV = dateV[i] - vel[i-1]
    return dateV
#
def func_exp(x,t,y):
    return x[0] + x[1] * np.exp(x[2] * t) - y
#
def func_log(x,t,y):
    '''
    '''
    return x[0] + x[1] * np.log(1+t/x[2]) - y
#
def ts_regress_exp(indata,x0=[0.0,1.0,1.0],loss='linear',f_scale=0.01):
    '''
    d(t) = c * ln(1+t/taul)
    where c is a constant, and taul is a decay time  following the mainshock
    t, is differential days since the reference.
    
    '''
    results = least_squares(func_exp, x0, loss=loss, \
                  f_scale=f_scale,args=(indata[:,0], indata[:,1]))
    return results
def ts_regress_log(indata,x0=[0.0,1.0,1.0],loss='linear',f_scale=0.01):
    '''
    d(t) = c * ln(1+t/taul)
    where c is a constant, and taul is a decay time  following the mainshock
    t, is differential days since the reference.
    
    '''
    results = least_squares(func_log, x0, loss=loss, \
                  f_scale=f_scale,args=(indata[:,0], indata[:,1]))
    return results
# 
def ts_individualAPS2v0(inv0):
    v0 = np.zeros(inv0.shape[0]-1)
    for i in range(inv0.shape[0]-1):
        v0[i] = inv0[i] - inv0[i+1]
    return v0

def ts_apsA2index(apsA):
    #
    mindex = np.zeros(apsA.shape[1])
    for i in range(apsA.shape[0]):
        mindex[apsA[i,:]==1] = 1
    return mindex
    #
    
def monthsrange(m1,m2):
    #
    m1,m2 = int(m1),int(m2)
    #
    if m1 < 1 or m1 > 12:
        print(" WARNING: a given month must be between 1 and 12.!!")
        m1 = 1
    if m2 < 1 or m2 > 12:
        print(" WARNING: a given month must be between 1 and 12.!!")
        m2 = 12
    #
    fullmrange = np.array([i+1 for i in range(12)])
    #
    index1 = np.where(fullmrange==m1)[0][0]
    index2 = np.where(fullmrange==m2)[0][0]
    if index1 <= index2:
        outrange = list(range(index1,index2+1))
    else:
        t1 = index2
        t2 = index1
        #
        # exceptional range of month info
        #
        tmprange = list(range(t1+2,t2+1))
        outrange = [i for i in fullmrange if i not in tmprange]   
        #
    return outrange
#
###############################################################################
def ts_pairtimeinfo_cdate(pair_time_info,cdate):
    #
    index_arr = np.zeros(pair_time_info.shape[0])
    for i in range(pair_time_info.shape[0]):
        if int(pair_time_info[i,0])==int(cdate):
            index_arr[i] = 1
        elif int(pair_time_info[i,1])==int(cdate):
            index_arr[i] = -1
    return index_arr
#
def ts_dateinpair(pair,cdate):
    #
    # in default, pair is in ROI_PAC format
    #
    info,_ = roipac.rsc_read(pair+'.rsc')
    m_date = int(info['MASTER'])
    s_date = int(info['SLAVE'])
    #
    factor = 0
    if m_date == int(cdate):
        factor = 1
    if s_date == int(cdate):
        factor = -1
    #
    cdiff = diff2dates(tsstr(m_date),tsstr(s_date))
    #
    return factor,abs(cdiff)
#
###############################################################################
#
def ts_dateINpairs_info(dpath,cdate,dinfo_jd=None,max_time_lag=9999999):
    '''
    Return array having factors to indicate 
          if the pair includes the time (cdate)
    '''
    factorarr = []
    for cpath in dpath:
        #
        factor, cdiff = ts_dateinpair(cpath,cdate)
        if dinfo_jd is not None and cdiff > max_time_lag:
            factor = 0
        #
        factorarr.append([factor,cdiff])
    #
    return np.array(factorarr)
#
def ts_apsADD(phsarr,phsindex):
    '''
    APS estimation method based on a way proposed by Ekaterina Tymofyeyeva and 
    Yuri Fialko
    
    '''
    D = phsindex[:,0] * 0
    for ni in range(D.shape[0]):
        D[ni] = phsarr[phsindex[ni,0]] - phsarr[phsindex[ni,1]]
    return D
#
def ts_APS_Eka_udate2full(udates,inv=6):
    #
    # inv, interval days, 6 days for Sentinel-1A/B
    # by Wanpeng Feng, @SYSU, Guangzhou, 2020/02/11
    #
    minT = udates.min()
    maxT = udates.max()
    goFlag = True
    outdata = []
    outdata.append(int(minT))
    cdate = minT
    while goFlag:
        cdate = newdate(int(cdate),inv)
        if int(cdate) <= int(maxT):
           outdata.append(int(cdate))
        else:
            goFlag = False
        #
    #
    return np.array(outdata)
#
def ts_rankaps(apsarray,aps):
    #
    tmpaps = [abs(aps[apsarray[i][0]]) for i in range(len(apsarray)) ]
    index = np.argsort(np.array(tmpaps))
    #
    #  reverse the order of index by using [::-1]
    #
    return index[::-1]
#

def ts_updatepts(in_pts,aps,pairID):
    #
    pts = np.copy(in_pts)
    index = np.where(aps!=0)[0]
    for i in index:
        master_indx_arr = np.where(pairID[:,0] == i)[0]
        slave_indx_arr = np.where(pairID[:,1] == i)[0]
        pts[master_indx_arr] = pts[master_indx_arr] - aps[i]
        pts[slave_indx_arr]  = pts[slave_indx_arr]  + aps[i]
    return pts
#
def ts_estaps_iter(in_pts,apsarray,udates,pairID,maxpairs=99999,aps=None, iters=5):
    #
    #
    if aps is None:
       aps = ts_pts2aps(in_pts,apsarray,udates,maxpairs=maxpairs)
    #
    iters = iters - 1
    #
    while iters > 0:
        # make a copy of phase history of pts, (in_pts)
        pts = np.copy(in_pts)
        #
        rindex = ts_rankaps(apsarray,aps)
        #
        for jj in rindex:
          #
          aps = ts_pts2aps(pts,apsarray,udates,aps=aps,\
                              orders=[jj],maxpairs=maxpairs)
          #
          # update phs history of pts by removing the maximum aps at rindex[0]
          #
          maxaps_id       = apsarray[jj][0]
          master_indx_arr = np.where(pairID[:,0] == maxaps_id)[0]
          slave_indx_arr  = np.where(pairID[:,1] == maxaps_id)[0]
          pts[master_indx_arr] = pts[master_indx_arr] - aps[maxaps_id]
          pts[slave_indx_arr]  = pts[slave_indx_arr]  + aps[maxaps_id]
        #
        # aps = aps + caps
        iters  = iters - 1
        #
    return aps  
#
def ts_pts2aps(pts,apsarray,udates,aps=None,orders=None,maxpairs=1000):
    # an order of estimating aps 
    # it is supposed to estimate the maximum aps at the very first place...
    #
    # aps and orders should be given at the same time...
    #
    if aps is None:
       aps = np.copy(udates) * 0
    # 
    if orders is None:
        orders = [i for i in range(len(apsarray))]
    #
    for i in orders:
        #
        date_no = apsarray[i][0]
        apsMatrix = np.array(apsarray[i][1])
        # 
        n_aps = apsMatrix.shape[0]
        if n_aps > maxpairs:
            n_aps = maxpairs
        #
        for j in range(n_aps):
            #
            caps = (pts[apsMatrix[j,0]] * apsMatrix[j,2] + \
                    pts[apsMatrix[j,1]] * apsMatrix[j,3])/2
            if j == 0:
                MY_APS = caps
            else:
                MY_APS = MY_APS+caps
        #
        MY_APS = MY_APS / n_aps
        aps[date_no] = MY_APS
    return aps
#
def ts_pairshavingCOS(pairs_IDS,pairArr,udates,cosd):#
    #
    # (pairArr, N x 3, master_date_ID, slave_date_ID, temporal_diff
    #
    flag = np.copy(pairs_IDS)*0+1
    #
    for j in range(pairs_IDS.shape[0]):
        i = pairs_IDS[j]
        mdate = udates[int(pairArr[i,0])]
        sdate = udates[int(pairArr[i,1])]
        if int(mdate)<=int(cosd) and int(sdate)>=int(cosd):
            flag[j] = 0
        #
    return pairs_IDS[flag==1]
#
def ts_pairIDs4apssyn(pairIDs,udates,cosd=None):
    #
    # pairIDs generated from ts_infs2apsA()
    # i is date index
    # j is pair index
    #
    outAPSarray = []
    for i in range(udates.shape[0]):
        #
        index_in_master = np.where(pairIDs[:,0] == i)[0]
        index_in_slave  = np.where(pairIDs[:,1] == i)[0]
        #
        if cosd is not None:
            #
            index_in_master = ts_pairshavingCOS(index_in_master,pairIDs,\
                                                udates,cosd)
            index_in_slave = ts_pairshavingCOS(index_in_slave, pairIDs,\
                                                udates,cosd)
        #
        cdata = []
        for master_j in index_in_master:
            slaves = np.where(\
                          pairIDs[index_in_slave,2] == pairIDs[master_j,2])[0]
            #
            if len(slaves)>0:
                slave_j = index_in_slave[slaves][0]
                # print(pairIDs[master_j,:],pairIDs[slave_j,:])
                cdata.append([master_j,slave_j,1,-1])
            #
        #
        if len(cdata)>0:
            outAPSarray.append([i,cdata])
    #
    return outAPSarray
            
def ts_infs2apsA(datainfo):
    '''
    infs2 simple A and time information of pair
    
    '''
    udates = np.sort(np.unique(datainfo[:,1::]))
    #
    # matrix I based on interfeorgram itself
    # A_con, array for master_aps and slave aps for each pair
    #        N x M, where N is the number of interferograms used here
    #                     M is the number of unique dates included in the data
    #
    A_con = np.zeros([datainfo.shape[0],udates.shape[0]])
    pairMatrix = np.zeros([datainfo.shape[0],3])
    for ni in range(datainfo.shape[0]):
        m_indx = np.where(udates == datainfo[ni,1])[0]
        s_indx = np.where(udates == datainfo[ni,2])[0]
        diffdays = diff2dates(str(datainfo[ni,1]),str(datainfo[ni,2]))
        A_con[ni,m_indx[0]] = -1.
        A_con[ni,s_indx[0]] = 1.
        #
        pairMatrix[ni,:] = [m_indx[0],s_indx[0],diffdays]
    #
    return A_con, pairMatrix,udates
    # 
def udates2datetime(udates):
    return [datetime.datetime.strptime(tsstr(cdate),'%Y%m%d') for cdate in udates]
#
def vmatrix2annualrate(varr,vmatrix):
    tinv = np.array([yyyymmdd2jd(vmatrix[i,1])-yyyymmdd2jd(vmatrix[i,0]) \
            for i in range(vmatrix.shape[0])])
    return varr / tinv * 365.
def vmatrix2centerdatetime(vmatrix):
    return [jdutil.jd_to_datetime(cjd) for cjd in vmatrix2centertime(vmatrix)]
    #
def vmatrix2centertime(vmatrix):
    return np.array([(yyyymmdd2jd(vmatrix[i,0])+yyyymmdd2jd(vmatrix[i,1]))/2 \
            for i in range(vmatrix.shape[0])])
    #
def ts_julian(dates):
    return [yyyymmdd2jd(cdate) for cdate in dates]
#
def ts2udates(datainfo):
    return np.sort(np.unique(np.ravel(datainfo)))
#
def ts_infs2datephs(datainfo):
    #
    udates = ts2udates(datainfo)
    A = np.zeros([datainfo.shape[0]+1,udates.shape[0]])
    #
    for ni in range(datainfo.shape[0]):
        #
        A[ni,udates==datainfo[ni,0]] = -1
        A[ni,udates==datainfo[ni,1]] =  1
    return A
#
def ts_acc(vs):
    # 
    outvs = vs * 0.
    for i in range(vs.shape[0]):
        if i == 0:
            outvs[i] = vs[i]
        else:
            outvs[i] = vs[i] + outvs[i-1]
    return outvs
############################################################################### 
def tsstr(vfn):
    # force date information to a string as "YYYYMMDD"
    #
    return str(int(vfn))
#
def ts_laplacianV(vmatrix):
    #
    lap = np.zeros([vmatrix.shape[0]-1,vmatrix.shape[0]])
    #
    for i in range(vmatrix.shape[0]-1):
        if i > 1:
          lap[i,i] = 2. / diff2dates(tsstr(vmatrix[i,0]),tsstr(vmatrix[i,1]))
          lap[i,i+1] = -1. / diff2dates(tsstr(vmatrix[i+1,0]),tsstr(vmatrix[i+1,1]))
          lap[i,i-1] = -1. / diff2dates(tsstr(vmatrix[i-1,0]),tsstr(vmatrix[i-1,1]))
        else:
          lap[i,i] = 1. / diff2dates(tsstr(vmatrix[i,0]),tsstr(vmatrix[i,1]))
          lap[i,i+1] = -1. / diff2dates(tsstr(vmatrix[i+1,0]),tsstr(vmatrix[i+1,1]))
          
    #
    invlap = lap * -1.
    lap = np.vstack((lap,invlap))
    return lap
#
def ts_coef4v(vmatrix,cpair):
    '''
    return coeffients of velocities for an interferogram pair
    vmatrix    n x 2 array, a velocity array from starting date to the end
    cpair      2 x 2 array recording the date information
    all dates in integer, e.g. YYYYMMDD, 20150101
    '''
    #
    coef = vmatrix[:,0] * 0.
    #
    for i in range(vmatrix.shape[0]):
        #
        if (vmatrix[i,0] >= cpair[0] and vmatrix[i,1] <= cpair[1] \
            and vmatrix[i,1] > cpair[0]):
            coef[i] = 1.
        if (vmatrix[i,0] >= cpair[0] and vmatrix[i,1] >= cpair[1] \
            and vmatrix[i,0] < cpair[1]): 
            coef[i] = float(diff2dates(tsstr(vmatrix[i,0]),tsstr(cpair[1])))/\
                      float(diff2dates(tsstr(vmatrix[i,0]),tsstr(vmatrix[i,1])))
        if (vmatrix[i,0] <= cpair[0] and vmatrix[i,1] <= cpair[1] \
            and vmatrix[i,1] > cpair[0]):
            coef[i] = float(diff2dates(tsstr(cpair[0]),tsstr(vmatrix[i,1])))/\
                      float(diff2dates(tsstr(vmatrix[i,0]),tsstr(vmatrix[i,1])))
    #
    return coef
#
def ts_infs2t(datainfo):
    #
    udates = np.sort(np.unique(datainfo[:,1::]))
    outtinfo = np.zeros([udates.shape[0]-1,3])
    for i in range(outtinfo.shape[0]):
        #
        outtinfo[i,0:2] = [udates[i],udates[i+1]]
        outtinfo[i,2]   = diff2dates(str(udates[i]),str(udates[i+1]))
        #
    return outtinfo
#
def ts_APS_j4dates(apsM,apsInd,phase_data_j,dsim=None):
    '''
    '''
    apsD = np.zeros(len(apsM))
    for i in range(len(apsM)):
        apsD[i] = ts_APS_j(apsM[i],apsInd[i],phase_data_j,dsim=dsim)
    return apsD
#
def ts_APS_j(APSMatrix_i,zero_def_index_i,phasedata_j,dsim=None):
    '''
    j index of pixe, which is being worked on
    
    Auxiliar function for use ts_est_APS()
    
    dsim, a deforamtion series of the current pixel j
    '''
    #
    # APS = np.zeros(phasedata.shape[1])
    #
    shift_1 = 0.
    shift_2 = 0.
    #
    aps_i = 0
    for i in range(zero_def_index_i.shape[0]):
        #
        if dsim is not None:
           shift_1 = dsim[zero_def_index_i[i,0]]
           shift_2 = dsim[zero_def_index_i[i,1]]
        #
        cdiff = (phasedata_j[zero_def_index_i[i,0]]-shift_1)  * \
                APSMatrix_i[zero_def_index_i[i,0],0] + \
                (phasedata_j[zero_def_index_i[i,1]]-shift_2)  * \
                APSMatrix_i[zero_def_index_i[i,1],0]
        #
        aps_i = aps_i + cdiff / 2
        #
    aps_i = aps_i / zero_def_index_i.shape[0]
        #
    #
    return aps_i
#
def ts_est_APSGreen(udates,dpath, dsim=None,max_time_lag=9999999,\
               eqt=None,dinfo_jd=None,sminimum=1,smaximum=10,isprint=False):
   '''
   Tymofyeyeva, Ekaterina and Fialko, Yuri (2015, JGR)
   an algorithm was proposed to estimate atmospheric components independently
   
   This is a faster version of ts_est_APS_j()
   
   updated by FWP @SYSU, 2020/03/09
   added two more keywords and remove sample_thres for two bounds...
   sminimum, 1
   smaximum, 10
   
   #
   '''
   addAPS = []
   addAPS_w = []
   apsM = []
   apsInd = []
   for i in range(udates.shape[0]):
      #
      APSMatrix = ts_dateINpairs_info(dpath,udates[i],dinfo_jd=dinfo_jd,\
                                      max_time_lag=max_time_lag)
      #
      index_i   = np.where(APSMatrix[:,0]!=0)[0]
      val_APS_Matrix_i = APSMatrix[index_i,:]
      diffs = np.unique(val_APS_Matrix_i[:,1])
      #
      outdata = []
      #
      for cdiff in diffs:
          sub_index_i = np.where(val_APS_Matrix_i[:,1]==cdiff)[0]
          if sub_index_i.shape[0] > 1 and \
             sum(APSMatrix[index_i[sub_index_i[0:2]],0])==0:
             #
             outdata.append(index_i[sub_index_i[0:2]])
          #
      #
      zero_def_index_i = np.array(outdata)
      
      #
      # if zero_def_index_i.shape[0] >= sample_thres:
      #
      if zero_def_index_i.shape[0] >= sminimum and \
         zero_def_index_i.shape[0] <= smaximum:
         #
          if isprint:
             print(" No%d date of %d with %d samples..."  % \
                                 (i,udates[i],zero_def_index_i.shape[0]))
          #
          if eqt is None:
             tmp_addAPS = np.zeros(udates.shape[0])
          else:
             tmp_addAPS = np.zeros(udates.shape[0]+1)
          # 
          tmp_addAPS[i] = 1
          addAPS.append(tmp_addAPS)
          addAPS_w.append(zero_def_index_i.shape[0])
          apsM.append(APSMatrix)
          apsInd.append(zero_def_index_i)
      #
   #
   addAPS = np.array(addAPS)
   add_W  = np.array(addAPS_w)
   add_W  = add_W / add_W.max() / 2
   #
   return addAPS, add_W, apsM, apsInd
#
# independent APS estimation
###############################################################################
#
def ts_est_APS_j(udates,dpath,phase_pixel_j, dsim=None,\
               eqt=None,dinfo_jd=None,sample_thres=3,isprint=False):
   '''
   Tymofyeyeva, Ekaterina and Fialko, Yuri (2015, JGR)
   an algorithm was proposed to estimate atmospheric components independently
   
   
   '''
   addAPS = []
   addD   = []
   addAPS_w = []
   for i in range(udates.shape[0]):
      #
      APSMatrix = ts_dateINpairs_info(dpath,udates[i])
      #
      index_i   = np.where(APSMatrix[:,0]!=0)[0]
      val_APS_Matrix_i = APSMatrix[index_i,:]
      diffs = np.unique(val_APS_Matrix_i[:,1])
      #
      outdata = []
      #
      for cdiff in diffs:
          sub_index_i = np.where(val_APS_Matrix_i[:,1]==cdiff)[0]
          if sub_index_i.shape[0] > 1 and \
             sum(APSMatrix[index_i[sub_index_i[0:2]],0])==0:
             #
             outdata.append(index_i[sub_index_i[0:2]])
          #
      #
      zero_def_index_i = np.array(outdata)
      # print("%d having %d" % (udates[i],zero_def_index_i.shape[0]))
      #
      if zero_def_index_i.shape[0] >= sample_thres:
          if isprint:
             print(" No%d date of %d with %d samples..."  % \
                                 (i,udates[i],zero_def_index_i.shape[0]))
          #
          if eqt is None:
             tmp_addAPS = np.zeros(udates.shape[0])
          else:
             tmp_addAPS = np.zeros(udates.shape[0]+1)
          #
          APS = ts_APS_j(APSMatrix,zero_def_index_i,\
                         phase_pixel_j,\
                         dsim=dsim)
          #
          #
          tmp_addAPS[i] = 1
          addAPS.append(tmp_addAPS)
          addD.append(APS)
          addAPS_w.append(zero_def_index_i.shape[0])
      #
   #
   addAPS = np.array(addAPS)
   addD   = np.array(addD)
   add_W  = np.array(addAPS_w)
   add_W  = add_W / add_W.max() / 5
   #
   return addAPS, addD, add_W
#
###############################################################################
#
def ts_infs2A(datainfo):
    '''
    David A. Schmidt and Roland Burgmann (2003,JGR)
    
    a method proposed by above study, for n acquistions, n-1 velocities can
    be solved. 
    
    '''
    udates = np.sort(np.unique(datainfo[:,1::]))
    v_time_matrix = np.zeros([udates.shape[0]-1,2])
    for i in range(udates.shape[0]-1):
        v_time_matrix[i,0] = udates[i]
        v_time_matrix[i,1] = udates[i+1]
    #
    A = np.zeros([datainfo.shape[0],v_time_matrix.shape[0]])
    #
    # coefficient for each velocity
    for i in range(A.shape[0]):
      A[i,:] = ts_coef4v(v_time_matrix,datainfo[i,1::])
    #
    lap = ts_laplacianV(v_time_matrix)
    #
    return A,lap,v_time_matrix
#
###############################################################################
def nw_dinfo2loop(dpath,dinfo,maxpairs=100000000):
    #
    # 
    # dinfo should have information of baseline, master and slave 
    # as extracted from .list file using ts.nw_read_datalist()
    # created by FWP, @SYSU, 2020/10/17
    #
    current_pair = dinfo[:,1:3]
    pmatrix = nw_dateinfo2loopind(current_pair)
    # print(pmatrix.shape)
    #
    syncoef = nw_plmatrix(current_pair,pmatrix)
    # print(syncoef.shape)
    #
    looplst = []
    for i in range(syncoef.shape[0]):
       index = np.where(syncoef[i,:]!=0)[0]
       if index.shape[0] == 3:
           looplst.append('%s,%s,%s : %d,%d,%d' % (dpath[index[0]],\
                                          dpath[index[1]],\
                                          dpath[index[2]],\
                                          syncoef[i,index[0]],\
                                          syncoef[i,index[1]],\
                                          syncoef[i,index[2]]))
    #
    return syncoef,looplst
#
def nw_list2loop(in_list,maxpairs=1000000):
    #
    dpath,dinfo = nw_read_datalist(in_list)
    syncoef, looplst = nw_dinfo2loop(dpath,dinfo,maxpairs=maxpairs)
    #
    return syncoef, dpath, looplst
#    
def nw_plmatrix(fullpairs,pMatrix):
    #
    A = np.zeros([pMatrix.shape[0],fullpairs.shape[0]])
    for ni in range(pMatrix.shape[0]):
       pair1 = fullpairs[pMatrix[ni,0],:]
       pair2 = fullpairs[pMatrix[ni,1],:]
       pair3 = fullpairs[pMatrix[ni,2],:]
       signs = nw_phaseloop_sign(pair1,pair2,pair3)
       A[ni,pMatrix[ni,0]] = signs[0]
       A[ni,pMatrix[ni,1]] = signs[1]
       A[ni,pMatrix[ni,2]] = signs[2]
    return A
 #
def pairinlist(datapath,pairinfo):
    #
    flag = False
    index = None
    for cindex,cfile in enumerate(datapath):
        #
        if pairinfo in cfile:
            flag = True
            index = cindex
    return flag,index
#
def dates2fullpairs(dates):
    #
    outdata = []
    for ni in range(len(dates)-1):
        #
        for nj in range(ni+1,len(dates)):
            outdata.append([dates[ni],dates[nj]])
        #
    return np.array(outdata)
#       
def pair_of_min_time_lag(in_list,outlist,outdir=None):
    #
    if outdir is not None:
       if not os.path.exists(outdir):
           os.makedirs(outdir)
    #
    dpath,dinfo = nw_read_datalist(in_list)
    dpath = np.array(dpath,dtype='str')
    dinfo = np.array(dinfo)
    dates = dinfo[:,1:3]
    dates = np.ravel(dates)
    udates = np.sort(np.unique(dates))
    #
    fid = open(outlist,'w')
    for ni in range(udates.shape[0]-1):
        master = udates[ni]
        slave  = udates[ni+1]
        flag1  = dinfo[:,1] == master
        flag2  = dinfo[:,2] == slave
        flag = flag1 & flag2
        #
        cpath = dpath[np.where(flag)]
        cinfo = dinfo[np.where(flag),:]
        cinfo = cinfo[0,0,:]
        if outdir is not None:
           newphs = os.path.join(outdir,os.path.basename(cpath[0]))
           if not os.path.exists(newphs):
              shutil.copy(cpath[0],newphs)
              shutil.copy(cpath[0]+'.rsc',newphs+'.rsc')
        else:
            newphs = cpath[0]
        fid.write('%s %f %f %f\n' % (newphs,cinfo[0],cinfo[1],cinfo[2]))
    #
    fid.close()
    return True
    #
def phsshiftres(in_file):
    data = []
    pairs = []
    with open(in_file,'r') as fid:
        for cline in fid:
            cline = cline.split('\n')[0]
            cline = cline.split()
            data.append(float(cline[1]))
            pairs.append(cline[0])
    return pairs,data
def phsshift_pairstr2pairnum(pair):
    #
    tmp = pair.split('_')
    return [int(tmp[0]),int(tmp[1])]
###############################################################################
def data2A(data):
    #
    # master   slave     los change (mm) in default
    #
    # yyyymmdd yyyymmdd los_dis
    #
    udates = np.ravel(data[:,0:2])
    udates = np.unique(udates)
    #
    A = np.zeros([data.shape[0]+1,udates.shape[0]])
    #
    for i in range(data.shape[0]):
        #
        index_m = np.where(udates == data[i,0])[0]
        index_s = np.where(udates == data[i,1])[0]
        #
        A[i,index_m[0]] = -1
        A[i,index_s[0]] = 1
        #
    #
    A[-1,0] = 1
    return A,udates
#
def dataSVD(data,A=None, udates=None):
    # 
    # solve an underdetermined linear issue
    #
    #
    data = data[~np.isnan(data[:,2]),:]
    #
    if A is None:
      A,udates = data2A(data)
    #
    D = np.hstack([data[:,2],0])
    #
    ndate = udates.shape[0]
    #
    los1,res1,rnk1,info1 = np.linalg.lstsq(A,D,rcond=None)
    #
    return los1,udates

def lsq_svd(A,D):
    '''
    This needs wide validation later...
    by Wanpeng Feng, @CCRS/NRCan, 2017-08-10
    
    '''
    # U,s,V = np.linalg.svd(A) # SVD decomposition of A
    U,s,Vh = sc.linalg.svd(A)
    #
    ss = np.pad(np.diag(1/s), ((0,0), (0, A.shape[0] - A.shape[1])), 'constant')
    #
    c = np.dot(U.T,D)
    w = np.dot(ss,c)
    xx = np.dot(Vh.conj().T,w)
    # dd,res1,rnk1,info1 = np.linalg.lstsq(A,D,rcond=None)
    return xx
###############################################################################
def phsshift2coefA(data):
    #
    pairs = phsshift2upairs(data)
    A = np.zeros([data.shape[0],pairs.shape[0]])
    #
    for ni in range(data.shape[0]):
        #
        cpairs = dates2pair(data[ni,0:3])
        sign   = nw_phaseloop_sign(phsshift_pairstr2pairnum(cpairs[0]),\
                                   phsshift_pairstr2pairnum(cpairs[1]),\
                                   phsshift_pairstr2pairnum(cpairs[2]))
        #
        A[ni,pairs == cpairs[0]] = sign[0]
        A[ni,pairs == cpairs[1]] = sign[1]
        A[ni,pairs == cpairs[2]] = sign[2]
    #
    return A
#
def phsshift2upairs(data):
    #
    pairs = []
    for ni in range(data.shape[0]):
        cpairs = dates2pair(data[ni,0:3])
        pairs.append(cpairs)
    #
    pairs = np.array(pairs,dtype='str')
    #
    return np.unique(pairs)
    
def dates2pair(dates):
    #
    dates = np.array(dates)
    dates = dates.astype(int)
    dates = np.sort(dates)
    return [str(dates[0])+'_'+str(dates[1]), \
            str(dates[0])+'_'+str(dates[2]),\
            str(dates[1])+'_'+str(dates[2])]
    #
def nextcoming(reftime,cycle,fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    '''
    cycle in days, 12 for sentinel-1
    '''
    nowjd = timestr2jd(datetime.datetime.now().strftime(fmt),fmt=fmt)
    #
    refjd = timestr2jd(reftime,fmt=fmt)
    flag = True
    counter = 0
    while flag:
        crefjd = refjd + counter * cycle
        if crefjd > nowjd:
            flag = False
        counter += 1
    expectancy = jd2timestr(crefjd,fmt=fmt)
    return expectancy
#
def phsshiftest(in_data):
    #
    data = np.loadtxt(in_data)
    #
    A = phsshift2coefA(data)
    D = data[:,3]
    # D = np.hstack((data[:,3],np.zeros(1)))
    x,res,rnks,s = np.linalg.lstsq(A,D,rcond=0.1)
    #
    return x,D,np.dot(A,x)
    
def yeardecimal2yyyymmdd(in_yr_decimal):
    #
    year = int(in_yr_decimal)
    rem  = in_yr_decimal - year
    base = datetime.datetime(year, 1, 1)
    result = base + datetime.timedelta(seconds=\
                    (base.replace(year=base.year + 1) - base).total_seconds() \
                    * rem - 12. * 60. * 60.)
    #
    return result.strftime('%Y%m%dT%H%M%S.%fZ')
# 
def yyyymmdd2fracyear(yyyymmdd,s=0):
    '''
    
    Parameters
    ----------
    yyyymmdd : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        return yyyy<dayOFyear>
        the result may be larger than we expected...
    '''
    dt = timestr2datetime(str(int(yyyymmdd)),fmt='%Y%m%d')
    dt = dt + datetime.timedelta(days=s)
    #
    return dt.strftime('%Y%j')
#
def yyyymmdd2dt(dates,ismid=False):
    #
    # as dates2dts, but with different names....
    #
    return dates2dts(dates,ismid=ismid)
#
#
def dates2dts(dates,ismid=False):
    #
    # copied from aps.py
    #
    # 
    dims = dates.shape
    outdates = np.array([datetime.datetime(int(str(dates[i])[0:4]),\
                                  int(str(dates[i])[4:6]),\
                                  int(str(dates[i])[6:8])) \
                                  for i in range(dims[0])])
    #
    if ismid:
        #
        coutdate = outdates[0:-1]
        for i in range(coutdate.shape[0]):
            #
            diffdays = outdates[i+1] - outdates[i]
            shift = int(diffdays.days/2)
            coutdate[i] = outdates[i]+datetime.timedelta(days=shift)
        #
        return coutdate
    return outdates
#
def yyyymmdd2jd(yyyymmdd,hhmmss='12:00:00',fmt='%Y%m%dT%H:%M:%S'):
    #
    return timestr2jd('%sT%s' % (str(int(yyyymmdd)),hhmmss),fmt=fmt)
    #
def mtimes2jd(times,fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    timesjd = [timestr2jd(ctime,fmt=fmt) for ctime in times]
    return np.array(timesjd)
#
#
def timestr2datetime(time_str,fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    return datetime.datetime.strptime(time_str,fmt)
#
def dt2timestr(cdatetime,fmt='%Y%m%dT%H:%M:%S.%f'):
    #
    # return a time (datetime format) in string
    # 
    return cdatetime.strftime(fmt)
#
# from year,month,day,hour,minute,second arrays to julian dates
# by Wanpeng Feng, @SYSU, 2018/12/29
def jdfromRSC(in_rsc):
    #
    info,ext = roipac.rsc(in_rsc)
    mtime = timestr2jd(info['MTIME'])
    stime = timestr2jd(info['STIME'])
    return mtime,stime
#
def yymmddhhMMsss2jd(yy,mm,dd,hh,MM,ss):
    # print(yy)
    dts = [datetime.datetime(year=int(yy[i]),month=int(mm[i]),\
                             day=int(dd[i]),hour=int(hh[i]),\
                             minute=int(MM[i]),second=int(ss[i])) \
           for i in range(yy.shape[0])]
    return [datetime2jd(dts[i]) for i in range(len(dts))]    
    #
def yymmdds2jd(yy,mm,dd):
    #
    # print(yy)
    #
    dts = [datetime.datetime(year=int(yy[i]),month=int(mm[i]),day=int(dd[i])) \
           for i in range(yy.shape[0])]
    return [datetime2jd(dts[i]) for i in range(len(dts))]
#
def timestr2jd(time_str,fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    #
    indatetime = datetime.datetime.strptime(time_str,fmt)
    return datetime2jd(indatetime)
###############################################################################
def time2jd_test(intime='2017-07-02T12:05:45.3533Z',\
                 fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    jd = timestr2jd(intime,fmt=fmt)
    retime = jd2timestr(jd,fmt=fmt)
    jd2 = timestr2jd(retime,fmt=fmt)
    print(" %s -> %f" % (intime,jd))
    print(" %s <- %f" % (retime,jd))
    print(" %s -> %f" % (retime,jd2))
    return True
#
def datetime2jd(fdate):
    #
    inyear  = fdate.year
    inmonth = fdate.month
    inday   = fdate.day
    in_fraction_day = jdutil.hmsm_to_days(hour=fdate.hour,\
                                               min=fdate.minute,\
                                               sec=fdate.second,\
                                               micro=fdate.microsecond)
    return jdutil.date_to_jd(inyear,inmonth,inday+in_fraction_day)
    #                    
#
def dayofyear2yyyymmdd(dayofyear,gmtsar=False):
    #
    in_date = str(int(dayofyear))
    if gmtsar:
        days = int(in_date[4:])+1
        in_date = in_date[0:4]+str(days)
    dt_info = datetime.datetime.strptime(in_date,"%Y%j")
    return dt_info.strftime('%Y%m%d')
def yyyymmdd2dayofyear(yyyymmdd):
    #
    in_date = str(int(yyyymmdd))
    dt_info = datetime.datetime.strptime(in_date,"%Y%m%d")
    # print(dt_info.year,dt_info.strftime('%j'))
    return '%s%s' % (str(dt_info.year),str(dt_info.strftime('%j')))
#
def yyyymmdd2yeardecimal(yyyymmdd):
    #
    in_date = str(int(yyyymmdd))
    dt_info = datetime.datetime.strptime(in_date,"%Y%m%d")
    return dt_info.year + float(dt_info.strftime('%j'))/365.
#
def jd2timestr(jd,fmt='%Y-%m-%dT%H:%M:%S.%f'):
    #
    return jdutil.jd_to_datetime(jd).strftime(fmt)
    
def jd2datetime(jd):
    return jdutil.jd_to_datetime(jd)
    
def dates2jd(in_date_str):
    
    '''
    in_date_str is a format like 20150101T023830
    
    '''
    # print(in_date_str)
    inyear = float(in_date_str[0:4])
    inmonth= float(in_date_str[4:6])
    inday  = float(in_date_str[6:8])
    in_fraction_day = float(in_date_str[9:11])/24.+\
                      float(in_date_str[11:13])/(60.*24.) + \
                      float(in_date_str[13:])/(60.*24.*60.)
    #
    return jdutil.date_to_jd(inyear,inmonth,inday+in_fraction_day)
    
###############################################################################    
def points2file(vec,outfile):
    #
    # dims = vec.shape
    # ncol = dims[1]
    # 
    np.savetxt(outfile,vec)
#################################################################
def checkevent(infile,eventdate):
    #
    """
      Check if input file covers the specific date
      the date should be in YYYYMMDD format...
    """
    master,slave = name2dateinfo(infile)
    #
    if master < eventdate and slave > eventdate:
       return True
    else:
       return False
###############################################################################  
def name2dateinfo(infile):
    """
       The file name of geocoded phase should be 
       in geo_<YYYYMMDD>_<YYYYMMDD>_T[TRACK].phs

    """
    file_names = infile.split('.')[0]
    master = file_names[4:12]
    slave  = file_names[13:21]
    #
    return int(master),int(slave)
    
###############################################################################
def nw_infs2udates(in_infs):
    '''
    time information of pairs with master,slave (date,e.g. YYYYMMDD)
    
    '''
    # return unique dates from a set of interferograms
    #
    in_infs = np.array(in_infs)
    in_infs = np.reshape(in_infs,in_infs.shape[0]*in_infs.shape[1])
    #
    return np.unique(in_infs)
    #
###############################################################################
def nw_read_gammabsinfo(gamma_info):
    #
    # <index> <Master> <slave> <perpendicular_bs> <vertical_bs> 
    #
    fid = open(gamma_info,'r')
    #
    dinfo = []
    for cline in fid:
        #
        cline = cline.split('\n')[0]
        tmp = cline.split()
        # datapath.append(tmp[0])
        dinfo.append([float(tmp[3]),float(tmp[1]),float(tmp[2])])
    #
    datainfo = np.array(dinfo)
    #
    return datainfo
    #
###############################################################################
def nw_read_gammalist(inlist):
    #
    datapath=[]
    dinfo = []
    fid = open(inlist,'r')
    for cline in fid:
        #
        cline = cline.split('\n')[0]
        tmp = cline.split()
        #datapath.append(tmp[0])
        dinfo.append([float(tmp[3]),float(tmp[1]),float(tmp[2])])
    #
    fid.close()
    datainfo = np.array(dinfo)
    #
    return datapath, datainfo
#
def nw_list2pair_jd(inlist,fmt='%Y-%m-%dT%H:%M:%S.%fZ',\
                    t1=19000101,t2=21000101):
    #
    # time information of pairs in julian time (float number with accuracy in second)
    # 
    dpath,datainfo = nw_read_datalist(inlist,t1=t1,t2=t2)
    dinfo_jd = np.copy(datainfo)
    #
    for i,cfile in enumerate(dpath):
        cinfo,cext = roipac.rsc_read(cfile+'.rsc')
        #
        # print(cinfo['MTIME'])
        mtime_jd = timestr2jd(cinfo['MTIME'],fmt=fmt)
        stime_jd = timestr2jd(cinfo['STIME'],fmt=fmt)
        #
        dinfo_jd[i,1] = mtime_jd
        dinfo_jd[i,2] = stime_jd
        #
    return dpath,datainfo,dinfo_jd
#
def nw_read_datalist(inlist,t1=19000101,t2=21000101):
    """
    
    t1,t2 two keywords to filter itnerferograms by a given period
    
    inlist is a list file recording all data in an ascii file
    format of each line is simple like:
    
    <fullpath_of_file> <baseline> <master date> <slave date>
    
    t1/t2 added by fWP, @SYSU,Guangzhou, 2020/02/11
          to filter interferograms within given time span.

    """
    datapath = []
    #
    fid = open(inlist,'r')
    #
    dinfo = []
    for cline in fid:
        #
        cline = cline.split('\n')[0]
        tmp = cline.split()
        #
        if len(tmp) == 4:
           ct1 = int(tmp[2])
           ct2 = int(tmp[3])
           #
           # note that we need an "and" below
           # other than a "&"
           #
           flag1 = ct1>=t1 and ct1 <= t2
           flag2 = ct2>=t1 and ct2 <= t2
           flag = flag1 and flag2
           # print(ct1,ct2,flag)
           #
           if flag:
              datapath.append(tmp[0])
              dinfo.append([float(tmp[1]),float(tmp[2]),float(tmp[3])])
    #
    fid.close()
    #
    # sorting data list in order
    # updated by FWP, @SYSU, Guangzhou, 2021/04/13
    datainfo = np.array(dinfo)
    datapath = np.array(datapath)
    indx = np.argsort(datapath)
    #
    #
    return datapath[indx], datainfo[indx,:]
###############################################################################
def nw_min_lag_check(udates,master,slave):
    #
    flag1 = udates > master
    flag2 = udates < slave
    flag  = np.logical_and(flag1,flag2)
    if sum(flag) > 0:
        return False
    else:
        return True
###############################################################################
def nw_list2mask(in_list,ext='.phs', mode='cc',cc=0.4,s=1,verb=True):
    #
    # build up a mask matrix for later analysis
    #
    dpath,dinfo = nw_read_datalist(in_list)
    if mode.upper() == 'CC':
        dpath = [cpath.replace(ext,'.cc') for cpath in dpath]
    #
    for i,cfile in enumerate(dpath):
        #
        if i == 0:
            mask = roipac.roi_read(dpath[i])[::s,::s]
            #
            mask[mask>=cc] = 1
            mask[mask<cc] = 0
        else:
            cmask = roipac.roi_read(dpath[i])[::s,::s]
            cmask[cmask>=cc] = 1
            cmask[cmask<cc] = 0
            mask = mask * cmask
        #
        nps = mask.shape[0] * mask.shape[1]
        index = np.where(mask==1)[0]
        #
        if verb:
           print(" Processing: %f valid pixels since %s" % (index.shape[0]/nps,cfile))
           if index.shape[0] == 0:
              return None
        #
        #
    # mask = mask / len(dpath)
    mask[np.isnan(mask)] = 0
    #
    return mask
    #
def nw_list2minlagpairs(in_list):
    #
    dpath,dinfo = nw_read_datalist(in_list)
    dpath       = np.array(dpath)
    #
    indMatrix,udate   = nw_dateinfo2uniquedate(dinfo[:,1:3])
    selinds = np.zeros(len(dpath),dtype=bool)
    #
    for ni in range(len(dpath)):
        #
        flag = nw_min_lag_check(udate,dinfo[ni,1],dinfo[ni,2])
        if flag:
            selinds[ni] = True
    #
    return dpath[selinds],dinfo[selinds,:]
###############################################################################
def nw_synsign(in_pair_1,in_pair_2,expected_pair):
    #
    # in_pair_1 = np.array(in_pair_1)
    # in_pair_2 = np.array(in_pair_2)
    # expected_pair = np.array(expected_pair)
    #
    master_sign = None
    slave_sign  = None
    ###########################################################################
    in_index_1 = np.array([1,1])
    in_index_2 = np.array([1,1])
    if in_pair_1[0] == expected_pair[0]:
        master_sign = in_index_1[0]
    if in_pair_1[1] == expected_pair[0]:
        master_sign = in_index_1[1] * -1
    #
    if in_pair_1[0] == expected_pair[1]:
        master_sign = in_index_1[0] * -1
    if in_pair_1[1] == expected_pair[1]:
        master_sign = in_index_1[1]
    # 
    # slave
    if in_pair_2[0] == expected_pair[0]:
        slave_sign = in_index_2[0]
    if in_pair_2[1] == expected_pair[0]:
        slave_sign = in_index_2[1] * -1
    if in_pair_2[0] == expected_pair[1]:
        slave_sign = in_index_2[0] * -1
    if in_pair_2[1] == expected_pair[1]:
        slave_sign = in_index_2[1]
    return [master_sign,slave_sign]
#
#############################################################################
def nw_locatepairsbydate(ref_pairs,in_date):
    # flag for locating the place 
    flag = np.copy(ref_pairs) * 0.
    flag[ref_pairs[:,0] == in_date,0] = 1
    flag[ref_pairs[:,1] == in_date,1] = 1
    # 
    # flag is N x 2 array 
    # 
    return flag[:,0] + flag[:,1], flag 
#
###############################################################################
def nw_pairindex(in_pairs,master,slave):
    #
    flag1,mflag = nw_locatepairsbydate(in_pairs,master)
    flag2,sflag = nw_locatepairsbydate(in_pairs,slave)
    flag = flag1 + flag2
    #
    if sum(flag==2) < 1:
        return None
    else:
        return np.where(flag==2)

#
###############################################################################
def new_fullpairs_mintimespan(ref_pair_dateinfo):
    '''
    dateinfo, an array from  nw_infs2newpair(ref_pairs,master,slave)
    '''
    timespans = np.zeros(ref_pair_dateinfo.shape[0])
    for i in range(ref_pair_dateinfo.shape[0]):
        df1 = diff2dates(str(int(ref_pair_dateinfo[i,0])), \
                         str(int(ref_pair_dateinfo[i,1])))
        df2 = diff2dates(str(int(ref_pair_dateinfo[i,2])),\
                         str(int(ref_pair_dateinfo[i,3])))
        timespans[i] = df1 + df2
    return timespans
                                                                   
# 
def nw_infs2newpair(ref_pairs,master,slave):
    #
    # return index of existing pairs for generating a new pair 
    # with master and slave
    #
    udates = nw_infs2udates(ref_pairs)
    #
    if len(np.logical_and(udates==master,udates==slave)) == 0:
        return False,np.array([None,None,None,None])
    else:
        #
        outindex = []
        outflag  = False
        flag1,flag_master = nw_locatepairsbydate(ref_pairs,master)
        flag2,flag_slave  = nw_locatepairsbydate(ref_pairs,slave)
        mpairs = ref_pairs[flag1>0,:]
        spairs = ref_pairs[flag2>0,:]
        #
        for inmaster in range(mpairs.shape[0]):
            #
            for inslave in range(spairs.shape[0]):
                
                cdates = np.array([mpairs[inmaster,0],mpairs[inmaster,1],\
                          spairs[inslave, 0],spairs[inslave,1]])
                #
                cudates = np.unique(cdates)
                flag_m  = sum(cdates == master)
                flag_s  = sum(cdates == slave)
                #
                if ( len(cudates) == 3 and flag_m == 1 and flag_s == 1 ):
                    #
                    outindex.append([mpairs[inmaster,0],mpairs[inmaster,1],\
                                     spairs[inslave, 0],spairs[inslave, 1]])
                    outflag = True
                #
        #
        return outflag, np.array(outindex)
        
#    
###############################################################################
#
def nw_syn2third(date1,date2):
    #
    # here, date1 and data2 are time information for pair1 and pair2
    # helpinformation was provided by Wanpeng Feng, @NRCan, 2017-02-17
    #
    if date1[0] == date2[0]:
       if date1[1] < date2[1]:
          sign = [-1,1]
       else:
          sign = [1,-1]
    else:
       if date1[0] > date2[0] and date1[1] == date2[1]:
          sign = [-1,1]
       elif date1[0] < date2[0] and date1[1] == date2[1]:
          sign = [1,-1]
       else:
          print(" ERROR: they have to have a common date")
          sign = [0,0]
    #
    return sign      
###############################################################################
def nw_phaseloop2weight(data):
    #
    data = np.sqrt(data ** 2)
    mean_data = np.mean(data[np.where(data!=0)])
    rdata = data / mean_data
    ind   = np.argsort(rdata[np.where(rdata!=0)])
    update_mean = np.mean(data[np.where(data!=0)][ind[0:int(ind.shape[0]/4)]])
    #print(mean_data,mean_data2)
    return data / update_mean
#################################################################
def nw_phaseloop_outname(pair1,pair2,pair3):
    #print(type(pair1))
    pair = []
    pair.append(pair1)
    pair.append(pair2)
    pair.append(pair3)
    pair = np.array(pair)
    pair = np.unique(pair)
    outname = str(int(pair[0])) + '-' + str(int(pair[1])) + '-' + str(int(pair[2])) 
    return outname
    
###############################################################################
def nw_udates2fullinfs(udates):
    #
    # return a full list of potential interferograms from SAR acquisitions
    # by Wanpeng Feng, @Ottawa, 2017-02-19
    #
    ndate    = len(udates)
    fullinfs = np.zeros([ ndate * (ndate - 1) / 2 ,2])
    counter  = 0
    for nk in range(len(udates)):
        for nj in range(len(udates)):
            master = dates2jd(str(int(udates[nk]))+"T010101")
            slave  = dates2jd(str(int(udates[nj]))+"T010101")
            #
            if master < slave:
                fullinfs[counter,:] = [udates[nk],udates[nj]]
                counter += 1
    #
    return fullinfs
#
###############################################################################
#
def nw_phaseloop_sign(pair1,pair2,pair3):
    #
    p1_m = pair1[0]
    p1_s = pair1[1]
    p2_m = pair2[0]
    p2_s = pair2[1]
    p3_m = pair3[0]
    p3_s = pair3[1]
    #
    signs = [1,1,1]
    if p1_m == p2_m:
       if p1_s > p2_s:
          signs[0] = -1
       else:
          signs[1] = -1
    #
    if p1_m == p3_m:
       if p1_s > p3_s:
          signs[0] = -1
       else:
          signs[2] = -1
    #
    if p2_m == p3_m:
       if p2_s > p3_s:
          signs[1] = -1
       else:
          signs[2] = -1
    #
    return signs
#################################################################
def sbas_invmatrix(indMatrix,baseinfo,dem=True,ndate=10,\
                   wavelength=5.54,r=693000,inc=32):
    #
    #
    ninf = indMatrix.shape[0] 
    A    = np.zeros([ninf+1,ndate])
    for ni in np.arange(ninf):
        A[ni,indMatrix[ni,0]] = -1
        A[ni,indMatrix[ni,1]] =  1
    #
    if dem:
       ba = 4 * np.pi * baseinfo / (wavelength * r * np.sin(inc/180.*np.pi))  
       MA = np.zeros([ninf+1,ndate+1])
       MA[:,0:-1] = A
       MA[0:-1,-1] = ba
       A = MA
       # A = np.concatenate((A,ba),axis=1)
    #
    A[ninf,0] = 1 
    return A

#################################################################
def nw_read_uniquedate(inlist):
    #
    datapath,datainfo = nw_read_datalist(inlist)
    #
    indMatrix,udate   = nw_dateinfo2uniquedate(datainfo[:,1:3])
    #
    return indMatrix, udate
#################################################################
def nw_dateinfo2uniquedate(datas):
    #
    # master and slave time mastrix to unique dates
    #
    dims = datas.shape
    dates= datas.reshape([dims[0]*dims[1],1])
    udate= np.unique(dates).astype(int)
    indMatrix = datas.astype(int) * 0
    #
    for cind in range(dims[0]):
        ind1 = np.where(udate==datas[cind,0])[0]
        ind2 = np.where(udate==datas[cind,1])[0] 
        # print(cind,ind1,ind2)
        indMatrix[cind,:] = [ind1[0],ind2[0]] 
    #
    return indMatrix, udate
################################################################
def nw_checkpair2(inpair,indMatrix):
    flag1 = indMatrix[:,0] == inpair[0]
    flag2 = indMatrix[:,1] == inpair[1]
    #
    flag = np.logical_and(flag1,flag2)
    #
    index = np.where(flag==True)[0]
    if len(index)==0:
        return -1
    else:
        return index[0]
def nw_checkpair(inpair,indMatrix):
    #
    outind = -1
    dims = indMatrix.shape
    for cind in range(dims[0]):
        mid = indMatrix[cind,0]
        sid = indMatrix[cind,1]
        if mid == inpair[0] and sid == inpair[1]:
           outind = cind
           break
    #
    return outind
#
###############################################################################
#
def nw_refinephase(loopG,phs,rho=1.0):
    #
    loopres = np.dot(loopG,phs)
    # 
    # just keep the integer part
    #
    # loopres = np.round(loopres/(np.pi*2))
    #
    w0 = np.abs(loopres)
    w0[w0<np.mean(w0)] = 1;
    w0[w0!=1] = 0.01
    dw = np.zeros(loopG.shape[1])
    for i in range(loopG.shape[1]):
        #
        index = np.where(loopG[:,i]!=0)[0]
        dw[i] = np.sum(w0[index])
    #
    #
    # print(dw.shape,loopG.shape)
    index = np.where(np.abs(loopres)<rho)[0]
    #
    cA = np.diag(np.ones(phs.shape[0]))
    #
    loopD = np.copy(loopG[:,0])*0.
    #
    loopw = loopD + np.max(dw)-0.5
    #
    D = np.concatenate([phs, loopD])
    W = np.concatenate([dw,loopw])
    #
    # plt.plot(W,'or')
    #  plt.show()
    #
    A = np.vstack([cA,loopG])
    cphs,_,_ = ts_ls(A,D,W=np.diag(W),istheilsen=False)
    #
    return cphs,dw
#
def nw_dateinfo2loopind2(indMatrix):
    # only for test 
    # it has been evidenced that slower than nw_dateinfo2loopind
    # by FWP, @SYSU, Guangzhou, 2021/06/11
    #
    dims    = indMatrix.shape
    # allind  = indMatrix.reshape([dims[0]*dims[1],1]);
    # uinds   = np.unique(allind).astype(int)
    # ndate   = uinds.shape
    #
    outids = []
    for i in range(dims[0]-2):
        for j in range(i+1,dims[0]-1):
            for k in range(j+1,dims[0]):
                cdates = np.unique(indMatrix[[i,j,k],0:2].ravel())
                if cdates.shape[0]==3:
                   flag = (indMatrix[i,0] - indMatrix[i,1]) -\
                          (indMatrix[j,0] - indMatrix[j,1]) + \
                          (indMatrix[k,0] - indMatrix[k,1])
                   # cdates = np.unique(indMatrix[[i,j,k],0:2].ravel())
                   if flag == 0 and cdates.shape[0] == 3:
                      # print(i,j,k,cdates.shape)
                      outids.append([i,j,k])
                #
    #
    idsArr = np.array(outids)
    loopG = np.zeros([idsArr.shape[0],dims[0]])
    for i in range(idsArr.shape[0]):
        #
        loopG[i,idsArr[i,:]] = [1, -1, 1]
    return idsArr,loopG
    #
def nw_dateinfo2loopind(indMatrix):
    # 
    # indMatrix, a matrix having dates of master and slave SARs
    # 
    dims    = indMatrix.shape
    allind  = indMatrix.reshape([dims[0]*dims[1],1]);
    uinds   = np.unique(allind).astype(int)
    ndate   = uinds.shape
    #
    counter = 0
    #
    outloopid = []
    for mind in range(ndate[0]-2):
        #
        for sind_index in range(mind+1,ndate[0]-1):
            for tind_index in range(sind_index+1,ndate[0]):
                #
                pair1 = [uinds[mind],uinds[sind_index]]
                pair2 = [uinds[mind],uinds[tind_index]]
                pair3 = [uinds[sind_index],uinds[tind_index]]
                #
                outind1 = nw_checkpair2(pair1,indMatrix)
                outind2 = nw_checkpair2(pair2,indMatrix)
                outind3 = nw_checkpair2(pair3,indMatrix)
                #
                if outind1 > -1 and outind2 > -1 and outind3 > -1:
                   counter += 1
                   if counter == 1: 
                      outloopid = np.unique(\
                            np.array([outind1,outind2,outind3])).reshape((1,3))
                   else:
                      outloopid = np.concatenate((outloopid,\
                            np.unique(np.array([outind1,outind2,\
                                                outind3])).reshape(1,3)))
    #
    # ndims = outloopid.shape
    # 
    return outloopid
#################################################################
def demcorrelatedsign_removal(phs,mlon,mlat,dem,maskphs=None,x0=[1.,1.,1.],\
                              maxfev=1000000,iterations=1,scale=1):
    #
    if maskphs is None:
       maskphs = np.copy(phs)
    #
    subphs  = maskphs[::scale,::scale]
    subdem  = dem[::scale,::scale]
    sublon  = mlon[::scale,::scale]
    sublat  = mlat[::scale,::scale]
    #
    #
    for ni in range(iterations):
      #
      demvec = subdem[np.where(subphs!=0)]
      phsvec = subphs[np.where(subphs!=0)]
      phsvec = phsvec[np.where(demvec>0)]
      demvec = demvec[np.where(demvec>0)]
      indem,inphs = opt.powlaw_sortdata(demvec,phsvec)
      coef,res    = opt.est_powlawcoef(indem,inphs,opt.powlaw_errfun_1,x0,maxfev=maxfev)
      simphs      = opt.powlaw_fitfun_1(coef,subdem,iskeepcons=True)
      tmpphs      = subphs - simphs
      tmpphs[subphs==0] = 0
      #
      print(" NO %d: %f %f %f" % (ni,coef[0],coef[1],coef[2]))
      corphs,simph= orbitalCor(tmpphs,sublon,sublat)
      #
      tmphs      = subphs - simph
      tmphs[subphs==0] = 0
      subphs     = np.copy(tmphs)
      #
      x0          = coef
    # 
    demphs      = opt.powlaw_fitfun_1(coef,dem,iskeepcons=False)
    masksub     = maskphs - demphs
    masksub[maskphs==0] = 0
    corphs,orbphs  = orbitalCor(masksub,mlon,mlat)
    #orbphs = np.zeros(demphs.shape)
    outphs         = phs - demphs - orbphs
    outphs[phs==0] = 0
    
    #
    return outphs,demphs,orbphs,coef
###############################################################################
def ts_ls_np(A,d):
    #
    coef = np.linalg.solve(A,d)
    return coef,0,0
#
def ts_ls_lsmr(A,d):
    #
    x, istop, itn, normr = lsmr(A,d)[:4]
    return x,itn,normr
def ts_ls_cg(A,d):
    #
    coef,info = cg(A,d)
    return coef,info,1
# 
def ts_ls(A,d,istheilsen=True,W=None,rcond=0.000000000000001,\
          minv=-10000,maxv=10000,method='bvls',max_iter=None):
   #  
   # method, bvls  or trf
   if W is not None:
     Aw = np.dot(W,A)
     Dw = np.dot(d,W)
   else:
     Aw = A
     Dw = d
   #
   # cof, res, nrnk, s = sc.linalg.lstsq(Aw,Dw)
   # updated by FWP, @SYSU,Guanghzou, 2020/02/06
   # below solution is certainly better than lstsq
   #
   lb = np.zeros(Aw.shape[1]) +minv
   ub = np.copy(lb) * 0 + maxv
   #
   if max_iter is None:
       max_iter = Aw.shape[1]*100
   #
   # lsmr_tol, None or auto
   lsmr_tol = None
   lsq_solver = 'lsmr'
   if method.upper() == 'BVLS':
       lsq_solver='exact'
   #
   res = sc.optimize.lsq_linear(Aw,Dw, bounds=(lb,ub), \
                                max_iter=max_iter,\
                                tol=rcond, method=method,\
                                lsmr_tol=lsmr_tol, lsq_solver=lsq_solver,\
                                verbose=0)
   cof = res.x
   res = res.cost
   nrnk = len(cof)
   #
   if istheilsen:
     #
     simD = np.dot(A,cof)
     resD = np.abs(d-simD)
     # median of residuals
     resM = np.median(resD)
     #resThres = resM + (resM - np.min(resD))
     cA = A[resD<=resM,:]
     tD = d[resD<=resM]
     # tcof, tres, tnrnk, ts = sc.linalg.lstsq(cA,tD)
     res = sc.optimize.lsq_linear(Aw,Dw, bounds=(lb,ub), \
                                 method='bvls', verbose=1)
     tcof = res.x
     tnrnk = len(cof)
     # 
     tres = np.std(tD-np.dot(cA,tcof))
     if not isinstance(tres,np.ndarray):
         res = tres
         cof = tcof
         nrnk = tnrnk
   #  
   return cof,res,nrnk
###############################################################################
#
def deramp(phs,npara=1,istheilsen=True,scale=4,iters=3):
    #
    X,Y = np.meshgrid(np.r_[0:phs.shape[1]],np.r_[0:phs.shape[0]])
    #
    for i in range(iters):
       phs,corsim = orbitalCor(phs,X,Y,dem='NULL',thirddep='NULL',\
               istheilsen=istheilsen,scale=scale,npara=npara)
    return phs,corsim
#    
#
###############################################################################
#
def orbitalCor(phs,mlon,mlat,dem='NULL',thirddep='NULL',\
               istheilsen=True,scale=1,npara=3,\
               cc=None,demexp=False,cof_only=False):
    '''
    Make sure dem is an float array if it is given...
    print(phs.shape,mlon.shape,mlat.shape,dem.shape)
    ======
    istheilsen is provided by Wanpeng Feng, @NRCan, 2017-03-01
    This is working for excluding outliers in the linear inversion based on a
    Thei-Sen algorithm, in which a median calculation is used to mask data for 
    a recalculation.
    '''
    #
    if istheilsen:
      print(" pSAR.ts: deramping with a setting for theilsen ")
    #
    phs[np.isnan(phs)] = 0
    #
    cphs  = phs[::scale,::scale]
    cmlon = mlon[::scale,::scale]
    cmlat = mlat[::scale,::scale]
    if cc is not None:
        ccc = cc[::scale,::scale]
    #
    #
    if not isinstance(dem,str):
       #
       cdem = dem[::scale,::scale]
       #
       cdem[np.isnan(cdem)] = 0
       maxdem = np.max(np.abs(cdem))
       if demexp:
           dempart = np.exp(8. * cdem/maxdem)
       else:
           dempart = cdem/maxdem
       
       # maxdem = 1.
    else: 
       cdem = np.array([])
    #
    if not isinstance(thirddep,str):
       cthirddep = thirddep[::scale,::scale]
    else:
       cthirddep = np.array([])
    #
    cmlon = cmlon[cphs != 0]
    cmlat = cmlat[cphs != 0]
    maxlon = np.max(cmlon**2)
    maxlat = np.max(cmlat**2)
    maxlonlat = np.max(cmlon*cmlat)
    #
    # Allow to build up a weighted least-square
    #
    if cc is not None:
       ccc   = ccc[cphs != 0 ]
       W = np.diag(ccc)
    else:
       W = None
    #
    # extract dem value if not zero
    #
    if len(cdem)>0:
       cdem = cdem[cphs != 0]
       dempart = dempart[cphs !=0 ]
    if len(cthirddep)>0:
       cthirddep = cthirddep[cphs != 0]
    #
    cphs = cphs[cphs != 0]
    cons = cphs * 0 + 1.
    #
    # create A matrix for orbital error correction
    #
    if npara == 3:
       if len(cdem) == 0:
          # print( " Processes: Generating A without DEM...")
          A = np.array([cons,cmlon,cmlat])
       else:
          #
          if len(cthirddep) == 0:
             # print( " Processes: Generating A with a given DEM (MAXD: %d)..." % maxdem)
             A = np.array([cons,cmlon,cmlat,dempart])
          else:
             A = np.array([cons,cmlon,cmlat,dempart,cthirddep])
          #
    elif npara == 4:
       lonlatm = cmlon * cmlat
       if len(cdem) == 0:
          A = np.array([cons,cmlon,cmlat,lonlatm/maxlonlat])
       else:
          if len(cthirddep) == 0:
             A = np.array([cons,cmlon,cmlat,lonlatm/maxlonlat,dempart])
          else:
             A = np.array([cons,cmlon,cmlat,lonlatm/maxlonlat,dempart,cthirddep])
    elif npara == 6:
        lonlatm = cmlon * cmlat
        #
        if len(cdem) == 0:
           A = np.array([cons,cmlon,cmlat,lonlatm/maxlonlat,cmlon**2/maxlon,cmlat**2/maxlat])
        else:
           A = np.array([cons,cmlon,cmlat,lonlatm/maxlonlat,cmlon**2/maxlon,cmlat**2/maxlat,dempart])
    elif npara == 1:
        if len(cdem) == 0:
            A = np.array([cons,cmlon])
        else:
            A = np.array([cons,cmlon,dempart])
    elif npara == 0:
        if len(cdem) == 0:
            A = np.array([cons])
        else:
            A = np.array([cons,dempart])
    #
    # solve a large linear problem with numpy least square method
    #
    A = A.T
    #
    if A.shape[0] < 10:
        print(" pSAR.ts: Failed due to too limited samples (%d)" % A.shape[0])
        return None
    #
    cof,res,nrnk = ts_ls(A,cphs,istheilsen=istheilsen,W=W)
    #
    if cof_only:
        return cof
    #
    #
    # cof,res = sbas_lsq(A,cphs,iterations=1)
    #
    # print(A.shape,res,cof)
    if isinstance(res, np.ndarray):
        print(" pSAR.ts: Warning!!! None was returned.")
        res = np.array([np.nan])
    #
    if not isinstance(res, np.float64):
        res = np.min(res)
    # 
    print(" RES: %f with %d parameters" % (res,npara))
    #
    if npara == 3: 
       #
       sim = cof[0] + mlon * cof[1] + mlat * cof[2] 
       #ramp = cof[0] + mlon * cof[1] + mlat * cof[2]
       nodem = 3
    elif npara == 4:
       sim = cof[0] + mlon * cof[1] + mlat * cof[2] + \
                      mlon * mlat * cof[3] / maxlonlat
       #ramp = cof[0] + mlon * cof[1] + mlat * cof[2]
       nodem = 4
    elif npara == 6:
       sim = cof[0] + mlon * cof[1] + mlat * cof[2] + \
                      mlon * mlat * cof[3] / maxlonlat +\
                      mlon**2 /maxlon * cof[4] + mlat ** 2 / maxlat * cof[5]
       #ramp = cof[0] + mlon * cof[1] + mlat * cof[2]               
       nodem = 6
    elif npara == 1:
        sim = cof[0] + mlon * cof[1]
        #ramp = cof[0] + mlon * cof[1]
        nodem = 2
    elif npara == 0:
        sim = cof[0]
        #ramp = phs * 0. + cof[0]
        nodem = 1
    #
    demsim = 0
    thirdsim = 0
    if len(cdem) > 0:
       #
       print(" Processes: Simulating DEM contributions with maxdem %f" % maxdem)
       if demexp:
           demsim = cof[nodem] * np.exp(dem/maxdem)
       else:
            demsim = dem * cof[nodem] / maxdem
       nodem = nodem + 1
    #
    if len(cthirddep)>0:
       thirdsim = thirddep * cof[nodem]
    #
    sim = sim + demsim + thirdsim
    #
    corphs = phs - sim
    corphs[phs==0] = 0.
    #
    return corphs,sim
#
###############################################################################
def sincenow(intime,utc=True,fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    #
    # intime should be in format of '%Y-%m-%dT%H:%M:%S.%fz
    # like 2018-01-12T23:32:35.383010Z
    #
    if utc:
       nowtime = datetime.datetime.utcnow()
    else: 
       nowtime = datetime.datetime.now()
    # Tnow    = datetime.datetime.strftime(nowtime,'%Y-%m-%dT%H:%M:%S.%fZ')
    intime = timestr2datetime(intime,fmt=fmt)
    difftime = intime - nowtime
    return difftime.total_seconds()

def today():
    return datetime.datetime.now()
#
def sincetoday(indate):
    #
    nowtime = today()
    now_date = datetime.datetime.strftime(nowtime,'%Y%m%d') 
    return diff2dates(now_date,str(indate))
#
def dates2dates(dates):
    '''
    To convert "YYYYMMDD" to datetime format
    '''
    dims = dates.shape
    #
    outdates = np.array([datetime.datetime(int(str(dates[i])[0:4]),\
                                  int(str(dates[i])[4:6]),\
                                  int(str(dates[i])[6:8])) \
                                  for i in range(dims[0])])
    return outdates
#
###############################################################################
#
def sar_predictACQ(refdate,eventdate,cycle):
    #
    diffdays = diff2dates(str(refdate),str(eventdate))
    ncycle   = np.ceil(diffdays / cycle)
    return newdate(refdate,ncycle*cycle)
#    
###############################################################################
def allmonths(dt1,dt2,fmt='%Y%m%d'):
    # 
    # return all months between two dates
    # by Wanpeng Feng, @SYSU, Guangzhou, 2019/05/08
    #
    if fmt.upper() == 'DT':
        sd = dt1;
        ed = dt2;
    else:
        sd = datetime.datetime.strptime(dt1, fmt) 
        ed = datetime.datetime.strptime(dt2, fmt) 
    #
    lst = [datetime.datetime.strptime('%2.2d-%2.2d' % (y, m),\
          '%Y-%m').strftime('%m-%Y') \
          for y in range(sd.year, ed.year+1) \
             for m in range(sd.month if y==sd.year else 1, \
                           ed.month+1 if y == ed.year else 13)]

    return lst
#
def time2yyyymmdd(mtime,fmt="%Y-%m-%dT%H:%M:%S.%fZ"):
    dt = datetime.datetime.strptime(mtime,fmt)
    return dt.strftime('%Y%m%d')
def timeshift(mtime,shiftdays,fmt="%Y-%m-%dT%H:%M:%S.%fZ",outfmt=None):
    """
    

    Parameters
    ----------
    mydt : TYPE
        DESCRIPTION.
    shiftdays : TYPE
        DESCRIPTION.
    fmt : TYPE, optional
        DESCRIPTION. The default is "".

    Returns
    -------
    None.

    """
    if outfmt is None:
        outfmt = fmt
    #
    mdt = datetime.datetime.strptime(mtime,fmt)
    mdt = mdt + datetime.timedelta(days=shiftdays)
    #
    #
    #
    return datetime.datetime.strftime(mdt,outfmt)
def newdate(indate,shiftdays,fmt='%Y%m%d'):
    #
    # return a new data by given a shift of few days...
    # for example "20150101" 
    #     with a shift 0f  1 can reach "20150102"
    #     with a shift of -1 can reach "20141231"
    # change output as a string
    #
    indate = str(int(indate))
    my = int(indate[0:4])
    mm = int(indate[4:6])
    md = int(indate[6:8]) 
    dform = datetime.datetime(my,mm,md)
    newd  = dform + datetime.timedelta(days=shiftdays)
    return newd.strftime(fmt)
#    
###############################################################################
#
def cloestdate(datematrix,refdate):
    #
    diffs = mdiffdates(datematrix,refdate)
    absdiffs = np.abs(diffs)
    return np.where(absdiffs==np.min(absdiffs))[0][0]
#
###############################################################################
#
def mdiffdates(datematrix,refdate):
    #
    diffs = np.copy(datematrix).astype(np.float64) * 0
    for ni in range(datematrix.shape[0]):
        #
        diffs[ni] =  diff2dates(str(int(datematrix[ni])),str(int(refdate)))
    #
    return diffs    
#             
def day_of_year(mdate):
    my = int(mdate[0:4])
    mm = int(mdate[4:6])
    md = int(mdate[6:8])
    cdatetime = datetime.datetime(my,mm,md)
    return cdatetime.timetuple().tm_yday
#
def diff2times(t1,t2,fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    #
    #
    dt1 = timestr2datetime(t1,fmt=fmt)
    dt2 = timestr2datetime(t2,fmt=fmt)
    difdays = dt2 - dt1
    #
    return difdays.days
def diff2dates(mdate,sdate):
    #
    # mdate and sdate are both in string format...
    # like '20150101'
    #
    my = int(mdate[0:4])
    mm = int(mdate[4:6])
    md = int(mdate[6:8])
    sy = int(sdate[0:4])
    sm = int(sdate[4:6])
    sd = int(sdate[6:8])
    # print(my,mm,md)
    # print(sy,sm,sd)
    d1 = datetime.datetime(my,mm,md)
    d2 = datetime.datetime(sy,sm,sd)
    dd = d2 - d1
    return dd.days
#################################################################
def tinfo2uniquedate(infpairs):
    #
    tinfo = infpairs.ravel()
    dates = np.unique(tinfo)
    return dates
#################################################################
def nw_coefA(loopmatrix,pairInfo,weights):
    #
    maxweig = np.max(weights)
    #
    nloops  = loopmatrix.shape[0]
    A1      = np.zeros([nloops, pairInfo.shape[0]])
    A2      = np.zeros([pairInfo.shape[0],pairInfo.shape[0]])
    #
    for ni in range(nloops):
       sign = nw_phaseloop_sign(pairInfo[loopmatrix[ni,0],:],\
                                pairInfo[loopmatrix[ni,1],:],\
                                pairInfo[loopmatrix[ni,2],:])
       A1[ni,loopmatrix[ni,0]] = sign[0]
       A1[ni,loopmatrix[ni,1]] = sign[1]
       A1[ni,loopmatrix[ni,2]] = sign[2] 
    #
    A1 = A1 * maxweig
    #
    for ni in range(pairInfo.shape[0]):
       A2[ni,ni] = 1 * weights[ni]
    #
    A = np.concatenate((A1,A2),axis=0)
    #
    return A,A1,A2
#################################################################
#
def tinfo2datematrix(infpairs):
    #
    # infpairs is an array saving time information of master and 
    # slave for each interferogram
    #
    dates  = tinfo2uniquedate(infpairs)
    npair  = infpairs.shape[0]
    ndate  = dates.shape[0]
    tinfomatrix = np.zeros((npair,ndate))
    for pair_ind in range(0,npair):
        for date_ind in range(0,ndate):
            #
            m_ind = np.where(dates == infpairs[pair_ind,0])
            s_ind = np.where(dates == infpairs[pair_ind,1])
            tinfomatrix[pair_ind,m_ind] = 1
            tinfomatrix[pair_ind,s_ind] = -1
    #
    return tinfomatrix
   
##################################################################
def nw_phscor_lsq(A1,A2,D1,D2,weigs,iterations=5):
    #
    ci  = 0
    WA2 = np.copy(A2)
    WD2 = np.copy(D2)
    for ni in range(weigs.shape[0]):
        WA2[ni,:] = WA2[ni,:] * weigs[ni]
    #
    WD2 = WD2 * weigs
    D = np.concatenate((D1,WD2))
    #
    A = np.concatenate((A1*np.max(weigs),WA2))
    #
    while ci < iterations:
       #
       corphs,res,rnk,s = np.linalg.lstsq(A,D)
       simD = np.dot(A2,corphs)
       resD = np.abs(D2 - simD)
       index = np.where(resD == np.max(resD))
       D2[index] = simD[index]
       WD2 = np.copy(D2)
       WD2 = WD2 * weigs
       D = np.concatenate((D1,WD2))
       # print(" NO: %d with RES: %f " %(ci,res))
       ci += 1
    #
    return corphs
##################################################################
def sbas_lsq(A,D,iterations=3,percent=0.99):
    #
    # iterative linear least-square method  
    # 
    cversion = platform.python_version()
    minor_num = int(cversion.split('.')[1])
    if minor_num < 6:
        rcond = -1
    else:
        rcond = None
    ci = 0
    while ci < iterations:
       #
       bperp,res,rnk,s = np.linalg.lstsq(A,D,rcond=rcond)
       simD = np.dot(A,bperp)
       resD = np.abs(D - simD)
       #
       D[np.where(resD>=np.max(resD)*percent)] = \
                        simD[np.where(resD>=np.max(resD)*percent)]
       #
       ci += 1
    #
    # print(resD)
    #
    return bperp,res
#
###############################################################################
#
def tinfo2baseline(infpairs,baseline,refindex=1):
    '''
     Calculate approximate baseline for each aquisition....
     infopairs, e.g. [[<master>,<slave>],[<master>,<slave>]]
    '''
    tinfomatrix = tinfo2datematrix(infpairs)
    #
    presetbase  = tinfomatrix[0,:] * 0
    presetbase[refindex-1] = 1
    zerobase   = np.zeros(1) 
    #
    # Create coefficient matrix 
    A = np.concatenate((tinfomatrix,[presetbase]),axis=0)
    D = np.concatenate((baseline,zerobase),axis=0)
    # bperp,res,rnk,s = np.linalg.lstsq(A,D) 
    bperp,res = sbas_lsq(A,D,iterations=5)
    #
    return bperp
###############################################################################
#
def lls2dist(p1,p2):
    '''
    This was transitioned from pDATA to pSAR.ts.py by Wanpeng Feng, @CCRS/NRCan
    , 2017-07-15
    
    To calculate the distance between two points
    return the distance in kml between two points (p1,p2)
    
    '''
    #
    x1,y1,zone,zonel = utm_conversion.from_latlon(p1[1],p1[0])
    x2,y2,zone,zonel = utm_conversion.from_latlon(p2[1],p2[0],\
                                        force_zone_number=zone,\
                                        force_zone_letter=zonel)
    dist  = np.hypot(x1-x2,y1-y2)
    dist  = dist / 1000
    #
    return dist
###############################################################################
#
def baselineinfo2master(dinfo,Tc=1000,Bc=2000):
    #
    outdata = []
    for i in range(dinfo.shape[0]):
        mb = 0
        md = 0
        counter = 0
        for j in range(dinfo.shape[0]):
            if dinfo[j,2]!=dinfo[i,2]:
                cbase = abs(dinfo[i,0]-dinfo[j,0])
                ddays = abs(diff2dates(str(dinfo[i,2]),str(dinfo[j,2])))
                if ddays > Tc:
                    ddays = ddays * 10
                if cbase > Bc:
                    cbase = cbase * 10
                #
                mb = mb + cbase
                md = md + ddays
                counter = counter + 1
            #
        #
        if mb > 0 and md > 0:
           outdata.append([dinfo[i,2],mb,md,counter])
    #
    outdata = np.array(outdata)
    if outdata.shape[0]>0:
      d1 = outdata[:,1] /outdata[:,3]
      d2 = outdata[:,2] /outdata[:,3]
      logvalue = np.log(d1/np.median(d1)+d2/np.median(d2))    
      index = np.where(logvalue==logvalue.min())[0][0]
      return outdata, int(outdata[index,0])
    else:
      index = None
      return outdata, None 

###############################################################################
#
def optimalmaster(pair_dates,baseline,Tc=10000.,Bc=20000.):
    #
    # Tc a critical Timperal baseline,   days
    # Bc a critical Spatial baseline,    meters
    #
    # return unique dates from a series of InSAR pairs
    #
    udates = tinfo2uniquedate(pair_dates)
    #
    refindex = 1
    #
    pberp    = tinfo2baseline(pair_dates,baseline,refindex=refindex)
    #
    tinfo    = udates * 0
    binfo    = udates * 0
    dims     = udates.shape
    optimalVal = tinfo * 0
    Tc         = float(Tc)
    Bc         = float(Bc)
    #
    for index in range(0,dims[0]):
        #
        tmptime = tinfo * 0
        tmpbase = tinfo * 0
        tmpopts = tinfo * 0
        #
        for cindex in range(0,dims[0]):
            # print(np.absolute(diff2dates(str(udates[cindex]), 
            # str(udates[index]))) / Tc)
            tmptime[cindex] = 1. - np.absolute(diff2dates(str(udates[cindex]),\
                              str(udates[index]))) / Tc
            tmpbase[cindex] = 1. - \
                              np.absolute(pberp[cindex] - pberp[index]) / Bc
            tmpopts[cindex] = tmptime[cindex] * tmpbase[cindex]
        #
        # print(tmptime)
        #
        tinfo[index]      = scipy.stats.gmean(tmptime[np.where(tmptime>0)]) 
        binfo[index]      = scipy.stats.gmean(tmpbase[np.where(tmpbase>0)])
        optimalVal[index] = scipy.stats.gmean(tmpopts[np.where(tmpopts>0)])
    #
    master = udates[np.where(optimalVal==np.max(optimalVal))]
    #
    return master,tinfo,binfo,optimalVal,udates
