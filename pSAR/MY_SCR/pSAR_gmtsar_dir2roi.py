#!/usr/bin/env python
#
#
# 
import shutil
import pGMT5SAR
import pSAR
import pS1
import os
import sys
import numpy as np
import glob
import pGMT
import matplotlib.pyplot as plt
#
def linkprmled(prms,baseline_dir):
    #
    for prm in prms:
        prm_path = os.path.dirname(os.path.abspath(prm))
        prm_basename = os.path.basename(prm).split('PRM')[0]
        target_prm = baseline_dir+'/'+prm_basename+'PRM'
        target_led = baseline_dir+'/'+prm_basename+'LED'
        if not os.path.exists(target_prm):
            os.system('rm %s -f' % target_prm)
            os.symlink(os.path.join(prm_path,prm_basename+'PRM'),target_prm)
        if not os.path.exists(target_led):
            os.system('rm %s -f' % target_led)
            os.symlink(os.path.join(prm_path,prm_basename+'LED'),target_led)
        #
    return True
#
def flist2path(inlist):
    #
    dpath = []
    with open(inlist,'r') as fid:
        dpath = fid.readline().split('intf_all')[0]
    return dpath     
#
#################################################################   
if len(sys.argv)<2:
    helpstr = \
        '''
        %s <outdir> -zipdir [a fullpath, None in default]
                    -prmFolder [None in default]
                    -model [merge, swath...]
                    -track [T000 in default, means nothing]
                    -gowrap [False in default]
                    -plot [False in default]
                    -amp [False in default]
        +++++++++++++++++++++++++++++++++++++++++++++++++++
        To convert GMTSAR results to ROI_PAC format with detailed 
        metadata information...
        
        by Wanpeng Feng, @SYSU, Guangzhou, 2020/04/19
        '''
    #
    print(helpstr % sys.argv[0])
    sys.exit(-1)
#
#
outdir    = sys.argv[1]
#
# when none is given, track will be read directly from zip file...
track     = None
model     = 'merge'
prmFolder = None
zipfolder = None
gowrap = False
plot = False
amp = False
#
for i,key in enumerate(sys.argv):
    #
    if key == '-amp':
        amp = True
    if key == '-plot':
        plot = True
    if key == '-gowrap':
        gowrap = True
    if key == '-prmFolder':
        prmFolder = sys.argv[i+1]
    if key == '-zipdir':
        zipfolder = sys.argv[i+1]
    if key == '-track':
        track = sys.argv[i+1]
