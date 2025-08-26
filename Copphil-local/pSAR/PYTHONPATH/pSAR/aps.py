#!/usr/bin/env python
#
#
import pSAR
import scipy.linalg.lapack as lapack
import scipy.linalg as la
import datetime 
import sys
import os
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('agg')
#
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
##
def sortdates(apsdates,refdate=None):
    #
    if refdate is None:
        refdate = apsdates[0]
    #
    return np.array([diff2dates(apsdates[0],apsdates[i]) for i in range(apsdates.shape[0])])
#
def phsdata2freq(data):
    #
    info,udates = phsdata2info(data)
    freq_data = np.zeros([udates.shape[0],2])
    #
    for i in range(udates.shape[0]):
        #
        ind1 = np.where(info[:,0]==udates[i])[0]
        ind2 = np.where(info[:,1]==udates[i])[0]
        freq_data[i,:] = [udates[i],ind1.shape[0]+ind2.shape[0]]
    #
    return freq_data
#
def phsdata2info(data,mode=0):
    # mode,0 for full dates
    #      1 for index
    #
    udates = np.sort(np.unique(data[:,0:2]))
    info = np.zeros([data.shape[0],3])
    for i in range(info.shape[0]):
        #
        # diff2dates(dt1,dt2)
        #
        diffdates = diff2dates(data[i,0],data[i,1])
        info[i,2] = diffdates
        if mode==0:
           info[i,0:2] = data[i,0:2]
        else:
           info[i,0] = np.where(udates==data[i,0])[0]
           info[i,1] = np.where(udates==data[i,1])[0]
    #
    return info,udates
#
def findindex_withoutJ(phsinfo,mj):
    # mj, array having all those at boundaries
    #
    for i,j in enumerate(mj):
      #index = []
      flag1  = phsinfo[:,0] != j
      flag2  = phsinfo[:,1] != j
      if i==0:
         flag = flag1 * flag2
      else:
         flag = flag * flag1 * flag2

    return np.where(flag==1)[0]
#
def average_aps4boundary(updated_phs,phsinfo,in_inds,out_inds,sign):
    #
    # invs = phsinfo[in_inds,2]
    #min_INV_inds = np.where(invs==np.min(invs))[0]
    counter = 0
    return np.mean(updated_phs[in_inds,2]) * sign * -1
    #
    for i,ci in enumerate(in_inds):
        #
        cinds = np.where(phsinfo[out_inds,2] == phsinfo[ci,2])[0]
        #
        if cinds.shape[0] == 0:
            cinds = out_inds
        else:
            cinds = out_inds[cinds]
        # 
        # after removing potential deformation, all pairs will be used 
        #
        dist = np.square((cinds - ci)**2)
        minDIST = np.where(dist == np.min(dist))[0]
        #
        factors = phsinfo[ci,2]/phsinfo[cinds[minDIST[0]],2]
        tmp = updated_phs[ci,2] - updated_phs[cinds[minDIST[0]],2]*factors
        #
        #
        if i == 0:
            totalRES = tmp
        else:
            totalRES = tmp + totalRES
        #
        counter = counter + 1 
    #
    return totalRES/counter * sign * -1
    #
    #
#
def DATA_updatedfromDIShistory(data,accumulated_dis):
    #
    #
    udates = np.sort(np.unique(np.ravel(data[:,0:2])))
    #
    outdata = np.copy(data)
    #
    for i in range(data.shape[0]):
        #
        mindex = np.where(udates==data[i,0])[0]
        sindex = np.where(udates==data[i,1])[0]
        #
        simDIS = accumulated_dis[sindex[0]] - accumulated_dis[mindex[0]]
        outdata[i,2] = outdata[i,2] - simDIS
        #
    return outdata
