#!/usr/bin/env python
#
#
import pGMT5SAR
import glob
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pSAR
#
def pairs2mergelist(pairs,outfile='merge_list'):
    #
    with open(outfile,'w') as fid:
        for cline in pairs:
            fid.write('%s\n' % cline)
    return True
def dirs2mergelist(iws,master):
    #
    # in default, the function will be working when you are in the folder of "merge"
    #
    target_dir = os.path.dirname(os.getcwd())
    #
    iws = np.array(iws)
    index = np.where(iws!=0)[0]
    iwdirs = ['F%d' % (i+1) for i in index]
    dirs = []
    for i in index:
       dirs_x = glob.glob(target_dir+'/F%d/intf_all/*/' % (i+1))
       dirs_x = [os.path.basename(os.path.dirname(cdir)) for cdir in dirs_x]
       dirs.append(dirs_x)
    #
    # 
    #if len(dirs)<2:
    #    print(" Progress: less than 2 swaths were found with valid intf_all")
    #    print("           no need for futher processing...")
    #    return False,None
    #
    if len(dirs)<2:
        print(" Progress: WARNING!!! No availabe swath available ...")
        return False,None
    #
    pairs = np.unique(np.array(dirs[0]).ravel())
    #
    mydirs = []
    #
    for cpair in pairs:
        counter = 0
        mystr = ''
        for tmpdir in iwdirs:
            test_dir = '../'+tmpdir+'/intf_all/%s' % cpair
            #
            if os.path.exists(test_dir):
               counter = counter +1
               prms = glob.glob(test_dir+'/S1*_ALL*.PRM')
               prms.sort()
               prms = [os.path.basename(cprm) for cprm in prms]
               #
               if counter == 1:
                   mystr = "%s:%s" % (test_dir+'/',":".join(prms))
               else:
                   mystr = "%s,%s" % (mystr,"%s:%s" % (test_dir+'/',":".join(prms)))
            #
        #
        if counter == len(iwdirs):
            mydirs.append(mystr)
    #
    k = 0
    for i in range(len(mydirs)):
        first_prm = mydirs[i].split(':')[1]
        if master in first_prm:
            k = i
            break
            #
    if k != 0:
       tmp_line = mydirs[0]
       mydirs[0] = mydirs[k]
       mydirs[k] = tmp_line
    #
    return True,mydirs
#
if len(sys.argv)<2:
    helpstr = \
        '''
        %s <iws, 1,1,1 in default for all three swath> -master <> 
           -unwrap_threshold [0.1 in default]
           -interp_flag [1 in default]
        ++++++++++++++++++++++++++++++++++++++++++
        To merge sub-swath into an integrated files...
        In default, three data will be generated:
        
        phasefilt.grd
        corr.grd
        mask.grd
        
        by Wanpeng Feng, @SYSU, Guangzhou, 2020/10/01

        flength, range_dec and azimuth_dec will be updated based on the configure files
        in individual folders. 
        Updated by Feng, Wanpeng, @SYSU, Guangzhou, 2021/03/29

        '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
#
#
pSAR.util.log(sys.argv)
#
#
iws = [int(ciws) for ciws in sys.argv[1].split(',')]
merge_dir = 'merge'
master = None
unwrap_threshold = 0.1
interp_flag      = 1
flength = None 
rlook=8
azlook=2
#
for i,key in enumerate(sys.argv):
    #
    if key == '-unwrap_threshold':
        unwrap_threshold = float(sys.argv[i+1])
    if key == '-interp_flag':
        interp_flag = int(sys.argv[i+1])
    if key == '-master':
        master = sys.argv[i+1]
    if key == '-flength':
        flength = int(sys.argv[i+1])
    if key == '-azlook':
        azlook = int(sys.argv[i+1])
    #
#
if flength is None:
    #
    flength = int(azlook*100)
#
if master is None:
    print(" ERR: master is not given yet!!! ")
    sys.exit(-1)
#
if True:
   topdir = os.getcwd()
   if not os.path.exists(topdir+'/merge'):
       #
       os.makedirs(topdir+'/merge')
   #
   os.chdir(os.path.join(topdir,'merge'))
   #
   # link topo
   if not os.path.exists('topo'):
       os.makedirs('topo')
   demgrd = 'topo/dem.grd'
   if not os.path.exists(demgrd):
       os.symlink(topdir+'/topo/dem.grd',demgrd)
   if not os.path.exists('dem.grd'):
       os.symlink(topdir+'/topo/dem.grd','dem.grd')
   #
   #
   flag, dirs = dirs2mergelist(iws,master)  
   #
   pairs2mergelist(dirs,outfile='merge_list')
   #
   cfg = pGMT5SAR.gmtsar_dir2batchcfg(iws,target_dir=topdir)
   #
   if cfg is None:
       print(" Progress: ERR-> no valid batch_config.cfg was found...")
       sys.exit(-1)
   #
   outfile = 'batch_config.cfg'
   #
   info = pGMT5SAR.gmtsar_batchcfg2info(cfg)
   #
   pGMT5SAR.gmtsar4batchconf(outfile,step=1,master=info['master_image'],\
           unwrap=unwrap_threshold,interp_flag = interp_flag,\
           flength=int(info['filter_wavelength']),\
           rlook=int(info['range_dec']),\
           azlook=int(info['azimuth_dec']))
   #
   print(" Progress: merge_batch_only.csh merge_list %s " % os.path.basename(cfg))
   goStr = 'merge_batch_only.csh merge_list %s' % os.path.basename(cfg)
   os.system(goStr)
   #
   #
   os.chdir(topdir)
