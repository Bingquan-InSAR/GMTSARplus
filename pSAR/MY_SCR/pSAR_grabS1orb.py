#!/usr/bin/env python
#
###############################################
#
from urllib.request import Request
from urllib.request import urlopen,URLError
import ssl, re, sys, os, subprocess
from multiprocessing.pool import ThreadPool
import numpy as np
from bs4 import BeautifulSoup, SoupStrainer
import pSAR
import numpy as np
import calendar 
import datetime
import requests
#
###############################################
def alldates(dt1,dt2,fmt='%Y%m%d'):
    if fmt.upper() == 'DT':
        sd = dt1;
        ed = dt2;
    else:
        sd = datetime.datetime.strptime(dt1, fmt)
        ed = datetime.datetime.strptime(dt2, fmt)
    delta = ed - sd        # timedelta
    outdates = []
    for i in range(delta.days+1):
        outdates.append((sd + datetime.timedelta(i)).strftime('%d-%m-%Y'))
    return outdates
#
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
    lst = [datetime.datetime.strptime('%2.2d-%2.2d' % (y, m), '%Y-%m').strftime('%m-%Y') \
      for y in range(sd.year, ed.year+1) \
      for m in range(sd.month if y==sd.year else 1, ed.month+1 if y == ed.year else 13)]
    return lst
#
def timematching(eofs,sjd,ejd,reforb=None):
    #
    eofs = np.array(eofs)
    #
    # updated by FWP, @SYSU, 2020/04/12
    #
    if reforb is not None:
        try:
          eof_names = [ceof.split('.')[0] for ceof in eofs]
        except:
          eof_names = [ceof.split('/')[-1].split('.')[0]  for ceof in eofs]
        #
        flag = [ceof.upper().strip() == reforb.upper().split('.EOF')[0].strip() for ceof in eof_names]
        return eofs[flag]
        # 
    try:
       eof_times = [[ceof.split('.')[0].split('_')[6][1::],ceof.split('.')[0].split('_')[7]] for ceof in eofs] 
    except:
       eof_times = [[ceof.split('/')[-1].split('.')[0].split('_')[6][1::],ceof.split('/')[-1].split('.')[0].split('_')[7]] for ceof in eofs] 
    #
    eof_times = np.array(eof_times)
    #
    eof_times_jd = np.zeros([eof_times.shape[0],2])
    eof_times_jd[:,0] = [pSAR.ts.timestr2jd(ctime,fmt='%Y%m%dT%H%M%S') for ctime in eof_times[:,0]]
    eof_times_jd[:,1] = [pSAR.ts.timestr2jd(ctime,fmt='%Y%m%dT%H%M%S') for ctime in eof_times[:,1]]
    #
    flag1 = eof_times_jd[:,0] <= ejd
    flag2 = eof_times_jd[:,1] >= sjd
    #
    flag = flag1 * flag2
    
    return eofs[flag]    
#
def eof_search_asf(url,outdir,isupdate=False):
    #
    out1 = outdir+'/orbit.html'
    out2 = outdir+'/orbit.txt'
    if isupdate:
        if os.path.exists(out1):
            os.system('rm %s -f' % out1)
            os.system('rm %s -f' % out2)
        #
    #
    if not os.path.exists(out1):
        #
        # set url_root = "https://s1qc.asf.alaska.edu/aux_poeorb/"
        # wget $url_root -O orbits.html
        # grep EOF orbits.html | awk -F'"' '{print $2}' > orbits.list
        osGo = 'wget %s -O %s' % (url,out1)
        print(osGo)
        os.system(osGo)
    #
    tolnum = 0
    eofarr = []
    if not os.path.exists(out2):
        #
        osGo = "grep EOF %s | awk -F'" % out1 +'"'+"' '{print $2}' > %s" % out2
        print(osGo)
        os.system(osGo)
    if os.path.exists(out2):
        #
        with open(out2,'r') as fid:
            for cline in fid:
                tmp = cline.split('\n')[0]
                eofarr.append(tmp)
                tolnum = tolnum + 1
    #
    return tolnum,eofarr
#
def eof_search(url,model,outdir,cyear,cmonth,cdate):
    #
    # search potential eof data files from the ESA official website
    #
    tolnum = 0
    eofarr = []
    if True:
        target_url = ("%s/%s/%s/%s/%s/" % (url,model.upper(),cyear,cmonth,cdate))
        # print(target_url)
        soup, urlcode = https_split(target_url)
        # print(soup)
        if soup is not None:
          eofnum, outeof= soup_eof(soup)
        else:
          eofnum = 0
        #
        if eofnum > 0:
           if tolnum == 0:
               eofarr = outeof
               tolnum = eofnum
               #
           else:
               tolnum += eofnum
               eofarr = eofarr + outeof
    #
    return tolnum,eofarr