#
def updateboundary_APS(updated_phs,aps,apsdates,apsarray):
    #
    # estiamte aps components at the boundaries
    #
    if apsdates.shape[0]==0:
        return aps
    #
    phsinfo,udates = phsdata2info(updated_phs,mode=1)
    #
    index = np.array([apsarray[i][0] for i in range(len(apsarray))])
    allindex = np.array([i for i in range(apsdates.shape[0])])
    #
    # index array for saving those dates without APS estimation
    #
    uinds = []
    for i in allindex:
        if np.where(index==i)[0].shape[0]<1:
           uinds.append(i)
        #
    #
    uinds = np.array(uinds)
    apsflag = np.zeros(apsdates.shape[0])+1
    apsflag[uinds] = 0
    #
    noI_inds = findindex_withoutJ(phsinfo,uinds)
    #
    for i in uinds:
        #
        ind1 = np.where(phsinfo[:,0] == i)[0]
        ind2 = np.where(phsinfo[:,1] == i)[0]
        #
        if ind1.shape[0] > 0:
            ind  = ind1
            sign = -1
        else:
            ind  = ind2
            sign = 1
        #
        if ind.shape[0]>0:
            #
            # noI_inds = findindex_withoutJ(phsinfo,i)
            aps[i] = average_aps4boundary(updated_phs,phsinfo,ind,noI_inds,sign)
            #
        #
    #
    return aps
#
def commonAPS(updated_phs,cosd,info,udates,iters,chhmmss='12:00:00',hhmmss='12:00:00',initers=2,maxpairs=2,mode='pre'):
    #
    # cosd, coseismic dates, in the format of YYYYMMDD
    # updated_phs = data
    #
    #
    tmpiters = iters
    #
    A1       = None
    pairIDs  = None
    udates   = None
    apsarray = None
    counter  = 1
    aps      = None
    #
    diffdays = np.array([diff2dates(cdate,cosd,hhmmss1=hhmmss,hhmmss2=chhmmss) for cdate in updated_phs[:,1]])
    if mode.upper() == 'POST':
       #
       cphs = updated_phs[diffdays<0,:]
    else:
       #
       if mode.upper() == 'PRE':
           cphs =  updated_phs[diffdays>0,:]
       else:
           cphs = np.copy(updated_phs)
       #
    #
    if cphs.shape[0]==0:
        return np.array([]),np.array([])
    #
    A,lap,mdays,dates = infs2A(cphs)
    indays = np.array([diff2dates(cosd,dates[i],hhmmss1=chhmmss,hhmmss2=hhmmss) for i in range(dates.shape[0])])
    #
    apsarray = None
    A1       = None
    pairIDs  = None
    udates   = None
    aps      = None
    #
    inphs = np.copy(cphs)
    #
    while (tmpiters > 0):
      #
      aps,apsdates,A1,pairIDs,udates,apsarray = est_aps(inphs,maxpairs=maxpairs,aps=None,\
                                  apsarray=apsarray,iters=initers,A1=A1,pairIDs=pairIDs,udates=udates)
      #
      tmpphs = update_infs(inphs,aps,apsdates)
      #
      # removing deformation history for aps estimates at boundaries 
      #
      if True:
         x,_,_,_ = np.linalg.lstsq(A,tmpphs[:,2],rcond=None)
         #
         dis = x2accumulateddis(x)
         if mode.upper() == 'POST':
           paras = log_fit(indays[1::],dis)
           trend_est = log_func(indays[1::],paras[0],paras[1],paras[2])
         else:
           if mode.upper() == 'PRE':
             paras = linear_fit(indays[1::],dis)
             trend_est = linear_func(indays[1::],paras[0],paras[1])
           else:
             print("Err: %s mode cannot be recognized in the current version!!!")
         inphs = removepost(tmpphs,apsdates[1::],trend_est)
      #
      if counter == 1:
          totalaps = aps
      else:
          totalaps = aps+totalaps
      #
      tmpiters = tmpiters - 1
      counter = counter + 1
    #
    return totalaps, apsdates 
#
def removepost(pts_phs,postdate,trend_post):
    #
    postdate = np.array(postdate)
    outdata = np.copy(pts_phs)
    #
    #
    # print(postdate)
    for i in range(pts_phs.shape[0]):
        #
        flag1 = postdate>pts_phs[i,0]
        flag2 = postdate<=pts_phs[i,1]
        flag  = flag1 * flag2
        indx  = np.where(flag == 1)[0]
        # checking
        #
        if indx.shape[0]==1:
            outdata[i,2] = outdata[i,2] - trend_post[indx[0]]
        else:
            if indx.shape[0]>1:
                outdata[i,2] = outdata[i,2] - (trend_post[indx[-1]] - trend_post[indx[0]])
        #
    #
    #
    return outdata
            
