#!/usr/bin/env python
#
#
################################
import os,sys,pSAR,numpy as np 
import matplotlib
#matplotlib.use('Qt5Agg')
#
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pSAR
import pGMT5SAR
#
################################
if len(sys.argv)<2:
    helpstr=\
       '''  
          %s <infile_list> -min_time_lag 
                  -outname [root, identical with the input in default] 
                  -addlist [] -thres [None] -master [None, in default] 
                  -gamma
                  -t1 [19000101, in default]
                  -t2 [21000101, in default]
                  -c  [None, in default]  
                  -colordates [keyword, yes or no to colo dots]
                  -cax [default as 0.875, 0.35, 0.01, 0.35]
                  -loopid [None in default, otherwise with 3 dates, YYYYMMDD]
                  -loopdate [None in default, otherwise with a date, YYYYMMDD]
                  -sp [None in default, Selected Pairs]
                  -tmpbase [1000000 in default]
          ++++++++++++++++++++++++++++++++++++++++++
          To plot baseline information of all InSAR pairs recorded in the infile_list.
          
          Keywords:
          -master     Specify the reference acquisition, yyyymmdd, the first data in default
          -t1         lower time bound 
          -t2         upper time bound for interfergoram filter...
          -c          occurrance time of earthquake, in YYYYMMDD format, None in default
          -gmtsar     flag for data format from gmt5sar
          -noplot     means no GUI is required for this case. A graphic view is in default...
          -gmode      1 in default, e.g. 1 or 2 so far
                      only for -gmtsar, 1 means we have a baseline file having info as 
                      S1_XXXXX_ALL_F* ...
                      2 means a file with information as ...
                      s1a-... (xmlname)
          -ud         a UI application for showing date information 

          Developed by Wanpeng Feng, @NRCan, 2016-05-04 \n

          Updated by FWP, @SYSU, Guangzhou, 2020/04/14
                       baseline_table.dat from GMT5SAR is supported since this version.
     
       '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)

# logging
pSAR.util.log(sys.argv)
#
# Presettings for plot
#
tmpbase      = 100000
ui_dates     = False
gmode        = 1
gmtsar       = False
cax          = [0.875, 0.35, 0.01, 0.35]
colordates   = False
master       = None
fontsize     = 10 
thres        = None
min_time_lag = False
gamma        = False
t1           = 19000101
t2           = 21000101
ct           = None
plot         = True
loopid       = None
loopdate     = None
sp = None
################################
inlist  = sys.argv[1]
outname = os.path.basename(inlist) 
counter = 0
addlist = None
#
for ckeyword in sys.argv:
   counter += 1
   if ckeyword == '-tmpbase':
       tmpbase = int(sys.argv[counter])
       #
   if ckeyword == '-loopdate':
       loopdate = sys.argv[counter]
       #
   if ckeyword == '-sp':
       #
       sp =  sys.argv[counter]
   if ckeyword == '-loopid':
       loopid = sys.argv[counter].split(',')
   if ckeyword == '-ud':
       ui_dates = True
   if ckeyword == '-gmode':
       gmode = int(sys.argv[counter])
   if ckeyword == '-noplot':
       plot = False
   if ckeyword == '-gmtsar':
       gmtsar = True
       gamma = False
   if ckeyword == '-cax':
       cax = [float(ci) for ci in sys.argv[counter].split(',')]
   if ckeyword == '-colordates':
       colordates = True
   if ckeyword == '-c':
       ct = int(sys.argv[counter])
   if ckeyword == '-t1':
       t1 = int(sys.argv[counter])
   if ckeyword == '-t2':
       t2 = int(sys.argv[counter])
   if ckeyword == '-gamma':
      gamma = False
      gmtsar = True
   if ckeyword == "-master":
      master = sys.argv[counter]
   if ckeyword == "-thres":
      thres = float(sys.argv[counter])
   if ckeyword == "-addlist":
      addlist = sys.argv[counter]
   if ckeyword == "-min_time_lag":
      min_time_lag = True
   if ckeyword == "-outname":
      outname = sys.argv[counter]
#
################################
if master is None and ct is not None:
    master = ct
#
if __name__ == '__main__':
  # 
  if len(sys.argv)<2:
     usage()
  #
  ###############################
  if not os.path.exists(inlist):
     print(" Canot find %s" % inlist)
     sys.exit(-1)
  #
  # Formating output names...
  #
  outfig    = outname+'.pdf'
  outfig_png= outname+'.jpg'
  #
  fid       = open(inlist,'r')
  timeshift = 15
  perpext   = 10
  filepaths = [] 
  bperpinfo = []
  ################################
  spdata = None
  if sp is not None:
      spdata = []
      for csp in sp.split(','):
          #
          tmp = csp.split(':')
          spdata.append([int(tmp[0]),int(tmp[1])])
      #
      spdata = np.array(spdata)
      #
  #
  gmtsar = True
  if gamma:
     filepaths,bperpinfo = pSAR.ts.nw_read_gammalist(inlist)
  elif gmtsar:
     # a bug was fixed by Wanpeng Feng, @SYSU, 2024/02/29
     #
     filepaths,bperpinfo = pGMT5SAR.gmtsar_baseline(inlist,mode=gmode)

  else:
     filepaths,bperpinfo = pSAR.ts.nw_read_datalist(inlist, t1=t1,t2=t2)

  #
  m_diff_dates = np.array([pSAR.ts.diff2dates('%d' % bperpinfo[i,1],'%d' % bperpinfo[i,2]) for i in range(bperpinfo.shape[0])])
  #
  m_diff_dates = m_diff_dates.astype('int')
  #
  filepaths = np.array(filepaths)
  #
  filepaths = filepaths[m_diff_dates<=tmpbase]
  bperpinfo = bperpinfo[m_diff_dates<=tmpbase,:]
  #
  ##

  if addlist is not None:
     #
     if gamma: 
        filepathsADD,bperpinfoADD = pSAR.ts.nw_read_gammalist(addlist)
     else:
        # gmtsar:
        # fileparts,bperpinfo = pGMT5SAR.gmtsar_baseline(inlist)
        #  else:
        filepathsADD,bperpinfoADD = pSAR.ts.nw_read_datalist(addlist)
  #
  indMatrix, udate = pSAR.ts.nw_dateinfo2uniquedate(bperpinfo[:,1:3])
  #
  print(" There are total %d acquistions!!! " % len(udate))
  #
  if ct is not None:
    postdates = np.where(udate>=ct)[0]
    predates = np.where(udate<ct)[0]
    print(" %d pre-eq acquistions and %d post-eq acquisitions!!!" % (predates.shape[0],postdates.shape[0]))
  #
  # convert dates into decimal numbers 
  mJD = pSAR.ts.ts_julian(udate)
  #
  if master is None:
     if loopdate is not None:
         master = int(loopdate)
         #
     else:
         _, masetr = pSAR.ts.baselineinfo2master(bperpinfo,Tc=100.,Bc=150.)
     #
     #
  #
  if master is None:
     meanJD = np.mean(mJD)
     refindex = np.where(np.abs(mJD - meanJD) == np.min(np.abs(mJD-meanJD)))[0][0] + 1
  else:
     mJD = np.array(mJD)
     #
     ddates  = mJD - pSAR.ts.yyyymmdd2jd(master)
     mindiff = np.min(np.abs(ddates))
     minind  = np.where(np.abs(ddates) == mindiff)
     refindex = minind[0][0]+1
     if mindiff != 0:
        print(" +++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print(" + Warning: %s cannot be found in acquisition." % master)
        print(" +          %d instead is selected.           " % udate[refindex-1])
        print(" +++++++++++++++++++++++++++++++++++++++++++++++++++++")
     #
  pberp     = pSAR.ts.tinfo2baseline(bperpinfo[:,1:3],bperpinfo[:,0],refindex=refindex)
  #
  #
  #
  dims      = bperpinfo.shape
  strudates = pSAR.ts.dates2dates(udate)
  #
  xmindate  = strudates[0]  + datetime.timedelta(days=-timeshift)
  xmaxdate  = strudates[-1] + datetime.timedelta(days=timeshift)
  ymin      = np.min(pberp) - perpext
  ymax      = np.max(pberp) + perpext
  #
  myFmt = mdates.DateFormatter('%Y-%m-%d')
  #
  if ui_dates:
      plt.subplot(121)
      f = plt.gcf()
      ax = plt.gca()
  else:
      f, ax = plt.subplots(1) #, sharex=True)
  # Highlight Master
  plt.plot(strudates[refindex-1],pberp[refindex-1],'*',ms=15,color='red',label='Reference Acq.')
  #
  # pair information
  pre_counter = 0
  post_counter = 0
  for ni in range(dims[0]):
      #
      mdate = bperpinfo[ni,1]
      sdate = bperpinfo[ni,2]
      mperp = pberp[np.where(udate==mdate)]
      sperp = pberp[np.where(udate==sdate)]
      mstrd = strudates[np.where(udate==mdate)]
      sstrd = strudates[np.where(udate==sdate)]
      line  = np.array([[mstrd,mperp],[sstrd,sperp]])
      #
      # print(line)
      plt.plot(line[:,0],line[:,1],':',linewidth=0.8,color='gray')
      #
      if ct is not None:
          if sdate < ct:
              pre_counter = pre_counter + 1
              if pre_counter == 1:
                 plt.plot(line[:,0],line[:,1],'-',linewidth=0.8,color='red',label='Pre-EQ Inf.')
              else:
                 plt.plot(line[:,0],line[:,1],'-',linewidth=0.8,color='red')
          if mdate >= ct:
              post_counter = post_counter + 1
              if post_counter == 1:
                 plt.plot(line[:,0],line[:,1],'-',linewidth=0.8,color='blue',label='Post-EQ Inf.')
              else:
                 plt.plot(line[:,0],line[:,1],'-',linewidth=0.8,color='blue') 

      #
      if min_time_lag:
         #
         flag  = np.logical_and(udate > mdate,udate < sdate)
         if sum(flag) == 0:
           plt.plot(line[:,0],line[:,1],'-',linewidth=0.8,color='red')
      #
      cperpb = np.abs(line[0,1]-line[1,1])
      if thres is not None and cperpb < thres:
         plt.plot(line[:,0],line[:,1],'-',linewidth=0.8,color='red')
  #
  if spdata is not None:
     #
     for i in range(spdata.shape[0]):
         #
         mdate = spdata[i,0]
         sdate = spdata[i,1]
         mperp = pberp[np.where(udate==mdate)]
         sperp = pberp[np.where(udate==sdate)]
         mstrd = strudates[np.where(udate==mdate)]
         sstrd = strudates[np.where(udate==sdate)]
         line  = np.array([[mstrd,mperp],[sstrd,sperp]])        
         plt.plot(line[:,0],line[:,1],'-',linewidth=2.5,color='red',label='Selected Inf.')
  #
  if loopdate is not None:
      #
      # dpath,dinfo = pSAR.ts.nw_read_datalist(inlist)
      dinfo = np.array(bperpinfo)
      #
      # udates = np.sort(np.unique(np.ravel(dinfo[:,1:3])))
      udates = udate
      #
      bperp = pSAR.ts.tinfo2baseline(dinfo[:,1:3],dinfo[:,0])
      #
      current_pair = dinfo[:,1:3]
      pmatrix = pSAR.ts.nw_dateinfo2loopind(current_pair)
      #
      loopdate_id = np.where(udates==int(loopdate))[0]
      #
      pair_dates = np.array([np.sort(np.unique(np.ravel(current_pair[pmatrix[i,:]]))).astype('int') for i in range(pmatrix.shape[0])])
      #
      mindex = []
      #
      for i in range(pair_dates.shape[0]):
          #
          #
          if int(loopdate) in pair_dates[i,:]:
              mindex.append(i)
      #
      print(mindex)
      #
      for cid in mindex:
          #
          c_pairs = pmatrix[cid,:]
          c_dates = np.sort(np.unique(np.ravel(current_pair[c_pairs,:]))).astype('int')
          #
          ind_1 = np.where(udates==c_dates[0])[0]
          ind_2 = np.where(udates==c_dates[1])[0]
          ind_3 = np.where(udates==c_dates[2])[0]
          #
          plt.plot([strudates[ind_1],strudates[ind_2]],\
                    [pberp[ind_1],pberp[ind_2]],'-r',linewidth=2.5)
          #
          plt.plot([strudates[ind_1],strudates[ind_3]],\
                    [pberp[ind_1],pberp[ind_3]],'-r',linewidth=2.5)
          #
          plt.plot([strudates[ind_3],strudates[ind_2]],\
                    [pberp[ind_3],pberp[ind_2]],'-r',linewidth=2.5)

  if loopid is not None:
      #
      loopdates = np.array([int(cdate) for cdate in loopid])
      ind1 = np.where(udate==loopdates[0])[0]
      ind2 = np.where(udate==loopdates[1])[0]
      ind3 = np.where(udate==loopdates[2])[0]
      #
      if ind1.shape[0]>0 and ind2.shape[0]>0 and ind3.shape[0]>0:
          plt.plot([strudates[ind1[0]],strudates[ind2[0]]],\
                    [pberp[ind1[0]],pberp[ind2[0]]],'-r',linewidth=2.5)
          plt.plot([strudates[ind1[0]],strudates[ind3[0]]],\
                    [pberp[ind1[0]],pberp[ind3[0]]],'-r',linewidth=2.5)
          plt.plot([strudates[ind2[0]],strudates[ind3[0]]],\
                    [pberp[ind2[0]],pberp[ind3[0]]],'-r',linewidth=2.5)
  #
  if addlist is not None:
     dimsADD = bperpinfoADD.shape
     for ni in range(dimsADD[0]):
      #
      mdate = bperpinfoADD[ni,1]
      sdate = bperpinfoADD[ni,2]
      mperp = pberp[np.where(udate==mdate)]
      sperp = pberp[np.where(udate==sdate)]
      mstrd = strudates[np.where(udate==mdate)]
      sstrd = strudates[np.where(udate==sdate)]
      line  = np.array([[mstrd,mperp],[sstrd,sperp]])
      #
      plt.plot(line[:,0],line[:,1],'-',linewidth=0.5,color='blue') 
  # SAR acquisition time information
  ndates = udate.shape
  #
  for ndate in range(ndates[0]):
      #
      plt.text(strudates[ndate],pberp[ndate],str(udate[ndate]),fontsize=fontsize)
  
  ax = plt.gca()
  ax.set_xlim(xmindate,xmaxdate)
  #
  ax.set_ylim(ymin,ymax)
  #ax.set_ylim(-200,200)
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
  #
  plt.xlabel(" Time Information (YYYY-MM-DD) ",fontsize=12.5)#,fontweight='bold')
  plt.ylabel(" Perpendicular Baseline (m)",fontsize=12.5)#,fontweight='bold')
  #
  if ct is not None:
      plt.legend()
      print(" In total %d pre-earthquake  infs." % pre_counter)
      print(" In total %d post-earthquake infs." % post_counter)
  #
  if not colordates:
     plt.plot(strudates,pberp,'o',ms=10,color='green')
  else:
     A,_,_ = pSAR.ts.ts_infs2apsA(bperpinfo)
     colors = np.zeros(A.shape[1])
     for i in range(A.shape[1]):
        cA = np.copy(A[:,i])
        colors[i] = np.abs(cA).sum()
     #
     cdot_id = plt.scatter(strudates,pberp,marker='o',s=60,c=colors,cmap=plt.get_cmap('jet'))
  #
#  plt.plot(strudates[refindex-1],pberp[refindex-1],'*',ms=18,color='red',label='Reference Acq.')
  #
  plt.tight_layout()
  if colordates:
      #
      cbaxes = f.add_axes(cax)
      f.colorbar(cdot_id,cax = cbaxes)
      cbaxes.set_ylabel('Used Times')

  #
  if ui_dates:
      #
      plt.subplot(122)
      pSAR.ts.ui_ts_dates(udate)
  #
  #
  fig = plt.gcf()
  fig.set_size_inches(14,10, forward=True)
  #
  plt.savefig(outfig,dpi=720)
  plt.savefig(outfig_png,dpi=720)
  if plot:
     plt.show()
