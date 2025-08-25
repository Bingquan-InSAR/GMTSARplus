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
        %s <refdate> <target_date>
        ++++++++++++++++++++++++++++++++++++++++++++
        To estimate sub-pixel offsets of <target_date>.SLC relative to <refdate>.SLC
        this script should be run in the folder of F*/raw/
        
        In default, <refdate> is not optiamally the master, but close to <target_date>.
        So it is expected that the interferometric coherence between <refdate> and <target_date> is 
        good enough for offset estimation.

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
    #
    ref1 = sys.argv[1]
    ref2 = sys.argv[2]
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
        os.system('ln -s %s %s' % ('dem.grd',out_dem))
        #
    #
    #
    linkfiles(mline,outdir)
    linkfiles(sline,outdir)
    #
    #
    #
    os.chdir(outdir)
    target_shifts = glob.glob('S*_%s_*.update_ashift.grd' % ref2)
    #
    if len(target_shifts)<1:
        #
        print(" FWP_preproc_batch_tops_esd.csh data.in dem.grd 2 ")
        print(" +++++++++++++++++++++++++++++++++++++++++++++++++")
        os.system('FWP_preproc_batch_tops_esd.csh data.in dem.grd 2')
        #
        target_shifts = glob.glob('S*_%s_*.update_ashift.grd' % ref2)
    #
    # now update the sub pixel offsets based on the azimuth shift....
    ref_shifts =  glob.glob('%s/S*_%s_*.refine_ashift.grd' % (topdir,ref1))
    if len(ref_shifts)==0:
       ref_shifts =  glob.glob('%s/S*_%s_*.update_ashift.grd' % (topdir,ref1))
    #
    if len(ref_shifts)>0:
        #
        ref_shift = ref_shifts[0]
        target_shift = target_shifts[0]
        #
        update_shift = topdir+'/'+target_shift.split('update_ashift')[0]+'refine_ashift.grd'
        #
        # S*_*_F*.update_ashift.grd is the offsets relative to the super master...
        #
        goStr = 'gmt grd2xyz %s -bo3 > %s' % (target_shift,target_shift+'.xyz')
        print(goStr)
        os.system(goStr)
        #
        goStr = 'gmt surface %s -R%s -G%s -T0.25 -C0.0001 -bi3' % (target_shift+'.xyz',ref_shift,target_shift)
        print(goStr)
        os.system(goStr)
        #
        goStr = 'gmt grdmath %s %s ADD = %s' % (ref_shift,target_shift,update_shift)
        print(goStr)
        os.system(goStr)
        #
        goStr = 'gmt grd2xyz %s -bo3 > %s' % (update_shift,update_shift+'.xyz')
        #target_shift+'.xyz')
        print(goStr)
        os.system(goStr)
        #
        # S1_20190213_103021_F2.a_withoutESD.grd
        target_ashift = update_shift.split('refine_ashift')[0]+'a_withoutESD'+'.grd'
        #
        goStr = 'gmt surface %s -R%s -G%s -T0.25 -C0.0001 -bi3' % (update_shift+'.xyz',target_ashift,update_shift)
        print(goStr)
        os.system(goStr)
        #
    #
    os.chdir(topdir)
    #
    os.system('rm S*%s*.SLC -f' % ref2)
    #
    os.system('FWP_preproc_batch_tops_esd.csh data.in dem.grd 2')
    #