def infinfo2elaspdays(data):
    #
    udates = np.sort(np.unique(data[:,0:2]))
    #
    infinfo = np.zeros([data.shape[0],3])
    for i in range(data.shape[0]):
        #
        infinfo[i,:] = [diff2dates(udates[0],data[i,0]),\
                        diff2dates(udates[0],data[i,1]),\
                       (diff2dates(udates[0],data[i,1])+diff2dates(udates[0],data[i,0]))/2]
        #
    #
    return infinfo
def log_func(x,a,tau,sigma):
    #
    return a*np.log(1+x/tau)+sigma
def log_fit(x,d):
    #
    res,_ = curve_fit(log_func,x,d,maxfev=10000)
    return res
#
def tsdata2weight(pts_phs,apsdates):
    #
    w = np.diag(np.ones(pts_phs.shape[0]))
    w = w*0.001
    for i in range(pts_phs.shape[0]):
        #
        ind1 = np.where(apsdates == pts_phs[i,0])[0]
        ind2 = np.where(apsdates == pts_phs[i,1])[0]
        if len(ind1)>0:
            w[i,i] = w[i,i]*1000
        if len(ind2)>0:
            w[i,i] = w[i,i]*1000
        #
    #
    return w
def linear_func(x,a,b):
    #
    return a*x+b
#
def linear_fit(x,d):
    #
    res,_ = curve_fit(linear_func,x,d,maxfev=5000)
    return res
#
def update_infs(phs_ts,aps,aps_dates):
    #
    outphs = np.copy(phs_ts)
    for i in range(aps_dates.shape[0]):
        #
        # index1 for primary date
        #
        index1 = np.where(phs_ts[:,0]==aps_dates[i])[0]
        if index1.shape[0]>0:
            outphs[index1,2] = outphs[index1,2] - aps[i]
        #
        # index2 for secondary date
        index2 = np.where(phs_ts[:,1]==aps_dates[i])[0]
        if index2.shape[0]>0:
            outphs[index2,2] = outphs[index2,2] + aps[i]
        #
    #
    return outphs
#
def est_aps(phs_ts,maxpairs=5,iters=3,aps=None,apsarray=None,A1=None,pairIDs=None,udates=None):
    #
    # phs_ts, N X 3 array, [primary, secondary, phase or los]
    # pairIDs, N x 3 array, [index-prim, index-second, diff days]
    #
    if A1 is None:
       baselineinfo = np.zeros([phs_ts.shape[0],3])
       baselineinfo[:,1:3]= phs_ts[:,0:2]
       A1,pairIDs,udates = pSAR.ts.ts_infs2apsA(baselineinfo)
       #
       apsarray = pSAR.ts.ts_pairIDs4apssyn(pairIDs,udates,cosd=None)
    #
    aps = pSAR.ts.ts_estaps_iter(phs_ts[:,2],apsarray,udates,pairIDs,aps=aps,maxpairs=maxpairs,iters=iters)
    #
    return aps,udates,A1,pairIDs,udates,apsarray
#
#
def set_x_datefmt(ax,myFmt):
    #
    ax.xaxis.set_major_formatter(myFmt)
    ax.spines['bottom'].set_linewidth(2.5)
    ax.spines['left'].set_linewidth(2.5)
    ax.spines['top'].set_linewidth(2.5)
    ax.spines['right'].set_linewidth(2.5)
    #
    # Updated by Wanpeng Feng, @NRCan, 2017-02-02
    # The defaut direction of ticks were changed since matplotlib_v2.0. Now it is out in default.
    # I fixed the direction as "in" for baesline plot...
    #
    ax.tick_params('both', length=10, width=0.75, direction='in',which='major')
    #
    labels = ax.get_xticklabels()
    plt.setp(labels, rotation=20, fontsize=10)
    return True
