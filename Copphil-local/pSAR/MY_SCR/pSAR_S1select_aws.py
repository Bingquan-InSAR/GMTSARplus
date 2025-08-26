#!/usr/bin/env python
#
# 
#-----------------------------------------------------------------#

from lxml import etree
import xml.dom.minidom
import pS1
import glob
import pS1
import string, time, sys, os, shutil
import numpy as np, pSAR
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
#
helpstr='''\
    
    Usage: %s <outdir> <roi, minlon,maxlon,minlat,maxlat> -track [None in default] -searchstr "*.zip" -hc
              -sd 00010101 -ed 20500101    
              -s [as used for -searchstr] 
              -plot
              -move [if given, the file will be moved to <outdir>
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    This software is part of gInSAR software package to select RS2 based on given lonlat boundaries
    
    -hc     a flag to move the files to the targeted folder. It will de done o make soft link in default.
    -track  allow one more condition, track number. For example, "T156". None in default. 
    -plot   flag for a quick view or not 

    (c) 2015-2018 Canada Centre for Mapping and Earth Observation, Natural Resource Canada, Ottawa Canada
    
    ---
    Developed by Wanpeng Feng, @CCRS/CCMEO/NRCan, OTTAWA, 2016-12-01
    Updated by Wanpeng Feng, @NRCan, 2017-02-02
    Now shapely is used to check if a S1 covers the given area...  
    
    ---
    Updated by Wanpeng Feng, @NRcan, 2017-05-10
    A filter on time information is allowed.
    
    ---
    Updated by Wanpeng Feng, @SYSU, Guangzhou, 2021/08/07
    Move files into a new folder...

    '''
    
if len(sys.argv) < 3:
   print(helpstr % sys.argv[0]) 
   sys.exit(1)
#
# logging
#
pSAR.util.log(sys.argv)
#
#
searchstr   = "S1*.zip"
outdir      = sys.argv[1]
llbounds    = sys.argv[2].split(',')
llbounds    = np.array([float(llbounds[0]),float(llbounds[1]),float(llbounds[2]),float(llbounds[3])])
minlon      = np.min(llbounds[0:2])
maxlon      = np.max(llbounds[0:2])
minlat      = np.min(llbounds[2:4])
maxlat      = np.max(llbounds[2:4])
#
roi         = np.zeros([5,2])
roi[0,:],roi[1,:] = [minlon,minlat],[minlon,maxlat]
roi[2,:],roi[3,:] = [maxlon,maxlat],[maxlon,minlat]
roi[4,:]          = [minlon,minlat]
polyROI           = Polygon(roi)
#
track = None
plot = False
#
ismove = False
hc             = False
#
sdate   = '00010101'
edate   = '20500101'
counter = 0
#
for ckey in sys.argv:
   counter += 1
   if ckey == '-move':
      ismove = True
      hc = True
   if ckey == '-plot':
      plot = True
   if ckey == "-track":
      track = sys.argv[counter]
   if ckey == "-hc":
      hc = True
   if ckey == "-searchstr":
      searchstr = sys.argv[counter]
   if ckey == '-s':
      searchstr = sys.argv[counter]
   if ckey == "-sd":
      sdate = sys.argv[counter]
   if ckey == "-ed":
      edate = sys.argv[counter]
#
#
inputFileName  = glob.glob(searchstr)
print(inputFileName)
#
print(" Total %d S1 SAFE found!!" % len(inputFileName))
#
st = pSAR.ts.dates2jd(sdate+'T000001')
et = pSAR.ts.dates2jd(edate+'T000001')

#
if not os.path.exists(outdir):
   os.makedirs(outdir)
#
for czip in inputFileName:
  #
  # track control

  trackflag = True
  cxmlinfo = pS1.s1safe2manifestString(czip)
  #print(cxmlinfo)
  #sys.exit(-1)

  if cxmlinfo is not None:
    ctrack  = pS1.s1manifest2track(cxmlinfo,isfile=False)
    if (track is not None):
       # ctrack  = pS1.s1manifest2track(cxml)
       if ("T"+ctrack != track):
          trackflag = False
    #
    timeflag = False
    if trackflag:
      ct = pS1.s1totime(cxmlinfo,isfile=False)
      if ct is None:
         print(czip)
         sys.exit(-1)
      ct = pSAR.ts.dates2jd(ct)
      if (ct >= st and ct <= et):
         timeflag = True
      print(" %s: %s %s %s " % (ctrack,\
                              pSAR.ts.jd2datetime(st),\
                              pSAR.ts.jd2datetime(ct),\
                              pSAR.ts.jd2datetime(et)))
    corners = []
    if (trackflag and timeflag):
       corners = pS1.s1tocorners(cxmlinfo,isfile=False)
       #print(corners,roi)
    #
    flag    = False
    #
    if len(corners) > 0:
      #
      #
      cpoly   = Polygon(corners)
      flag    = polyROI.intersects(cpoly)
    #

    if flag:
       #
       #
       corners = np.vstack((corners,corners[0,:]))
       plt.plot(corners[:,0],corners[:,1],'-b',linewidth=1.0)
       xmlfullpath = os.path.abspath(czip)
       xmlpath     = os.path.dirname(xmlfullpath)
       xmlzipfile  = xmlfullpath 
       # print(" %s" % czip)
       #
       if os.path.exists(xmlzipfile):
          # print(" %s" % xmlzipfile)
          xmlzipinfolder = os.path.join(outdir,os.path.basename(xmlzipfile))
          if not os.path.exists(xmlzipinfolder):
            #
            if hc:
              shutil.move(xmlzipfile,xmlzipinfolder)
            else:
              os.symlink(xmlzipfile,xmlzipinfolder)
          xmlinfolder = os.path.join(outdir,os.path.basename(czip))
          #
          if not os.path.exists(xmlinfolder):
            #
            if hc:
               if ismove:
                  os.system("mv %s %s -f " % (czip,xmlinfolder))
               else:
                  shutil.move(xmlfullpath, xmlinfolder)
            else:
               os.symlink(xmlfullpath,xmlinfolder)
            #
          else:
            #
            if ismove:
              print(" %s has been found! Now saving the space by deleting %s" % (xmlinfolder,czip)) 
              os.system('rm %s -f' % czip)

  #
  else:
      print("ZIP-Error: ",czip)
  #
if plot:
  plt.plot(roi[:,0],roi[:,1],'-r',linewidth=2.5)
  plt.show()