#
#
def download_eofurl_asf(eoflist,url,outdir,usr='wasar',passwd='Coco3333$'):
    #
    for ceof in eoflist:
        #
        if len(ceof.split('/')) > 1:
            ceof = ceof[-1]
        #
        final_url = '%s%s' % (url, ceof)
        # check_existing = requests.get(final_url)
        # print("checking weblink: %s VS %s" % (final_url,check_existing.status_code))\
        #
        # if check_existing.status_code == 200 or  check_existing.status_code == 401:
        if True:
            wget_cTr = ("wget -c --no-check-certificate --http-user=%s --http-password=%s -P %s %s" % (usr,passwd,outdir,final_url))
            print(wget_cTr)
            os.system(wget_cTr)
        #
    return False
def download_eofurl(eoflist,url,outdir,searchdate):
    #
    for ceof in eoflist:
        #
        if len(ceof.split('/')) > 1:
            ceof = ceof[-1]
        #
        model = ceof.split('_')[3]
        # cyear = ceof.split('_')[5][0:4]
        # cmonth = ceof.split('_')[5][4:6]
        # cdate = ceof.split('_')[5][6:8]
        ymd = searchdate.split('-')
        cyear  = ymd[2]
        cmonth = ymd[1]
        cdate  = ymd[0]
        #
        if not os.path.exists(outdir+'/'+ceof):
           final_url = url+'/%s/%s/%s/%s/' % (model.upper(),cyear,cmonth,cdate) + ceof
           #
           #
           
           check_existing = requests.get(final_url)
           print("checking weblink: %s VS %s" % (searchdate,cdate), check_existing.status_code)
           #
           if check_existing.status_code == 200:
              wget_cTr = ("wget -c --no-check-certificate -P %s %s" % (outdir,final_url))
              print(wget_cTr)
              os.system(wget_cTr)
    #
    return False
#
################################################
def https_split(url):
    #
    #
    context = ssl._create_unverified_context()
    urlpath = requests.get(url)
    #
    # urlpath = urlopen(url,context=context)
    # soup = BeautifulSoup(urlpath,"lxml")
    # urlpath = urlopen(url,context=context)
    if (urlpath.status_code / 100 >= 4):
       soup = None
       returncode = urlpath.status_code
    else:
       urlpath = urlopen(url,context=context)
       soup = BeautifulSoup(urlpath,"lxml")
       returncode = urlpath.code
    return soup, returncode
#
def soup_eof(insoup):
    #
    #
    outnumber = 0
    outeof    = []
    for link in insoup.findAll('a'):
        href = link.get('href') 
        # print(href)
        if href is not None:
          if ".EOF" in href:
            outeof.append(href)
            outnumber += 1
    #
    return outnumber,outeof
###############################################
# 
#
if len(sys.argv) < 2:
   helpstr=\
   '''
      %s <starttime> <stoptime> -model <RESORB in default> 
                                -s1_orb [defined in system in default] 
                                -mission [S1A and S1B in default] 
                                -fmt [time format]
                                -reforb [None]
                                -update [False in default]
                                -usr [wasar, for asf in default]
                                -passwd [Coco3333$ in default]
      ++++++++++++++++++++++++++++++++++++++++++++++++++
      To return precise orbital determination (POD) data full address from ESA

      <startTime> and <stopTime> are two necessary inputs to specify the state vectors that will be applied to the data.

      
      Model:
      <model> POEORB or RESORB
      
      -s1_orb [path_for_state_vectors] a default setting from sysmte environment if not given...
      If a specific month is given, the search will only be implemented in that month...
      urllib2, bs4(BeautifulSoup) and ssl are required for a successful application.
      Developed by Wanpeng Feng, @NRCan, 2017-02-07
      #
      -reforb a specific orbfile is given. None is in default.
      -url    'http://aux.sentinel1.eo.esa.int'
      Updated by Wanpeng Feng, @CCRS/NRCan, 2017-11-03 to make it work in python3
     
      Since this version, the startTime and stopTime will be given. So the search time can be specified based on the information.
      In default, the <startTime> and <stopTime> should be in a format like "2018-02-19T23:10:17.573866"
      Rewritten by Wanpeng Feng, @CCRS/NRCan, 2018-05-15 to allow to search a specific file online. 
      #
      -fmt time format, in default "%%Y%%m%%dT%%H%%M%%S"
      added by Wanpeng Feng, @SYSU(Guangzhou), 2018-11-02
      #
      Updated by FWP, @SYSU, Guangzhou, 2021/04/06
      http://aux.sentinel1.eo.esa.int has been out of line, we now try to swithc to below website...
      #
      replaced by below site
      https://s1qc.asf.alaska.edu/
   '''
   print(helpstr % sys.argv[0])
   sys.exit(-1)

