#!/usr/bin/env python
#
#
#
import pSAR
import os
import sys
import numpy as np
import glob
#
def linkfiles(cline,outdir):
    #
    tmp = cline.split(':')
    os.system('ln -s $PWD/%s* %s/. ' % (tmp[0],outdir))
    os.system('ln -s $PWD/%s* %s/. ' % (tmp[1],outdir))
    #
def grep_date_inDATAin(datain,refdate):
    #
    with open(datain,'r') as fid:
        #
        for cline in fid:
            #
            cline = cline.split('\n')[0]
            ids_date = cline.split(':')[0].split('-')[4]
            # print(ids_date)
            if refdate in ids_date:
                #
               return cline
            #
        #
    #
    return None
#
if len(sys.argv)<3:
    #
    helpstr = \
        '''
        %s <refdate> <target_date> -esd_mode [1 in default]
        ++++++++++++++++++++++++++++++++++++++++++++
        To estimate sub-pixel offsets of <target_date>.SLC relative to <refdate>.SLC
        this script should be run in the folder of F*/raw/
        
        In default, <refdate> is not optiamally the master, but close to <target_date>.
        So it is expected that the interferometric coherence between <refdate> and <target_date> is 
        good enough for offset estimation.
        
        -esd_mode 0, average
              1, median, in default
              2, interpolate


        <date>.refine_ashift.grd will be created and rSLC will be re-processed...

        by Wanpeng Feng, @SYSU, Guanghzou, 2022/02/12
        
        '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
    #
#
#
pSAR.util.log(sys.argv)
#
#
if __name__ == '__main__':
    #
    datain='data.in'
    #
    topdir = os.getcwd()
    #
    mode = 2 
    esd_mode = 1
    #
    #
    ref1 = sys.argv[1]
    ref2 = sys.argv[2]
    #
    for i,key in enumerate(sys.argv):
        #
        if key == '-esd_mode':
            esd_mode = int(sys.argv[i+1])
            #
        #
    #
    #
    mline = grep_date_inDATAin(datain,ref1)
    sline = grep_date_inDATAin(datain,ref2)
    #
    outdir = '%s_%s_REFINE' % (ref1,ref2)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        #
    #
    out_datain = '%s/data.in' % outdir
    if not os.path.exists(out_datain):
        #
        with open(out_datain,'w') as fid:
            #
            fid.write('%s\n' % mline)
            fid.write('%s\n' % sline)
            #
        #
    #
    out_dem = '%s/dem.grd' % outdir
    if not os.path.exists(out_dem):
        #
        # print(out_dem,os.path.abspath('../../topo/dem.grd'))
        os.system('ln -s %s %s' % (os.path.abspath('../../topo/dem.grd'),out_dem))
        #
    #
    #
    #
    linkfiles(mline,outdir)
    linkfiles(sline,outdir)
    #
    #
    #
    os.chdir(outdir)
    slcs = glob.glob('S*%s*ALL*.SLC' % ref2 )
    #
    if len(slcs)<1:
        #
        # gmtsar_preproc_batch_tops_esd.csh
        print(" gmtsar_preproc_batch_tops_esd.csh data.in dem.grd %d %d" % (mode,esd_mode))
        print(" +++++++++++++++++++++++++++++++++++++++++++++++++")

        os.system('gmtsar_preproc_batch_tops_esd.csh data.in dem.grd %d %d' % (mode,esd_mode))
        #
    #
    led = glob.glob('S*%s*ALL*.LED' % ref2 )
    #
    if len(led) > 0:
        cfile = os.path.abspath(led[0])
        rootfile = os.path.basename(led[0])
        #
        if os.path.exists('../%s' % rootfile):
            os.system('rm ../%s -f ' % rootfile)
        #
        os.system('ln -s %s ../%s' % (cfile,rootfile))
          # 
    #
    slc = glob.glob('S*%s*ALL*.SLC' % ref2 )
    #
    if len(slc) > 0:
        cfile = os.path.abspath(slc[0])
        rootfile = os.path.basename(slc[0])
        #
        if os.path.exists('../%s' % rootfile):
            os.system('rm ../%s -f ' % rootfile)
        #
        os.system('ln -s %s ../%s' % (cfile,rootfile))
    #
    prm = glob.glob('S*%s*ALL*.PRM' % ref2 )
    #
    #
    if len(prm) > 0:
        cfile = os.path.abspath(prm[0])
        rootfile = os.path.basename(prm[0])
        #
        # print(rootfile)
        if os.path.exists('../%s' % rootfile):
            os.system('rm ../%s -f ' % rootfile)
        #
        os.system('ln -s %s ../%s' % (cfile,rootfile))

    #
    master_slc = glob.glob('S*%s*ALL*.SLC' % ref1 )
    master_slc_basename = os.path.basename(master_slc[0])
    #
    if not os.path.exists('../%s' % master_slc_basename):
        #
        #
        master_slc_PRM = glob.glob('S*%s*ALL*.PRM' % ref1 )
        master_slc_LED = glob.glob('S*%s*ALL*.LED' % ref1 )
        #
        files = [master_slc[0],master_slc_PRM[0],master_slc_LED[0]]
        bnames= [os.path.basename(cfile) for cfile in files]
        abs_files = [os.path.abspath(cfile) for cfile in files]
        #
        #
        for i,cfile in enumerate(abs_files):
            #
            os.system('ln -s %s ../%s' % (cfile,bnames[i]))
            #
        #
    else:
        os.system('rm %s -f' % master_slc[0])
        #

    os.chdir(topdir)
    #