#
topdir = os.getcwd()
if True:
    #
    outdir = os.path.abspath(outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        #
    #
    #
    ref_grd = 'unwrap_ll.grd'
    if not os.path.exists(ref_grd) and not gowrap:
        print(" ERR: no valid unwrapped grd was found in the folder...")
        sys.exit(-1)
    if not os.path.exists(ref_grd):
        ref_grd = 'corr_ll.grd'
    geoext = pGMT.gmt_grd2gext(ref_grd)
    gext = [float(cext) for cext in geoext.split('-R')[1].split('/')]
    roipoly = pSAR.roipac.ext2polygon(gext)
    roipoly[roipoly[:,0]>180,0] = roipoly[roipoly[:,0]>180,0] - 360.
    #
    # print(roipoly)
    #
    if prmFolder is None:
        tmplist = '../tmpm.filelist'
        prmFolder = flist2path(tmplist)
    #
    pairname = os.path.basename(os.getcwd())
    #
    prms = glob.glob(prmFolder+'/intf_all/'+pairname+'/S*ALL*.PRM')
    prms.sort()
    #
    if len(prms)==0:
        print(" ERR: no valid PRM was found!!!")
        sys.exit(-1) 
    # print(pairname,prmFolder,prms)
    dates = [os.path.basename(prm).split('_')[1] for prm in prms]
    #
    mdate = dates[0]
    sdate = dates[1]
    #
    print(" Process: cos-pair with %s and %s " % (mdate,sdate))
    #
    print( outdir+'/geo_'+mdate+'_'+sdate)
    outname = outdir+'/geo_'+mdate+'_'+sdate
    #
    # baseline info
    baseline_dir = 'baseline_dir'
    if not os.path.exists('baseline_dir'):
       os.makedirs(baseline_dir)
    #
    linkprmled(prms,baseline_dir)
    os.chdir(baseline_dir)
    cmd = 'baseline_table.csh %s %s ' % (os.path.basename(prms[0]),os.path.basename(prms[1]))
    #
    print(" Process: %s" % cmd)
    # info,flag,errors = pSAR.util.run(cmd)
    os.system("%s > baseline.dat " % cmd)
    _,info = pGMT5SAR.gmtsar_baseline('baseline.dat',mode=1)
    #
    if len(info)>=1:
       baseline = float(info[0,0])
    else:
       baseline = 0
    #
    os.chdir(topdir)
    #
    m_time = pGMT5SAR.prm2time(prms[0])
    s_time = pGMT5SAR.prm2time(prms[1])
    days   = pSAR.ts.diff2dates(mdate,sdate)
    # print(m_time,days)
    m_time_str = pSAR.ts.doy2time(m_time,fmt='%Y%jT%H:%M:%S.%f',of='%Y-%m-%dT%H:%M:%S.%fZ')
    s_time_str = pSAR.ts.doy2time(s_time,fmt='%Y%jT%H:%M:%S.%f',of='%Y-%m-%dT%H:%M:%S.%fZ')
    #
    # date need to be shifted forward by 1 day, a trick in GMTSAR processing chain
    #
    m_time_str = pSAR.ts.timeshift(m_time_str,1,fmt="%Y-%m-%dT%H:%M:%S.%fZ")
    s_time_str = pSAR.ts.timeshift(s_time_str,1,fmt="%Y-%m-%dT%H:%M:%S.%fZ")
    #
    minfo,keys = pSAR.roipac.roipac_info()
    minfo['MASTER'] = str(mdate)
    minfo['SLAVE'] = str(sdate)
    minfo['MTIME'] = m_time_str
    minfo['STIME'] = s_time_str
    minfo['PERPB'] = str(baseline)
    minfo['TEMPB'] = str(days)
    # 
    if zipfolder is not None and os.path.exists(zipfolder):
        #
        zips = glob.glob(zipfolder+'/S1*%s*.zip' % mdate)
        if len(zips)>0:
            track = pS1.s1zip2track(zips[0])
            aux = pS1.s1zip2aux(zips[0])
            xmlinfo, xmls = pS1.s1zip2swathxmlString(zips[0],pol='vv') 
            direction = pS1.s1swathxml2dir(xmlinfo[0],isfile=False)
            heading   = pS1.s1swathxml2heading(xmlinfo[0],isfile=False)
            wavelength = pS1.s1swathxml2wavelength(xmlinfo[0],isfile=False)
            minfo['HEADING_DEG'] = str(heading)
            minfo['WAVELENGTH']  = str(wavelength)
            minfo['TRACK'] = 'T%s' % track
            #
            xmlinfo = []
            for czip in zips:
                cxmls, xmls = pS1.s1zip2swathxmlString(czip,pol='vv')
                xmlinfo = xmlinfo + cxmls
            #
            for i,xml in enumerate(xmlinfo):
               incgrid = pS1.s1swathxml2incgrid(xml,isfile=False)       
               if i == 0:
                   allinc = incgrid
               else:
                  allinc = np.vstack([allinc,incgrid])
            #
            flag = pSAR.util.ptsINpolygon(roipoly,allinc)
            incs = allinc[flag,2]
            #
            if plot:
                plt.plot(allinc[:,0],allinc[:,1],'or')
                plt.plot(roipoly[:,0],roipoly[:,1],'-b')
                plt.show()
            #
            minfo['INCIDENCE'] = str(incs.mean())
            #
            outincpdf = outname+'_T'+track+'.global.inc.pdf'
            outincpng = outname+'_T'+track+'.global.inc.png'
            outincdat = os.path.dirname(outname)+'/T'+track+'.inc.dat'
            if not os.path.exists(outincdat):
              #
              np.savetxt(outincdat,allinc,fmt='%f %f %f',newline='\n')
            if os.path.exists(outincpdf):
              #
              plt.scatter(allinc[:,0],allinc[:,1],c=allinc[:,2])
              plt.plot(roipoly[:,0],roipoly[:,1],'-r',linewidth=3.5)
              #
              color_bar = plt.colorbar() #this one is a little bit
              color_bar.ax.set_ylabel('Incidence(degree)')
              #
              plt.savefig(outincpdf, dpi=720)
              plt.savefig(outincpng, dpi=720)
            #
            # print(len(xmlinfo),allinc.shape)
            #
    #
    # inc and azi grds
    #
    incazi = ['losvec.inc','losvec.azi']
    for cfile in incazi:
        #
        if os.path.exists(cfile):
            #
            ext = cfile.split('.')[1]
            cout = '%s/geo_T%s.%s' % (outdir,track,ext)
            if not os.path.exists(cout):
               shutil.copyfile(cfile,cout)
               shutil.copyfile(cfile+'.rsc',cout+'.rsc')
            #
            
            
    #
    for grd in glob.glob('*_ll.grd'):
       #
       #
       outroi = None
       if 'phasefilt' in grd and gowrap:
           outroi = outname+'_T'+track+'.wrap'
       elif 'unwrap_mask_ll' in grd:
           outroi = outname+'_T'+track+'.phs'
       elif 'unwrap_ll' in grd:
           outroi = outname+'_T'+track+'.phs'
       elif 'corr' in grd:
           #
           # change the extension of the coherence file to cc
           # by Wanpeng Feng, @SYSU, Guangzhou, 2020/05/31
           #
           print(outname)
           print(track)
           outroi = outname+'_T'+track+'.cc'
       elif 'amp' in grd:
           #
           # updated by FWP, @SYSU, 2021/12/24
           if amp:
              outroi = outname+'_T'+track+'.amp'
           else:
               continue
       else:
           continue
       #
       if not os.path.exists(outroi) and outroi is not None:
         #
         # modified by W. Feng, @SYSU, Guangzhou, 2024/01/20
         print(" Progress: converting %s to %s using a driver of gdal" % (grd,outroi))
         pGMT.gmt_grd2roi(grd,outroi,ginfo=minfo,refrsc=None,fmt='f',driver='gdal')
