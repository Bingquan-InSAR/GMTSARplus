#!/usr/bin/env python
#
#
#
import multiprocessing as mp
import os
import sys
import glob
import numpy as np
import shutil
import pS1
#

#
def cdir2prm(indir):
    #
    cxml = glob.glob(indir+'/annotation/*%s*%s*.xml' % (swathID,pol))
    if len(cxml)>0:
        cxml = os.path.abspath(cxml[0])
        rootname = os.path.basename(cxml)
        oxml = PRM_DIR+'/'+rootname
        if not os.path.islink(oxml):
           os.symlink(cxml,oxml)
        #
        ctiff = os.path.abspath(indir+'/measurement/'+rootname.split('.xml')[0]+'.tiff')
        otiff = os.path.abspath(PRM_DIR+'/'+rootname.split('.xml')[0]+'.tiff')
        #
        if os.path.exists(ctiff):
           if not os.path.islink(otiff):
               os.symlink(ctiff,otiff)
           #
        #
        xmlroot = rootname
        tifroot = rootname.split('.xml')[0]+'.tiff'
        cdate   = rootname.split('-')[4][0:8]
        print(xmlroot,tifroot,cdate)
        #
        if os.path.islink(oxml) and os.path.islink(otiff):
           #
           os.chdir(PRM_DIR)
           #
           goStr = 'make_s1a_tops %s %s %s 0 ' % (xmlroot,tifroot,cdate)
           print(goStr)
           os.system(goStr)
           #
           # update height and baselineinfo
           shutil.copyfile(cdate+'.PRM','%s.junk1' % cdate)
           #
           goStr = 'calc_dop_orb %s.junk1 %s.junk2 0 0' % (cdate,cdate)
           os.system(goStr)
           goStr = 'cat %s.junk1 %s.junk2 > %s' % (cdate,cdate,cdate+'.PRM')
           os.system(goStr)
           #
           # extending orbit
           #
           goStr = 'extend_orbit %s.LED %s.tmp1.LED 3' % (cdate,cdate)
           print(goStr)
           os.system(goStr)
           os.system('mv %s.tmp1.LED %s.LED' % (cdate,cdate))
           #
           #
           os.chdir(TOP_DIR)
        
        #
    return True
#
global PRM_DIR,swathID,pol,TOP_DIR

njob = 10
TOP_DIR = os.getcwd()
PRM_DIR = 'tmpPRM_DIR'
#
if len(sys.argv)>1:
    swathID = 'iw%s' % sys.argv[1]
else:
    swathID = 'iw1'
pol = 'vv'
#
#
if not os.path.exists(PRM_DIR):
    #
    os.makedirs(PRM_DIR)
#
if True:
    dirs = os.getcwd()
    #
    #
    dirs = glob.glob('*.SAFE/')
    #
    cpool = mp.Pool(processes=njob)
    results = cpool.map(cdir2prm, dirs)
    cpool.close()
    cpool.join()
    #

