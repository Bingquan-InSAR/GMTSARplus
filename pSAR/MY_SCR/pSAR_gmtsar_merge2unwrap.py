#!/usr/bin/env python
#
#
import multiprocessing as mp
import glob
import os
import sys
import pSAR
#
def read_wrap_dirs(in_list):
    #
    wrap_dirs = []
    with open(in_list,'r') as fid:
        for cline in fid:
            cline = cline.split('\n')[0]
            wrap_dirs.append(cline)
            #
        #
    #
    return wrap_dirs
def dir2unw(cdir):
    #
    os.chdir(topdir)
    os.chdir(cdir)
    #
    if redomerge:
        os.system('rm *.in -f')
        os.system('rm *.bin -f')
        #
        os.system('gmtsar_merge_redo.py supermaster -update')
        #
    if unwrap_thresh == 0:
        # goStr = 'merge_unwrap_tops.csh batch_config.cfg %d %s %s ' % (unwrap_thresh,script,method)
        goStr = 'gmtsar_unwrap.py %d -m %s -maxc 2000 %s -snaphu_alg %s -in %s' % (unwrap_thresh,method,unwrap_interp,snaphu_alg,phasefilt)
    else:
        # goStr = 'merge_unwrap_tops.csh batch_config.cfg %f %s %s ' % (unwrap_thresh,script,method)
        goStr = 'gmtsar_unwrap.py %f -m %s -maxc 2000 %s -snaphu_alg %s -in %s' % (unwrap_thresh,method,unwrap_interp,snaphu_alg,phasefilt)
    #
    print(" Progress: %s" % goStr)
    os.system(goStr)
    goStr = 'pSAR_gmtsar_geocode_dir.py'
    print(" Progress: %s" % goStr)
    os.system(goStr)
    # 
    # creating azi and inc files 
    goStr = 'pSAR_gmtsar_dir2losvecs.py'
    os.system(goStr)
    #
    #
    return True
#
if len(sys.argv)<3:
    helpstr = \
        '''
           %s <unwrap_threshod>  <njob> -script [None in default] -method [fls in default]
               -list [None in default] -redomerge
               -i [0 in default]
               -snaphu_alg ["MCF" in default] -phasefilt [phasefilt.grd in default]
           +++++++++++++++++++++++++++++++++++++++++++
           To unwrap and geocode individual folders in the local folder.
           In default, the folder, merge should have a topo folder for dem and trans.dat

           trans.dat may not be available yet, but will be generated first...
           
           Created by Wanpeng Feng, @SYSU，Guangzhou, 2020/04/16

        '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
#
################################################################
#
pSAR.util.log(sys.argv)
# 
global topdir,script,method,redomerge,unwrap_interp,snaphu_alg,phasefilt
#
snaphu_alg = "MST"
unwrap_interp = None
redomerge = False
unwrap_thresh = float(sys.argv[1])
njob          = int(sys.argv[2])
script        = ''
method        = 'fls'
in_list       = None
phasefilt     = 'phasefilt.grd'
#
for i,key in enumerate(sys.argv):
    #
    if key == '-phasefilt':
        phasefilt = sys.argv[i+1]
    if key == '-snaphu_alg':\
        snaphu_alg = sys.argv[i+1].upper()
    if key == '-i':
        unwrap_interp = '-i 1'
    if key == '-redomerge':
        redomerge = True
    if key == '-list':
        in_list = sys.argv[i+1]
    if key == '-method':
        method = sys.argv[i+1]
    if key == '-script':
        script = sys.argv[i+1]
    #
#
if unwrap_interp is None:
    unwrap_interp = ''
#
#
topdir = os.getcwd()
#
print(" Progress: working in the folder of merge to unwrap and geodode the results...")
#
if True:
    #
    if in_list is None:
       #
       folders = glob.glob('2*_2*/')
    else:
       #
       print(" Progress: now reading a wrapped phase list of %s" % in_list)
       #
       folders = read_wrap_dirs(in_list)
       #
    #
    # making trans.dat first...
    #
    if len(folders)<1:
        print( " Warning: no intf folder was found in %s" % os.getcwd())
        sys.exit(-1)
    #
    if not os.path.exists('topo/trans.dat'):
      os.chdir(folders[0])
      goStr = 'merge2trans.csh batch_config.cfg'
      print(" Progress: creating a universal trans.dat first for all merged interferograms...")
      os.system(goStr)
    #
    os.chdir(topdir)
    #
    #
    cpool = mp.Pool(processes=njob)
    results = cpool.map(dir2unw,folders)
    cpool.close()
    cpool.join()