###############################################
update    = False
reforb    = None
counter   = 0
njobs     = 2
startTime = sys.argv[1]
stopTime  = sys.argv[2]
#
model     = 'RESORB' 
savedir   = None 
syear     = 2014
eyear     = 2020
spemonth  = None
fmt       = '%Y-%m-%dT%H:%M:%S.%f'
fmt       = '%Y%m%dT%H%M%S'
url       = 'http://aux.sentinel1.eo.esa.int'
url       = 'https://s1qc.asf.alaska.edu/'
mission   = 'S1A'
usr       = 'wasar'
passwd    = 'Coco3333$'
#
###############################################
#
for ckey in sys.argv:
  #
  counter += 1
  if ckey == '-usr':
      usr = sys.argv[counter]
  if ckey == '-passwd':
      passwd = sys.argv[counter]
  if ckey == '-update':
      update = True
  if ckey == '-reforb':
     reforb = sys.argv[counter]
  if ckey == '-mission':
     mission = sys.argv[counter]
  if ckey == '-model':
     model = sys.argv[counter]
  if ckey == "-s1_orb":
     savedir = sys.argv[counter]
  if ckey == '-fmt':
     fmt = sys.argv[counter]
#
##############################################
if savedir is None:
    savedir = os.environ['S1_ORB']
#
# 
potential_orbs = []
#
if True:
  #
  startTime_num = pSAR.ts.timestr2jd(startTime,fmt=fmt)
  stopTime_num  = pSAR.ts.timestr2jd(stopTime,fmt=fmt)
  startTime_dt  = pSAR.ts.timestr2datetime(startTime,fmt=fmt)
  stopTime_dt   = pSAR.ts.timestr2datetime(stopTime,fmt=fmt)
  syear         = startTime_dt.year
  eyear         = stopTime_dt.year
  dataMean_num  = (startTime_num + stopTime_num) / 2
  dataMean      = pSAR.ts.jd2timestr(dataMean_num,fmt=fmt)
  dataMean_dt   = pSAR.ts.timestr2datetime(dataMean,fmt=fmt)
  cmonth = dataMean_dt.month
  cyear  = dataMean_dt.year
  sdate  = startTime_dt.day
  edate  = stopTime_dt.day
  #
  if model.upper() == 'POEORB':
      shiftdays = 25
      startTime_dt  = startTime_dt + datetime.timedelta(days=18)
  else:
      shiftdays = 1
  #
  enddates  = stopTime_dt + datetime.timedelta(days=shiftdays)
  #
  alldates = alldates(startTime_dt,enddates,fmt='DT')
  #
  #
  if model.upper()=="POEORB":
     outdir = savedir + '/aux_poeorb/'
  else:
     outdir = savedir + '/aux_resorb/'
  #
  #
  if True:
  # for tmpdate in alldates:
      # cmonth = tmpdate.split('-')[1]
      # cyear =  tmpdate.split('-')[2]
      # cdate =  tmpdate.split('-')[0]
    eofnum,outeof = eof_search_asf('%saux_%s' % (url,model.lower()),outdir,isupdate=update)
    for tmpdate in alldates:
      cmonth = tmpdate.split('-')[1]
      cyear =  tmpdate.split('-')[2]
      cdate =  tmpdate.split('-')[0]
      #
      if eofnum > 0:
        ceof = timematching(outeof,startTime_num,stopTime_num,reforb=reforb)
        print("  ** Info: %d EOF are available on %s-%s-%s" % (len(ceof),cyear,cmonth,cdate))
        #
        if len(ceof) > 0:
           # download_eofurl(ceof,url,outdir,tmpdate)
           if not os.path.exists("%s/%s" % (outdir,ceof)):
              download_eofurl_asf(ceof,"%saux_%s/" % (url,model.lower()),outdir,usr=usr,passwd=passwd)
           flag = False 
           for myeof in ceof:
               cmission = myeof.split('_')[0]
               if os.path.exists(outdir+'/'+myeof) and not os.path.exists(myeof) and \
                  cmission == mission:
                  os.symlink(outdir+'/'+myeof,myeof)