#
def dates2dts(dates,ismid=False):
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
def ts_split_A(data):
    #
    udates = np.unique(data[:,0:2].ravel())
    udates = np.sort(udates)
    A = np.zeros([data.shape[0]+1,udates.shape[0]])
    #
    for i in range(data.shape[0]):
        index1 = np.where(udates==data[i,0])[0]
        index2 = np.where(udates==data[i,1])[0]
        A[i,index1[0]] = 1
        A[i,index2[0]] = -1
        #
    #
    A[data.shape[0],0] = 1
    #
    return A,udates
def acc2vel(indata):
    #
    vel = []
    for i in range(indata.shape[0]-1):
        t1 = indata[i+1,0] - indata[i,0]
        v  = (indata[i+1,1] - indata[i,1])/t1
        vel.append([(indata[i+1,0] + indata[i,0])/2,v])
    return np.array(vel)
#
# calculate accumulated displacements between current dates to the beginning
#
def x2accumulateddis(x):
    #
    dis = np.copy(x)*0
    for i in range(x.shape[0]):
        tmp = 0
        for j in range(i):
            tmp = tmp + x[j]
        #
        dis[i] = tmp
    return dis
def dates2ts(udates):
    #
    ts_time = np.zeros(udates.shape[0])
    for i in range(udates.shape[0]):
        ts_time[i] = diff2dates(udates[0],udates[i])
    #
    return ts_time
#
def diff2dates(dt1,dt2,hhmmss1='12:00:00',hhmmss2='12:00:00'):
    #
    # cdt1 = datetime.datetime.strptime('%sT%s' % (str(int(dt1)),hhmmss1),'%Y%m%dT%H:%M:%S')
    # cdt2 = datetime.datetime.strptime('%sT%s' % (str(int(dt2)),hhmmss2),'%Y%m%dT%H:%M:%S')
    jd1 = pSAR.ts.yyyymmdd2jd(str(int(dt1)),hhmmss=hhmmss1)
    jd2 = pSAR.ts.yyyymmdd2jd(str(int(dt2)),hhmmss=hhmmss2)
    ddt =  jd2-jd1
    #
    #
    return ddt
#
def infs2A(data):
    #
    dates = np.sort(np.unique(data[:,0:2].ravel()))
    #
    # mdays is median days between primary and secondary sar data
    #
    mdays = [diff2dates(dates[0],dates[i]) for i in range(dates.shape[0])]
    mdays = [(mdays[i+1]+mdays[i])/2 for i in range(len(mdays)-1)]
    mdays = np.array(mdays)
    #
    A     = np.zeros([data.shape[0],mdays.shape[0]])
    lap   = np.zeros([mdays.shape[0],mdays.shape[0]])
    #
    for i in range(data.shape[0]):
        #
        mdif  = diff2dates(dates[0],data[i,0])
        sdif  = diff2dates(dates[0],data[i,1])
        flag1 = mdays > mdif
        flag2 = mdays < sdif
        flag  = flag1 * flag2
        A[i,flag==1] = 1 # sdif-mdif 
        #
    for i in range(lap.shape[0]-1):
        if i == 0:
          lap[i,i] = -1
          lap[i,i+1] = 1
        if i>0 and i < lap.shape[0]-1:
           lap[i,i-1] = -1/2
           lap[i,i]   = 1
           lap[i,i+1] = -1/2
        if i== lap.shape[0]-1:
           lap[i,i] = -1
           lap[i,i+1] = 1
        
    #
    return A,lap,mdays,dates
