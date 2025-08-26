#!/usr/bin/env python
#
#
import os
import sys
import numpy as np
import glob
def update(logfile,cdate):
    #
    os.system('echo %d >> %s' % (cdate,logfile))
    #
def doneORnot(logfile,cdate):
    #
    if not os.path.exists(logfile):
        return False
    #
    #
    dates = np.loadtxt(logfile)
    #
    index = np.where(dates==cdate)[0]
    if len(index)==0:
        return False
    else:
        return True
    #

def tiffs2dates(tiffs):
    #
    dates = np.array([int(ctiff.split('-')[4][0:8]) for ctiff in tiffs])
    return np.sort(dates)
#
if __name__ == '__main__':
    #
    logfile = 'rslc_refine.log'
    #
    print(" now start refining secondary SLCs by considering the close SLCs in order @ %s" % os.getcwd())
    #
    # in default, master.in should be ../../master.in
    #
    master_in = '../../master.in'
    #
    if not os.path.exists(master_in):
        print(" ERR: no master was found!!!")
        sys.exit(-1)
    #
    #
    master = np.loadtxt(master_in)
    master = int(master)
    #
    tiffs = glob.glob('s1*.tiff')

    #
    dates = tiffs2dates(tiffs)
    #
    mIndex = np.where(dates==master)[0]
    #
    print(" +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(" Now let's start working with s1TIFFs acquired before %d" % master)
    print(" +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #
    for i in range(mIndex[0]-1):
        #
        ci = 21-i
        flag = doneORnot(logfile,dates[ci-1])
        #
        if ci > 0 and not flag:
            #
            goStr = 'pSAR_gmtsar_refineESD.py %s %s' % (dates[ci],dates[ci-1])
            print(goStr)
  
            os.system(goStr)
            #
            update(logfile,dates[ci-1])          
            #
        #
    #
    print(" +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(" Now let's start working with s1TIFFs acquired after %d" % master)
    print(" +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    #
    for i in range(mIndex[0]+1,dates.shape[0]-1):
        #
        ci = i
        flag = doneORnot(logfile,dates[ci+1])
        if ci > 0 and not flag:
            #
            goStr = 'pSAR_gmtsar_refineESD.py %s %s' % (dates[ci],dates[ci+1])
            print(goStr)
            #
            os.system(goStr)
            update(logfile,dates[ci+1])

