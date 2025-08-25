#!/usr/bin/env python
#
#
import os
import sys
import glob
import numpy as np
import pS1
import pSAR
#
def safedirsort(tifs,master):
    #
    if master is None:
       print(" No master is given! %s is picked as master..." % tifs[0].split('.tiff')[0])
       return tifs
    #
    topid = 0
    for i in range(len(tifs)):
        if master in tifs[i]:
           topid = i
        #
    #
    tmpa = tifs[0]
    tifs[0] = tifs[topid]
    tifs[topid] = tmpa
    return tifs
#
if len(sys.argv)<3:
    helpstr = \
      '''
      %s <raw_folder> <data.list> -master [None in default] 
                           -pol [vv in default]
                           -l [PWD in default] -update
                           -eofmodel ['resorb']
      ++++++++++++++++++++++++++++++++++++++
      To generate a data.list for use in preproc_batch_topo_esd.csh
      
      create F1/F2/F3 subfolders for further processing
      
      -l local path where we will create F1/F2/F3 sub-folders for individual swaths...

      created by Wanpeng Feng, @SYSU, Guangzhou, 2020/04/13
      
      '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
    #
#
pSAR.util.log(sys.argv)
#
in_folder = sys.argv[1]
pol = 'vv'
out_list  = 'data.list'
master    = None
update    = False
eofmodel  = 'RESORB'
l = os.getcwd()
#
#
for i, key in enumerate(sys.argv):
    if key == '-eofmodel':
       eofmodel = sys.argv[i+1].upper()
    if key == '-update':
       update = True
    if key == '-l':
       l = sys.argv[i+1]
    if key == '-master':
       master = sys.argv[i+1]
#
if len(sys.argv)>2:
    out_list = sys.argv[2]
#
if True:
    safe_dirs = glob.glob(in_folder+'/*.SAFE/')
    if len(safe_dirs)<2:
        print(" ERROR: no valid SAFE folders were found!!!!")
        sys.exit(-1)
    #
    if update:
        # clean up first if update is given...
        print(" Progress: clean up raw folders first. data.in if available will be removed...")
        os.system('rm F*/raw/data.in -f')
    #
    #
    for i in range(3):
        t = i + 1
        if os.path.exists(os.path.join(l,'F%d/raw/data.in' % t)):
            continue
        #
        if not os.path.exists(os.path.join(l,'F%d/raw' % (i+1))):
            os.makedirs(os.path.join(l,'F%d/raw' % (i+1)))
    #
    if os.path.exists(os.path.join(l,'F1/raw/data.in')) or \
       os.path.exists(os.path.join(l,'F2/raw/data.in')) or \
       os.path.exists(os.path.join(l,'F3/raw/data.in')):
        print(" Progress: Quit now as data.in have been created in the target folders...")
        sys.exit(-1)
    #
    fid_F1 = open(os.path.join(l,'F1/raw/data.in'),'w')
    fid_F2 = open(os.path.join(l,'F2/raw/data.in'),'w')
    fid_F3 = open(os.path.join(l,'F3/raw/data.in'),'w')
    #
    safe_dirs = safedirsort(safe_dirs,master)
    #
    for jj in range(len(safe_dirs)):
       #
       cdir = safe_dirs[jj]
       cdir = os.path.abspath(cdir)
       tifs = glob.glob(os.path.join(cdir,'measurement/*iw*%s*.tiff' % pol))
       #
       print(" Checking before seaching orb, in %s" % cdir)
       cdate=cdir[-39:-31]
       
       orb,flag = pS1.s1dir2orb(os.path.basename(cdir),cdate,orbdir=None,model=eofmodel)

       print(" Checking: %s" % orb)
       #
       if not flag:
           orb = pS1.s1zip2statevector(cdir,model='RESORB',isdir=True)
           if os.path.exists(orb):
               flag = True
           #
       #
       if not flag:
           print(" ERR: EOF for %s is NOT ready. Updating orbit DB now..." % cdir)
           #print(os.getcwd())
           topdir = os.getcwd()
           os.chdir('DATA/S1_ZIP_RAW')
           goStr = 'pSAR_s1zips2orb.py *.zip -model %s' % eofmodel
           os.system(goStr)
           os.chdir(topdir)
       #
       if flag and len(tifs)>=1:
          for ctif in tifs:
              ctif = os.path.abspath(ctif)
              ctifname = os.path.basename(ctif).split('.tiff')[0]
              track = ctifname.split('-')[1][2:3]
              xml = ctif.replace('measurement/','annotation/')
              xml = xml.replace('.tiff','.xml')
              track_F = os.path.join(l,'F%s' % track)
              #
              target_ctif = os.path.join(l,'F%s/raw/%s' %(track,os.path.basename(ctif)))
              if os.path.exists(ctif) and not os.path.exists(target_ctif):
                 os.system('ln -s %s %s' % (ctif,target_ctif))
                 #
                 # os.system('ln -s %s F%s/raw/. ' % (xml,track))
                 pS1.s1xmlupdate(xml,outxml=os.path.join(l,'F%s/raw/%s' % (track,os.path.basename(xml))))
                 #
              target_orb = os.path.join(l,'F%s/raw/%s' %(track,os.path.basename(orb)))
              if not os.path.exists(target_orb):
                 os.system('ln -s %s %s ' % (orb,target_orb))
              #
              if track=='1':
                  fid_F1.write('%s\n' % ('%s:%s' % (ctifname,os.path.basename(orb))))
              elif track=='2':
                  fid_F2.write('%s\n' % ('%s:%s' % (ctifname,os.path.basename(orb))))
              elif track == '3':
                  fid_F3.write('%s\n' % ('%s:%s' % (ctifname,os.path.basename(orb))))
                 #
              #
        #
        #
    #
    fid_F1.close()
    fid_F2.close()
    fid_F3.close()
    #