#
def aps(data,cosd,iters,maxpairs=2,isplot=False,unit='mm',hhmmss='12:00:00',chhmmss='12:00:00',A=None,mdays=None,apsplot=False,cosp=False,freqinfo=False):
    #
    # APS estimation based on Common Sence Stacking method (CSS)
    # proposed by    and Fialko (2015, JGR)
    #
    # cosp, coseismic data plotting
    #       False in default
    # 
    rawdata  = np.copy(data)
    alldates = np.sort(np.unique(data[:,0:2]))
    # infinfo  = infinfo2elaspdays(data)
    #
    # 
    plt_row = 1
    plt_col = 1
    if freqinfo:
        plt_row = 2
    #
    if apsplot:
        plt_row = plt_row+1
    #
    if cosd is not None:
        # 
        cosd_dt = diff2dates(alldates[0],cosd,hhmmss1=hhmmss,hhmmss2=chhmmss) 
        # 
        masterjds = np.array([pSAR.ts.yyyymmdd2jd(cdate,hhmmss=hhmmss) for cdate in data[:,0]])
        cosdjd    = pSAR.ts.yyyymmdd2jd(cosd,hhmmss=chhmmss)
        qtimeinfo = masterjds-cosdjd 
    #
    # first round for the retrieval of accumualted displacements
    #
    info,udates = phsdata2info(data)
    freq_dates  = phsdata2freq(data)
    #
    updated_phs = np.copy(data)
    #
    preaps,predates = commonAPS(updated_phs,cosd,info,udates,iters,hhmmss=hhmmss,chhmmss=chhmmss,maxpairs=maxpairs,mode='pre')
    #
    updated_phs = update_infs(data,preaps,predates)
    #
    #
    postphs = updated_phs[qtimeinfo>0,:]
    #
    if postphs.shape[0]>0:
      # 
      post_udates = np.sort(np.unique(postphs[:,0:2]))
      postaps,postdates = commonAPS(postphs,cosd,info,post_udates,iters,hhmmss=hhmmss,chhmmss=chhmmss,maxpairs=maxpairs,mode='post')
      updated_post_phs = update_infs(postphs,postaps,postdates)
      # 
      postA,postlap,postmdays,postdates = infs2A(updated_post_phs)
      #
      postdays = [diff2dates(cosd,postdates[i],hhmmss1=chhmmss,hhmmss2=hhmmss) for i in range(postdates.shape[0])]
      # 
      #
    else:
      postaps = np.array([])
      postdates = np.array([])
    #
    updated_phs = update_infs(updated_phs,postaps,postdates)
    #
    apsdates = np.hstack([predates,postdates])
    aps = np.hstack([preaps,postaps])
    # 
    if A is None:
       A,_,mdays,_ = infs2A(data)
    #
    try:
       x,res,rnk,info = np.linalg.lstsq(A,updated_phs[:,2],rcond=None)
    except:
       aps = aps * 0
       x = aps[1::]*0
       dis = x
       return aps,apsdates,x,dis
    #
    #
    dis = x2accumulateddis(x)
    #
    raw_x,res,rnk,info = np.linalg.lstsq(A,rawdata[:,2],rcond=None)
    raw_dis = x2accumulateddis(raw_x)
    #
    if cosd is not None and predates.shape[0]>=3:
       #
       data1 = update_infs(data,preaps,predates)
    else:
       data1 = np.copy(data)
    #
    # plotting settins since here
    #
    strudates = pSAR.ts.dates2dates(apsdates)
    stdates = np.array([strudates[i] for i in range(0,len(strudates)-1)])
    #
    if isplot:
       plt.subplot(plt_row,plt_col,1)
       plt.plot(stdates,raw_dis,'ok',markersize=5.5,label='Before_APSCOR')
       plt.plot(stdates,dis,'-or',label='After_APSCOR')
    #
    # linear modelling
    if predates.shape[0]>=5:
       #
       index = np.where(mdays<cosd_dt)[0]
       shift0 = dis[index[0]]
       #
       paras = linear_fit(mdays[index],dis[index]-shift0)
       trend_pre = linear_func(mdays[index],paras[0],paras[1])
       trend_pre = trend_pre + shift0
       #
       if isplot:
         plt.text(stdates[index[0]],trend_pre[0]+0.5,'y=<%f*t+%f>' % (paras[0],paras[1]))
         plt.plot(stdates[index],trend_pre,'-g',linewidth=5.5,label='Inter.(pre)')
       #
    if cosd is not None and postdates.shape[0]>=5:
       #
       index = np.where(mdays>cosd_dt)[0]
       shift0 = dis[index[0]]
       # 
       # estimating the trend of postseismic processes
       #
       paras = log_fit(mdays[index]-cosd_dt,dis[index]-shift0)
       trend_post = log_func(mdays[index]-cosd_dt,paras[0],paras[1],paras[2])
       trend_post = trend_post + dis[index[0]] # + shift0
       #
       # 
       if isplot and index.shape[0]>0:
          #
          # plt.subplot(plt_row,plt_col,1)
          # plt.plot(stdates,dis,'-or',label='After_APSCOR')
          plt.text(stdates[index[0]],trend_post[0]+0.5,'%f*log(1+t/%f)' % (paras[0],paras[1]))
          plt.plot(stdates[index],trend_post,'-b',label='Log(post)',linewidth='5.5')
    #
    #
    if cosp:
       #
       #
       plot_cosd_dt = pSAR.ts.dates2dates(np.array([cosd]))
       ymin,ymax = plt.gca().get_ylim()
       # cos_data = np.zeros([2,2])
       #
       if cosp:
         ax = plt.gca()
         ax.arrow(plot_cosd_dt[0],ymax, 0, -1* (ymin+ymax)/2, width=3.5,label='Coseismic')
         # plt.plot(cos_data[:,0],cos_data[:,1],'-g',linewidth=6,label='Coseismic')
         #
    #
    pltnum = 1
    if isplot:
      #
      plt.legend()
      #
      myFmt = mdates.DateFormatter('%Y-%m-%d')
      ax = plt.gca()
      ax.xaxis.set_major_formatter(myFmt)
      ax.spines['bottom'].set_linewidth(1.5)
      ax.spines['left'].set_linewidth(1.5)
      ax.spines['top'].set_linewidth(1.5)
      ax.spines['right'].set_linewidth(1.5)
      #
      ax.tick_params('both', length=10, width=0.75, direction='in',which='major')
      #
      ax.set_xlim(strudates[0],strudates[-1])
      #
      labels = ax.get_xticklabels()
      plt.setp(labels, rotation=15, fontsize=10)
      #
      plt.xlabel("Time Information (YYYY-MM-DD) ",fontsize=12.5)#,fontweight='bold')
      plt.ylabel("Accumualted Dis. (%s)" % unit,fontsize=12.5)
      #
    if apsplot:
      #
      struc_aps_dates = pSAR.ts.dates2dates(apsdates)
      pltnum = pltnum + 1
      plt.subplot(plt_row,plt_col,pltnum)
      plt.plot(struc_aps_dates,aps,'or',label='APS(rad)')
      ax = plt.gca()
      plt.legend()
      ax.xaxis.set_major_formatter(myFmt)
      ax.spines['bottom'].set_linewidth(1.5)
      ax.spines['left'].set_linewidth(1.5)
      ax.spines['top'].set_linewidth(1.5)
      ax.spines['right'].set_linewidth(1.5)
      #
      labels = ax.get_xticklabels()
      plt.setp(labels, rotation=15, fontsize=10)
      plt.ylabel("APS Components(%s)" % unit,fontsize=12.5)
      #
      #
    if freqinfo:
      #
      # freq_dates = freq_dates[1:-1,:]
      #
      pltnum = pltnum + 1
      plt.subplot(plt_row,plt_col,pltnum)
      #
      tmpDATEStr = pSAR.ts.dates2dates(freq_dates[:,0])
      #
      plt.bar(tmpDATEStr, freq_dates[:,1], width= 0.9, align='center',color='cyan', edgecolor = 'red')
      #
      ax = plt.gca()
      ax.xaxis.set_major_formatter(myFmt)
      ax.spines['bottom'].set_linewidth(1.5)
      ax.spines['left'].set_linewidth(1.5)
      ax.spines['top'].set_linewidth(1.5)
      ax.spines['right'].set_linewidth(1.5)
      #
      ax.tick_params('both', length=10, width=0.75, direction='in',which='major')
      #
      labels = ax.get_xticklabels()
      plt.setp(labels, rotation=15, fontsize=10)
      plt.xlabel("Time Information (YYYY-MM-DD) ",fontsize=12.5)#,fontweight='bold')
      plt.ylabel("Number of pairs",fontsize=12.5)
    if isplot:
      plt.show()
    #
    #
    return aps,apsdates,x,dis
