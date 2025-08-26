#!/usr/bin/env python 
#
import os
import sys
import glob
import multiprocessing as mpg
#
def readtiffs(infile):
    #
    tiffs = []
    eofs = []
    with open(infile,'r') as fid:
        for cline in fid:
            tmp = cline.split('\n')[0]
            tmp = tmp.split(':')
            tiffs.append(tmp[0])
            eofs.append(tmp[1])
            #
            #
        #
    #
    return tiffs,eofs
#
def coreg_go(i):
    #
    goStr = 'pSAR_gmtsar_refineSLC.py %d %d -esd_mode %d' % (slc_master,slc_dates[i],esd_mode)
    os.system(goStr)
    print(goStr)
    #
    c_slc = glob.glob('S*%d*.SLC' % slc_dates[i])
    #
    if len(c_slc)<1:
        os.system(goStr)
        #
    #
    #
    #
    #
#

if True:
    #
    global slc_master, slc_dates, esd_mode
    #
    # esd_mode for coregistration
    #   0, average
    #   1, median
    #   2, interpolate
    #
    esd_mode = 1
    njob = 4
    #
    if len(sys.argv)>1:
        esd_mode = int(sys.argv[1])
        #
        #
    if len(sys.argv)>2:
        njob = int(sys.argv[2])
        #
    #
    #
    #
    infile = 'data.in'
    tiffs, eofs = readtiffs(infile)
    #
    slc_dates = [int(cfile.split('-')[4][0:8]) for cfile in tiffs]
    #
    # print(dates,eofs)
    #
    slc_master = slc_dates[0]
    #
    index = [i for i in range(1,len(slc_dates))]
    # print(index)
    #
    if not os.path.exists('dem.grd'):
        #
        # dempath = os.path.abspath('../../topo/dem.grd')
        #
        if os.path.exists('../../topo/dem.grd'):
            #
            demfile = os.path.abspath('../../topo/dem.grd')
            #
            os.system('ln -s %s .' % demfile)
        #
    #
    #
    pool = mpg.Pool(processes=njob)
    result = pool.map(coreg_go,index)
    pool.close()
    pool.join()
    #
    #
    master_slc = glob.glob('S*%d*ALL*.SLC' % slc_master)
    #
    if len(master_slc)<1:
        #
        slcs = glob.glob('*_REFINE/S*%d*ALL*.SLC' % slc_master)
        #
        if len(slcs)>0:
           target_slc = slcs[0]
           target_slc_path = os.path.abspath(os.path.dirname(slcs[0]))
           #
           print(target_slc_path)
           #
           for cfile in glob.glob(target_slc_path+'/S*%d*' % slc_master):
               if '.SLC' in cfile or \
                  '.PRM' in cfile or \
                  '.LED' in cfile:
                      #
                      os.system('ln -s %s . ' % cfile)
                      #

