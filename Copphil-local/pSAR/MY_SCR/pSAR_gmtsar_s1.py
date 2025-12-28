#!/usr/bin/env python


import datetime
import matplotlib
matplotlib.use('Svg')
import matplotlib.pyplot as plt
import multiprocessing as mp
import pSAR
import os,sys
import glob
import pS1
import numpy as np
import pGMT
import zipfile
import shutil
import subprocess
import pGMT5SAR
from shapely.geometry import Polygon

if 'LD_LIBRARY_PATH' in os.environ:
    del os.environ['LD_LIBRARY_PATH']
    print("LD_LIBRARY_PATH has been unset.")
else:
    print("LD_LIBRARY_PATH is not set.")
    
#
def repairlinks(czip):
    #
    s1dir = os.environ.get('S1DB')
    if not os.path.exists(czip):
      zipname = os.path.basename(czip)
      czip    = s1dir+'/%s' % zipname
    #
    return czip
    #
#
def intflist4pairinfo(pairlist):
    '''
    '''
    with open(pairlist,'r') as fid:
        tline = fid.readline()
        tmp = tline.split('\n')[0].split(':')
        master = tmp[0]
        slave  = tmp[1]
    #
    master_prm = os.path.join('raw','%s.PRM' % master)
    slave_prm  = os.path.join('raw','%s.PRM' % slave)
    #
    mtime = pGMT5SAR.prm2date(master_prm)
    stime = pGMT5SAR.prm2date(slave_prm)
    #
    # mtime = int(float(master_info['SC_clock_start']))
    # stime = int(float(slave_info['SC_clock_start']))
    #
    intf_dir = os.path.join('intf_all','%s_%s' % (mtime,stime))
    if os.path.exists(intf_dir):
       return True,intf_dir
    else:
       return False,intf_dir
    #
def rawdir2swathinfo(inraw,roi,master,pol,issave=True,plot=True,iniws=None):
    #
    ctopdir = os.getcwd()
    #
    iws = np.zeros(3)
    #
    #
    topdir = os.getcwd()
    #
    os.chdir(inraw)
    #
    polygons  = pSAR.roipac.ext2polygon(roi)
    refpolyID = Polygon(polygons)
    #
    if master is not None:
       zips = glob.glob('S1*%s*.SAFE' % master)
       refdate = master
       strmaster = "M%d" % master
    else:
       
       zips = glob.glob('S1*20**.SAFE')
       zips.sort()
       refdate = pS1.s1safe2date(zips[0])
       zips = glob.glob('S1*%s*.SAFE' % refdate)
       # 
       strmaster = "T%d" % int(zips[0].split('_')[5].split("T")[0])  
    #
    if not os.path.exists(zips[0]):
        zips[0] = repairlinks(zips[0])
        if not os.path.exists(zips[0]):
          print(" Process: a reference SAFE of %s is NOT available." % zips[0])
          sys.exit(-1)
    #
    track = pS1.s1safe2track(zips[0])
    outfig = os.path.join(topdir,'Fig_spatial_coverage_%s_T%s.pdf' % (strmaster,track))
    outfig_png = os.path.join(topdir,'Fig_spatial_coverage_%s_T%s.png' % (strmaster,track))
    #
    xmls = []
    xmlfiles = []
    for czip in zips:
        if not os.path.exists(czip):
          czip = repairlinks(czip)
        #
        xmlstr, xmlfile = pS1.s1safe2swathxmlString(czip,pol=pol)
        xmls.append(xmlstr)
        xmlfiles.append(xmlfile)
    # 
    label_counter_0 = 0
    label_counter_1 = 0 
    #
    dem_roi_lat = []
    dem_roi_lon = []
    #
    burstcounter = 0
    for i,cxml in enumerate(xmls):
        #
        # pS1.s1xmlupdate(cxml,outxml='_tmp')
        for j,xml in enumerate(cxml):
            xmlpolys = pS1.s1subswath2geopoly(xml,isfile=False)
            iwinfo = pS1.s1swathxml2iw(xml,isfile=False)
            #
            iwID = int(xmlfiles[i][j].split('-')[1][2:3])
            iwID = int(iwinfo[2:3])
            #
            # print(" Progress: working with %s in IW%d" % (xmlfiles[i][j],iwID))
            #
            counter = 0
            for k in range(len(xmlpolys)):
              #
              cpoly = xmlpolys[k]
              #
              if True:
                 if burstcounter == 0:
                    plt.plot(cpoly[:,0],cpoly[:,1],'-',color='gray',label='TOPS Bursts')
                    burstcounter += 1
                 else:
                    plt.plot(cpoly[:,0],cpoly[:,1],'-',color='gray')
                 #
                 plt.text(cpoly[:,0].mean(),cpoly[:,1].mean(),'IW%d_Burst%d' % (iwID,k))
              #
              _tmp_polyID = Polygon(cpoly)
              #
              if iniws is not None and iniws[iwID-1] == 0:
                 #
                 continue
              flag = refpolyID.intersects(_tmp_polyID)
              if flag:
                  dem_roi_lon.append([cpoly[:,0].min(),cpoly[:,0].max()])
                  dem_roi_lat.append([cpoly[:,1].min(),cpoly[:,1].max()])
                  if True:
                     if label_counter_1 == 0:
                        plt.plot(cpoly[:,0],cpoly[:,1],'-',color='blue',linewidth=2.5,label='Selected Bursts')
                     else:
                        plt.plot(cpoly[:,0],cpoly[:,1],'-',color='blue',linewidth=2.5)
                     #
                     plt.text(cpoly[:,0].mean(),cpoly[:,1].mean(),'IW%d_Burst%d' % (iwID,k),color='blue')
                     #
                     print("  *** Progress: working with %s in IW%d" % (xmlfiles[i][j],iwID))
                  counter += 1
                  label_counter_1 = label_counter_1+1
              #
              label_counter_0 = label_counter_0+1
            #
            if counter > 0:
                iws[iwID-1] = 1
        #
    # 
    plt.plot(polygons[:,0],polygons[:,1],'-r',label='ROI Region')
    #
    dem_roi_lat = np.array(dem_roi_lat)
    dem_roi_lon = np.array(dem_roi_lon)
    #
    dem_roi = [dem_roi_lon[:,0].min(),dem_roi_lon[:,1].max(),\
               dem_roi_lat[:,0].min(),dem_roi_lat[:,1].max()]
    dem_poly = pSAR.roipac.ext2polygon(dem_roi)
    #
    plt.plot(dem_poly[:,0],dem_poly[:,1],'-g',linewidth=10,label='DEM_coverage')
    #
    plt.legend()
    plt.xlabel('Lon(degree)')
    plt.ylabel('Lat(degree)')
    #
    fig = plt.gcf()
    fig.set_size_inches(14,10, forward=True)
    #
    if issave:
       plt.savefig(outfig,dpi=720)
       plt.savefig(outfig_png,dpi=720)
       #
    if plot:
       #
       plt.show()
    #
    plt.close(fig)
    #
    os.chdir(ctopdir)
    #
    return iws,dem_roi
    #
def pre_intf(intf,master=None):
    #
    outpair = []
    with open(intf,'r') as fid:
        for cline in fid:
            cline = cline.split('\n')[0]
            outpair.append(cline.split(':'))
    #
    if master is not None:
        k = 0 
        for i in range(len(outpair)):
            cprm = outpair[i][0]
            if str(int(master)) in cprm:
                k = i
                break
        #
        if k != 0:
            tmpprm = outpair[0]
            outpair[0] = outpair[k]
            outpair[i] = tmpprm
            #
        #
    return outpair
    #
def pre_pair2in(pairlist,master=None):
    #
    outinps = []
    for i in range(len(pairlist)):
       m_date = pairlist[i][0].split('_')[1]
       s_date = pairlist[i][1].split('_')[1]
       #
       if m_date != s_date:
         outinp = 'intf_%s_%s.inp' % (m_date,s_date)
         with open(outinp,'w') as fid:
            fid.write('%s:%s\n' % (pairlist[i][0],pairlist[i][1]))
         #
         outinps.append(outinp)
    #     
    return outinps
#
def intf_single(in_cmd):
    #
    pairlist = in_cmd.split()[1]
    flag,intf_dir = intflist4pairinfo(pairlist)
    # 
    if not flag:
       print( " Progress: %s " % in_cmd)
       os.system(in_cmd)
    else:
       print(" Progress: %s is ready!!!" % intf_dir)
    #
    # generating inc and azi file...
    # phasefilt_ll.grd
    lls = glob.glob('phasefilt_ll.grd')
    if len(lls)==0:
        lls = glob.glob('unwrap_ll.grd')
    #
    # updated by FWP, @SYSU, Zhuhai, to generate inc and azi files in the individual folders...
    #
    if len(lls)>0:
        goStr = 'pSAR_gmtsar_dir2losvecs.py'
        os.system(goStr)
        #
    #
    return True
#
def merge_prestamps(iws=[1,1,1],master=None):

    c = iws.count(1)
    topdir = os.getcwd()
    print(topdir)

    mode = None
    if iws == [1,1,1]:
       mode = 0
    elif iws == [1,1,0]:
       mode = 1
    elif iws == [0,1,1]:
       mode = 2
    else:
       mode = None
    dirs = ['F1','F2','F3']
    if os.path.exists('merge_stamps/ADIlist'):
       os.remove('merge_stamps/ADIlist')
    for i in range(3):
        if iws[i]<1:
            continue
        cdir = dirs[i]
        os.chdir('merge_stamps')
        if mode != None:
          #os.system(f'echo ../{cdir}/raw/S1_{master}_ALL_{cdir}.PRM:../{cdir}/raw/scatter_SM.grd >> ADIlist')
          first_dir = subprocess.getoutput(f'ls -d {topdir}/{cdir}/stamps/* | head -n 1')
          first_dir = os.path.basename(first_dir)
          os.system(f'echo ../../{cdir}/stamps/{first_dir}/tmp.PRM:../../{cdir}/raw/scatter_SM.grd >> ADIlist')
          #os.system(f'echo ../{cdir}/stamps/tmp.PRM:../{cdir}/raw/scatter_SM.grd >> ADIlist')
          os.chdir(topdir)
        else:
          shutil.copy(f'../{cdir}/raw/scatter_SM.grd','scatter_SM.grd')
          os.chdir(topdir)

    print(mode)
    print(iws)
    print(master)
    for i in range(3):
        if iws[i]<1:
            continue
        cdir = dirs[i]
        os.system(f'mergeforstamps.csh {mode} {cdir} {master} {adi} {patch_r} {patch_a} {overlap_r} {overlap_a} ')
        break
    return 
    
    
def run_inf_ps(cfg='batch_config.cfg',njob=2,intf='intf.in',iws=[1,1,1],master=None):

    topdir = os.getcwd()
    dirs = ['F1','F2','F3']
    for i in range(3):
        if iws[i]<1:
            continue
        cdir = dirs[i]
        #
        os.chdir(cdir)
        os.system('intf_tops_ps.csh intf.in batch_config_ps.cfg')
        print("Interferograms have been generated")
        
        os.chdir(topdir+'/'+cdir+'/raw')  
        os.system('ls -1 *ALL_*.PRM --ignore="PRM.list*" > PRM.list')
        
        print(f'dispersion.csh PRM.list scatter_SM.grd {master} {cdir}')
        os.system(f'dispersion.csh PRM.list scatter_SM.grd {master} {cdir}')
        os.chdir(topdir)
    #
    return True        
            
def run_inf(cfg='batch_config.cfg',njob=2,intf='intf.in',iws=[1,1,1],master=None,\
        method='snaphu',snaphu_alg='MST',alpha=0.8,fftsize=32):
    '''
    
    method, unwrapping method, fls or snaphu
    '''
    #
    topdir = os.getcwd()
    #
    dirs = ['F1','F2','F3']
    for i in range(3):
        if iws[i]<1:
            continue
        #
        cdir = dirs[i]
        #
        os.chdir(cdir)
        #
        

        pairs = pre_intf(intf,master=master)
        #
        #
        if not os.path.exists('inp_copy_dir'):
           outinps = pre_pair2in(pairs,master=master)
        else:
           outinps = glob.glob('inp_copy_dir/intf*.inp')
           if len(outinps)==0:
               print(" Warning: no valid inps were found in inp_copy_dir!!")
               outinps = pre_pair2in(pairs,master=master)
           else:
               for cinp in outinps:
                   #
                   goStr = 'cp %s .' % cinp
                   os.system(goStr)
        # 
        tmpdir = os.getcwd()
        #
        script = topdir+'/proj_ra2ll_iw%d.info.sh' % (i+1)
        #
        goStr = 'gmtsar_intf_tops.csh %s %s %s %s %s %f %d' % (outinps[0],cfg,script,method,snaphu_alg,alpha,fftsize)
        flag,intf_dir = intflist4pairinfo(outinps[0])
        #
        if not flag:
           print(" Progress: %s in %s" % (goStr,cdir))
           os.system(goStr)
        else:
           print(" Progress: %s is ready. Nothing to do with it!!!" % intf_dir)
        #
        m_cmds = ['gmtsar_intf_tops_notopo.csh %s %s %s %s %s %f %d' % (cinp,cfg,script,method,snaphu_alg, alpha,fftsize) for cinp in outinps[1::]]
        cpool = mp.Pool(processes=njob)
        results = cpool.map(intf_single, m_cmds)
        cpool.close()
        cpool.join()
        #
        os.chdir('intf_all')
        incfile = glob.glob('*/losvec.inc')
        if len(incfile)<1:
            tmpdirs = glob.glob('2*_*/')
            os.chdir(tmpdirs[0])
            goStr = 'pSAR_gmtsar_dir2losvecs.py'
            os.system(goStr)
        #
        os.chdir(topdir)
    #
    return True
def s1rawinroi(roi,iws=[1,1,1]):
    '''
    '''
    #
    raws = ['F1/raw','F2/raw','F3/raw']
    polygons = pSAR.roipac.ext2polygon(roi)
    #
    for cdir in raws:
        #
        xmls = glob.glob(os.path.join(cdir,'s1*.xml'))
        print(xmls)
    return True
#
def safedir2master(indir,iws=None):
    '''
      This function is sensitive to the path. 
      So we need to make sure to run the function in the topfolder....
      #
      pSAR_gmtsar_rawdir2prms.py
      pSAR_gmtsar_raw2baseline.py
    '''
    #
    safes = glob.glob(os.path.join(indir,'*.SAFE/'))
    # 
    tmplist = []
    for cline in safes:
        if 'NaNT00' not in cline and '_T_' not in cline:
            tmplist.append(cline)
        else:
            if os.path.exists(cline):
                os.system('rm -r %s' % cline)
            #
    safes = tmplist
    # 
    names = [os.path.basename(os.path.dirname(csafedir)) for csafedir in safes]
    dates = np.array([cname.split('_')[5][0:8] for cname in names])
    fdates = np.array([pSAR.ts.yyyymmdd2jd(cdate) for cdate in dates])
    meand = fdates.mean()
    diffd = np.abs(fdates-meand)
    # 
    # print(safes,diffd)
    master = dates[diffd==diffd.min()]    
    #
    #
    ctopdir = os.getcwd()
    #
    os.chdir(os.path.abspath(indir))
    #
    if not os.path.exists('tmpPRM_DIR/baseline_table.dat'):
      #
      refiws = 1
      if iws is not None:
          iws = np.array(iws)
          index = np.where(iws!=0)[0]
          refiws = index[0]+1
          #
      os.system('pSAR_gmtsar_rawdir2prms.py %s' % refiws)
      os.chdir('tmpPRM_DIR/')
      os.system('pSAR_gmtsar_raw2baseline.py ')
      os.chdir('../')
    #
    if os.path.exists('tmpPRM_DIR/baseline_table.dat'):
        os.system('cat tmpPRM_DIR/baseline_table.dat ')
        #
        _,tmaster = pGMT5SAR.gmtsar_baseline2master('tmpPRM_DIR/baseline_table.dat',mode=2)
        # print(master)
    if tmaster is not None:
       master = tmaster
    #
    os.chdir(ctopdir)
    #
    if isinstance(master,int):
        return master
    else:
        return master[0]
#
def read_datain(indatain):
    #
    with open(indatain,'r') as fid:
         cline = fid.readline()
    #
    return cline.split(':')[0].split('-')[4][0:8]

#
def dir2infcfg(outcfg,step=1,iws=[1,1,1],master=None,unwrap=0.1,switch_land=0,\
              toposhift=0,flength=200,rlook=8,azlook=2,interp_flag=0):
    #
    
    topdir = os.getcwd()
    fdirs = ['F1','F2','F3']
    #
    datain = 'raw/data.in'

    for i in range(3):
        #
        if iws[i]<1:
            continue

        #
        cdir = fdirs[i]
        #
        os.chdir(cdir)
        #
        if os.path.exists(datain) and master is None:
           master = read_datain(datain)
        #
        PRM = glob.glob('raw/*%s*ALL*.PRM' % master)
        PRM = os.path.basename(PRM[0]).split('.PRM')[0]
        #
        pGMT5SAR.gmtsar4batchconf(outcfg,toposhift=toposhift,step=step,master=PRM,\
                flength=flength,rlook=rlook,azlook=azlook,\
                interp_flag=interp_flag, unwrap=unwrap,switch_land=switch_land)
        #
        os.chdir(topdir)
    #
    return True

def prefolders4inf(iws):
    '''
    '''
    topdir = os.getcwd()
    fdirs = ['F1','F2','F3']
    demgrd = glob.glob('topo/dem.grd')
    if len(demgrd) < 1:
        print(" ERROR: DEM grd is not ready!!!")
        return False
    demgrd = os.path.abspath(demgrd[0])
    #
    for i in range(3):
        if iws[i] < 1:
            continue
        #
        cdir = fdirs[i]
        #
        cdemdir = os.path.join(cdir,'topo')
        if not os.path.exists(cdemdir):
            os.makedirs(cdemdir)
        #
        target_dem = os.path.join(cdemdir,'dem.grd')
        if not os.path.exists(target_dem):
            if os.path.islink(target_dem):
               os.system('rm -f %s' % target_dem)
            #
            os.symlink(demgrd,target_dem)
        #
    return True

def fdirs2infpairs(tmpbase,master,sbase,iws,ps=None,mylist=None,update=False,minnum=3,season=None):

    topdir = os.getcwd()
    #
    for i in range(3):
        if iws[i]<1:
            continue
        #
        cdir = 'F%d/raw' % (i+1)
        #
        cdir_dir = os.path.dirname(cdir)
        os.chdir(cdir_dir)
        if not os.path.exists('intf.in') or update:
           #
           # pSAR_gmtsar_baseline2intfin.py baseline_table.dat test.in 48 200
           if season is None:
              goStr = 'pSAR_gmtsar_baseline2intfin.py baseline_table.dat intf.in %f %f -minnum %d -master %s -method %s' % (tmpbase,sbase,minnum,master,method)
           else:
              goStr = 'pSAR_gmtsar_baseline2intfin.py baseline_table.dat intf.in %f %f -minnum %d -season %d -master %s -method %s' % (tmpbase,sbase,minnum,season,master,method)
           #
           print(" ++++++++++++++++++++++++++++++++++++++++++")
           print(" Progress: %s in %s" % (goStr,os.getcwd()))
           os.system(goStr)
           #
           #
        #
        if mylist is not None:
            #
            #
            #
            for j in range(len(mylist)):
                cmdate = mylist[j][0]
                csdate = mylist[j][1]
                #
                os.system('grep %s intf.in|grep %s >> intf_selected.in' % (cmdate,csdate))
            #
            if os.path.exists('intf_selected.in'):
                os.system('mv intf_selected.in intf.in')
        #
        os.chdir(topdir)
    #
    return True

def raw2baseline(iws,master=None,update=False):
    #
    topdir = os.getcwd()
    #
    for i in range(3):
        if iws[i]<1:
            continue
        #
        cdir = 'F%d/raw' % (i+1)
        cdir = os.path.abspath(cdir)
        os.chdir(cdir)
        #
        goStr = 'pSAR_gmtsar_dir2baseline.py %s' % master
        #
        if not os.path.exists('baseline_table.dat') or update:
           print(" Processes: %s in F%d" % (goStr,(i+1)))
           os.system(goStr)
        #
        os.chdir(os.path.dirname(cdir))
        #
        goPlot = 'pSAR_baseline.py baseline_table.dat -gmtsar -noplot'
        print(" Processes: %s in F%d" % (goPlot,(i+1)))
        os.system(goPlot)
        #
        os.chdir(topdir)
    return True
#
def unzip2raw(dates,raw_full,topdir,orbmodel):
    #
    for cdate in dates:
            #
            
            if len(glob.glob(raw_full+'/S1*%s*.SAFE/' % cdate)) > 0:
                continue
            
            tmp_dirs = glob.glob('S1*%s*.SAFE' % cdate)
            tmp_dirs.sort()
            #
            # print(cdate,tmp_dirs)
            # print(os.getcwd())
            # sys.exit(-1)
            inmanifest = []

            if len(tmp_dirs)>0:
               cmanifest = glob.glob(tmp_dirs[0]+'/manifest.safe')
               if len(cmanifest) < 1:
                  print(" Warning: no manifest.safe was found in %s" % tmp_dirs[0])
                  continue
               else:
                  inmanifest = cmanifest[0]
                   #
            #
            # updated by FWP, orbfile name should be read directly from safe...
            #
            print(" Progress: finding the orbit files for each acquisition, with model (%s)" % orbmodel)
            #
            if os.path.exists(tmp_dirs[0]):
               print(" Finding Orb: %s" % (tmp_dirs[0]))

               orb,flag = pS1.s1dir2orb(tmp_dirs[0],cdate,orbdir=None,model=orbmodel.upper())
               #
            else:
               continue
               #
            if not flag:
               print(" Progress: No valid EOF found in %s. Trying RESORB mode now..." % orbmodel.upper())
               orbmodel = 'RESORB'
               cmanifest = glob.glob(tmp_dirs[0]+'/manifest.safe')
               orb = s1manifest2orb(inmanifest,model=orbmodel)
               # orb,flag = pS1.s1dir2orb(tmp_dirs[0],orbdir=None,model='RESORB')
               print("%s->%s" % (tmp_dirs[0],orb))
            if not flag:
               print(" Progress: ERROR!!! not EOF found for %s" % tmp_dirs[0])
               #sys.exit(-1)
            #
            flight_dir = pS1.s1manifest2dir(cmanifest[0],isfile=True)
            #
            if flight_dir == 'ASCENDING':
                p1 = [roi[0],roi[2]]
                p2 = [roi[1],roi[3]]
            else:
                p1 = [roi[1],roi[3]]
                p2 = [roi[0],roi[2]]
            #
            twopinll = '%s_twopins.ll' % cdate
            s1cutllt(twopinll,p1,p2)
            safelist_file = 'SAFE_filelist_%s' % cdate
            s1cutsafelist(safelist_file,tmp_dirs,roi=roi,pol=pol)
            #
            goStr = 'GMTSAR_s1_createTOPSframes_burst.csh %s %s %s 1 %s' % \
                    (safelist_file,orb,twopinll,raw_full)
            os.system('echo "%s" > GMTSAR_s1_createTOPSframes_burst.csh.log' % goStr)
            print(goStr)
            cutID = os.system(" %s >> %s.log " % (goStr,safelist_file) )
            print(" Progress: cutting S1 data with an output of %d" % cutID)
            #
            #
    os.chdir(topdir)

def raw2slcs(iws,rslc_refine=False,njob=4,esd_mode=1):
    '''
    '''
    topdir = os.getcwd()
    #
    for i in range(3):
        #
        if iws[i]<1:
            continue
        #
        cdir = 'F%d/raw' % (i+1)
        os.chdir(cdir)
        #
        dirs = glob.glob('*.tiff')
        slcs = glob.glob('*.SLC')
        #
        if len(dirs) == len(slcs) and not rslc_refine:
           os.chdir(topdir)
           continue
        #
        # topo.llt
        inllt = 'topo.llt'
        topo_llt = glob.glob('%s/F*/raw/%s' % (topdir,inllt))
        #
        if len(topo_llt)>0 and not os.path.exists(inllt):
            #
            if os.path.islink(inllt):
                os.system('rm -rf %s' % inllt)
            #
            cllt = os.path.abspath(topo_llt[0])
            #
            os.symlink(cllt,inllt)
        #
        # goStr = 'FWP_preproc_batch_tops_esd.csh data.in ../../topo/dem.grd 2'
        #
        goStr = 'pSAR_gmtsar_tiff2slcs_paral.py %d %d' % (esd_mode,njob)
        
        #
        if noesd:
            goStr = 'FWP_preproc_batch_tops_NOesd.csh data.in ../../topo/dem.grd 2'
        #
        #
        print(" Progress: working in %s" % cdir)
        print(" Progress: %s" % goStr)
        os.system(goStr)

        #
        # added by Wanpeng Feng, @SYSU, Guangzhou, 2022/02/12
        if rslc_refine:
            # once the flag rslc_refine is open, we re-do co-registration by only consider the offsets between neighbours...
            #
            print(" ")
            print(" pGMTSAR: refine rSLCs by close looking at the neighbours...")
            print(" ")
            os.system('pSAR_gmtsar_dir2refineSLCs.py')
            #
        #
        os.chdir(topdir)
    #
    print(" *** FWP checker for rslc_refine DONE!!! ***")
    #
    #
    print(" Progress: Hope all SLCs are already OK for interferometry!!!")
    return True

def clean_dir(iws):
    #
    for i in range(3):
        if iws[i]<0:
            continue
        #
        # updated by FWP, @SYSU, 2020/09/15
        # in Mac system, -f cannot be applied at the end of rm or cp commond lines...
        #
        os.system('rm -f F%d/*/*.SLC' % (i+1))
        os.system('rm -f F%d/intf/*/real*.grd' % (i+1))
    os.system('rm %s/ -r' % datadir)
    os.system('rm %s/ -r' % rawdir)
    #
    return True
#
def read_list(in_list):
    #
    mylist = []
    if in_list is not None and os.path.exists(in_list):
        with open(in_list,'r') as fid:
            for cline in fid:
                cline = cline.split('\n')[0]
                tmp = cline.split()
                mylist.append([tmp[0],tmp[1]])
        #
        # mylist = np.array(mylist)
    else:
        mylist = None
    #
    return mylist
#
def pairYESorNO(mylist,mt1,mt2):
    #
    flag = False
    if mylist is None:
       return True
    #
    for i in range(len(mylist)):
        #
        if (int(mt1) == int(mylist[i][0])) and (int(mt2) == int(mylist[i][1])):
           #
           flag = True
           break
        #
    return flag
#
def s1inf_linkdem(infolder,outfolder):
    #
    for cfile in glob.glob(infolder+'/dem*.*'):
        #
        cfile = os.path.abspath(cfile)
        cfile_name = os.path.basename(cfile)
        if not os.path.exists(outfolder+'/'+cfile_name):
            os.symlink(cfile,outfolder+'/'+cfile_name)
        #
    return True
#
def s1inf_link(inmanifest,outdir):
    #
    fullpath_s1 = os.path.abspath(os.path.dirname(inmanifest))
    s1_dirname = os.path.basename(fullpath_s1)
    if not os.path.exists(outdir+'/'+s1_dirname):
       os.symlink(fullpath_s1, outdir+'/'+s1_dirname)
    return True
#
def s1cutsafelist(outfile,safelist,roi=None,pol='vv'):
    #
    #
    flag = True
    with open(outfile,'w') as fid:
        for clist in safelist:
            #
            if roi is not None:
               flag,_ = pS1.s1dir_burstinROI(clist,roi,pol=pol)
            if flag:
               fid.write('%s\n' % os.path.abspath(clist))
    #
    return True
#
def s1cutllt(outfile,p1,p2):
    #
    with open(outfile,'w') as fid:
        fid.write('%f %f\n' % (p1[0],p1[1]))
        fid.write('%f %f\n' % (p2[0],p2[1]))
    return True
#
def s1cutwithroi(indirs,orb,outdir,flight_dir,roi):
    #
    
    #
    return False    
def s1manifest2orb(in_manifest,model='RESORB'):
    #
    orbfile = pS1.s1safe2statevector(in_manifest,model=model)
    #
    if not os.path.exists(orbfile):
      startTime,stopTime = pS1.s1manifest2Tcoverage(in_manifests)
      go_getORB = 'pSAR_grabS1orb.py %s %s -mission S1%s' % (startTime,stopTime,mission1)
      os.system(go_getORB)
    if os.path.exists(orbfile):
      orb_bname = os.path.basename(orbfile)
      if not os.path.exists(orb_bname):
          os.symlink(orbfile,orb_bname)
      #
      return orb_bname
    else:
      return None
#######################################    
def s1dir2dates(in_s1dir_list):
    #
    return [os.path.basename(cdir).split('_')[5][0:8] for cdir in in_s1dir_list]
#######################################
def checkrawdir():
    #
    for cdir in glob.glob('raw/S*.SAFE/'):
        if "NaNT000000" in cdir:
            os.system('rm %s -r' % cdir)
        if "T_T_" in cdir:
            os.system('rm %s -r' % cdir)
    #

#
topdir = os.getcwd()
#
if len(sys.argv)<3:
  helpstr = \
  '''
  +++++++++++++++++++++++++++++++++++
  %s -roi [none in default, or in lonmin,lonmax,latmin,matmax ] 
     -s1dir [] 
     -dem [dem.grd, a full path required] 
     -orbmodel [RESORB in default] 
     -maxtimeint [128 days in default]
     -list [None in default]
     -ueof [will be open in default]
     -nozip2orb [once it is set open, no pSAR_s1zips2orb.py is run.]
     -clean
     -i       0 in default, i or interp_flag 
     -njob    [4 in default]
     -pol     [vv in default] 
     -iws     [None in default]
     -unwrap_0 [0.01 in default for individual swath unwrapping setting]
     -swathplot [False in default]
     -flength [None, in default]
     -rlook [8 in default]
     -azlook [2 in default]
     -roidir [None in default, a output folder for output ROI]
     -unwrap_alg [fls or snaphu, snaphu in default]
     -minnum [3 in default]
     -noesd [flag for coregistration without ESD, false in default]
     -season [None in default, if given, data in a similar season will be allowed for interferometry]
     -sd [Starting Date, a parameter to use for filtering SAR data, 19991001 in default]
     -ed [Ending Date, a parameter to use for filtering SAR data, 20901001 in default]
     -switch_land [0 in default, 1 for masking water body out]
     -alpha [0.8 in default] strenght of power filtering of phasefilt
     -fftsize [64 in default], fftiszie of power filtering of phasefilt
     -snaphu_alg [MCF or MST, MST in default]
     -dem_source [COP30M or SRTM, COP30M in default]
     -esd_mode [0,1 or 2]
     -
  +++++++++++++++++++++++++++++++++++
  To do interferomery with Sentinel-1 TOPS data by using GMT5SAR
  starting from a given folder having Sentinel-1A/B zip files and dem grd file. 

  Optional parameters:
  -esd_mode methods for offsets estimation for the overlap region
           0 for average
           1 for median, in default
           2 for interpolate

  -i       if an interpolation is required prior to unwrapping, 0 in default, which means NO interpolation.
  -orbmodel 'resorb' or 'poeorb'
  -tmpbase temporal baseline, 100 days in default
  -method  [sbas|msbas|stamps]
  -list    optional, a list having pair time information
  -ueof    optional, update eof(s) if given, True in default...
  -clean   optional, to remove *.SLC and real*.grd to save space of the working folder.
  -njob    4 in default, multiple tasks will be run in the same time... parallel (gnu) should be provided...
  -master  None in default, YYYYMMDD will be only format that is support in this script.
           If not given, the middle image will be suggested to use...
  -pol     polarization band option, in default, vv is pre-set...
  -iws     None default. if roi is given, iws will be estimated automatically based on roi polygon. Only overlapping swaths will be processed.
           e.g. 1,1,1 means to process all three swaths...
           Note if you have more than 3 swaths for some areas, we must go back here to update the script...
  -unwrap_0 threshold for individual swaths... in default, unwrapping...
  -unwrap_1 threshold for merged interferograms, in default, 0.15 will be set...
  *
  -flength  filtering length, 200 in default
            The output resolution will be calculated approximatedly by <flength>/4
            
  -rlook    multilooking size in range, 8 in default
  -azlook   multilooking size in azimuth, 2 in default
  -update   False in default. If given, update will be reset to be True
  -st       starting step, in default 0
            st<=1 building dem for insar
            st<=2 unzip S1*.zip to the given folder ...
            ...
  -et       ending step, in default xxx
            Details of steps applied in the processing:
              step 0: link dem into the local folder
              step 1: link zip into the local folder
              step 2: unzip S1*.zip in the local folder
              ...
  -demonly  flag to create dem only, False in default
  -datadir  path for unzipping and burst cutting... DATA/ is in default.
  -rawdir   path for cutted S1 data, raw/ in default.
  -topodir  path for srtm dem data, topo/ in default.
  -zipcheck optional, 0 for no check, 1 for yes...
  -season         optional, 12,24,36... days
  -toposhift      0 in default
  -rslc_refine    False in default
  -adi            0.35 in default
  -patch          2 and 3 in default
  -overlap        50 and 200 in default
  #
  Data orbit data in RESORB model will be collected automatically based on the data temporal coverage.
  In default, three swaths will be processed separately in F1, F2 and F3 three subfolders.
  
  
   
  first developed by Wanpeng Feng, @CCRS/NRCan, 2018-05-16
  
  + an almost new version was ready to handle data cropping 
  Updated by FWP, @SYSU, Guangzhou, 2020/01/01
  + 
  + a list file can be allowed since this version.
  + if a list is given, only specific pairs are processed.
  Updated by FWP, @SYSU, Guangzhou, 2020/01/04

  +ueof should be always set as True for a more robust automation...

  **** NOTICE ******
  A bug was found in the version before 2020/02/13
  previously, manifest(s) were roughly sorted with <list>.sort()
  so for those with S1A and S1B pair, S1A acquisition will also be processed first...
  This is certainly wrong. Since this version(2020/02/13), pS1.s1manifestsort()
  is used to sort manifest(s) by date only...
  
  Updated by FWP, @SYSU, Guangzhou, 2020/02/13
  -roidir a path for output, if give, results will be sent to <roi_dir> in ROI_PAC format...
          None in default.
  #
  Updated by FWP, @SYSU, Guangzhou, 2020/05/28
  #
  since this version, the step control has been applied, which allow to redo specific steps without repeating other steps before
  This could be very useful if the origianl unzipped SLCs are too huge. This will allow users to save some space...

  Updated by FWP, @SYSU, Guangzhou, 2020/07/29
  #
  + Two improvements were made in this version:
    1) dem is not necessary to be given during the processing. The latest version will make dem data automatically based on the SLC data.
    2) re-set ROI to make selected bursts in adjacent swaths to look identical in height.
    3) we can modify iws.in, which can help re-organize the bursts that are required to process.
  Updated by FWP, @SYSU, Guangzhou, 2020/08/10
  # 
  Updated by FWP, @SYSU, Guangzhou, 2021/01/03
  + 
      -datadir is available since this version, which is temporarily used to store zip and unzipped S1 data.
      -rawdir  is available since this version, which is temporarily used to store cutted S1 data.
      -topodir is available since this version, which is temporarily used to store dem data.

  Updated by FWP, @SYSU, Zhuhai, 2021/01/07
  + 
      -zipcheck optional for pre-check on whether the input zip is legal... which could be time consuming...
                0 in default, which means no check is conducted.
  
  Updated by FWP, @SYSU, Guangzhou, 2021/01/19
      -nozip2orb, once this is open, it is not in default to run pSAR_s1zips2orb.py 
  
  Updated by FWP, @SYSU, Guangzhou, 2021/02/23
      -unwrap_alg, a new parameter to specify the unwrapping algorithm applied in the processing.
                   snaphu and fls can be optionally selected for use during unwrapping. snaphu is set in default.
                   Meanwhile, since this version, the data gap of non data in phase.grd will be interpolated using gdal_fillnodata.py
  
  Updated by FWP, @SYSU, Guangzhou, 2021/03/03
      -flength, filter length defined based on azlook in default
      -minnum,  minimum number of interferograms from an individual master date
  
  Updated by FWP, @SYSU, Guangzhou, 2021/07/31
      "inp_copy_dir" can be pre-set in F<x> to store potential processed pairs. If "in_copy_dir" exists and it is NOT empty, the inps inside will be copied out and start running gmtsar processing for those pairs only.
      Note that the folder of "inp_copy_dir" could be generated beforehand of the pSAR_gmtsar_s1.py by running pSAR_gmtsar_inlist2INTFinp.py, which will detect in.list in F<x> folder(s).
  
  Updated by FWP, @SYSU, Guangzhou, 2021/08/24
     -noesd available to switch to non-esd coregistration mode

  ---
  Updated by Wanpeng Feng, @SYSU, Guangzhou, 2021/09/14
     -swith_land available since this version...
  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  '''
  if '-help' in sys.argv:
     print(helpstr % (sys.argv[0]))
  else:
     helpstr = \
          '''
          %s -roi <> -s1dir <> -rlook [8] -azlook [2] -unwrap_alg [snaphu] -roidir []

          --
          try %s -help for complete help information.

          '''
     print(helpstr % (sys.argv[0],sys.argv[0]))

  sys.exit(-1)
#
#
esd_mode = 1
dem_source = 'COP30M'
#
# filtering, 200 in default
switch_land = 0
flength = None 
season = None
# multilooking
snaphu_alg = 'MCF'
rlook  = 8
azlook = 2
et     = 999999
st     = 0 
interp_flag = 0 
#
sd = '19991001'
ed = '20901001'
#
noesd = False
swathplot    = False
#
unwrap_alg   = 'snaphu'
unwrap_0     = None 
unwrap_1     = 0.05
iws          = None
pol          = 'vv'
master       = None
njob         = 1
tmpbase      = 180 
sbase        = 200
batch        = True 
maxtimeint   = 128
orbmodel     = "POEORB" #"POEORB"
dem          = None
roi          = None
s1dir        = None
unzip_n_cpus = 4
#
# filtering
#
alpha = 0.8
fftsize = 32
inlist       = None
mylist       = None
isclean      = False
# update eof(s)
ueof         = False 
roidir       = None
#
demonly      = False
update       = False
datadir      = 'DATA/'
rawdir       = 'raw/'
topodir      = 'topo/'
zipcheck     = 0
minnum       = 3
toposhift    = 1 
rslc_refine  = False
method = None
adi = 0.35
patch_r = 2
patch_a = 3
overlap_r = 50
overlap_a = 200
#
for i,key in enumerate(sys.argv):
    #
    if key == '-esd_mode':
        esd_mode = int(sys.argv[i+1])
        #
    if key == '-dem_source':
        dem_source = sys.argv[i+1]
        #
    if key == '-alpha':
        alpha = float(sys.argv[i+1])
        #
    if key == '-fftsize':
        fftsize = int(sys.argv[i+1])
        #
    #
    if key == '-rslc_refine':
        rslc_refine = True
        #
    if key == '-toposhift':
        toposhift=1
    if key == '-snaphu_alg':
        snaphu_alg = sys.argv[i+1]
    if key == '-switch_land':
        switch_land = int(sys.argv[i+1])
    if key == '-sd':
        sd = sys.argv[i+1]
    if key == '-ed':
        ed = sys.argv[i+1]
    if key == '-season':
        season = int(sys.argv[i+1])
    if key == '-noesd':
        noesd = True
    if key == '-minnum':
        minnum = int(sys.argv[i+1])
    if key == '-unwrap_alg':
        unwrap_alg = sys.argv[i+1]
    if key == '-nozip2orb':
        ueof = False
    if key == '-zipcheck':
        zipcheck = int(sys.argv[i+1])
    if key == '-rawdir':
        rawdir = sys.argv[i+1]
    if key == '-topodir':
        topodir = sys.argv[i+1]
    if key == '-datadir':
        datadir = sys.argv[i+1]
    if key == '-i':
        interp_flag = int(sys.argv[i+1]) 
    if key == '-demonly':
        demonly = True
    if key == '-st':
        st = int(sys.argv[i+1])
    if key == '-et':
        et = int(sys.argv[i+1])
    if key == '-roidir':
        roidir = sys.argv[i+1]
    if key == '-update':
        update = True
    if key == '-flength':
        flength = int(sys.argv[i+1])
    if key == '-rlook':
        rlook = int(sys.argv[i+1])
    if key == '-azlook':
        azlook = int(sys.argv[i+1])
    if key == '-orbmodel':
        orbmodel = sys.argv[i+1]
    if key == '-unwrap_1':
        unwrap_1 = float(sys.argv[i+1])
    if key == '-swathplot':
       swathplot = True
    if key == '-unwrap_0':
       unwrap_0 = float(sys.argv[i+1])
    if key == '-iws':
        iws = [float(ciw) for ciw in sys.argv[i+1].split(',')]
    if key == '-master':
        master = int(sys.argv[i+1])
    if key == '-njob':
        njob = int(sys.argv[i+1])
    if key == '-tmpbase':
        tmpbase = float(sys.argv[i+1])
    if key == '-method':
        method = sys.argv[i+1]
    if key == '-batch':
        batch = True
    if key == '-clean':
        isclean = True
    if key == '-ueof':
        ueof = True
    if key == '-list':
        inlist = sys.argv[i+1]
        #
    if key == '-maxtimeint':
        maxtimeint = int(sys.argv[i+1])
        tmpbase = float(sys.argv[i+1])
    if key == '-dem':
        dem = sys.argv[i+1]
    if key == '-s1dir':
        s1dir = sys.argv[i+1]
    if key == '-roi':
        roi = [float(croi) for croi in sys.argv[i+1].split(',')]

    if key == '-adi':
        adi = sys.argv[i+1]
    if key == '-patch':
        patch_r, patch_a = map(int, sys.argv[i+1].split(','))
    if key == '-overlap':
        overlap_r, overlap_a = map(int, sys.argv[i+1].split(','))

        

#
pSAR.util.log(sys.argv)
#
if flength is None:
    flength = int(100*azlook)
    #
#
#
# step 1: link s1zips to the local s1_raw
#
topdir = os.getcwd()
# 
# step 0: link dem into topo, a local folder in the processing folder
#
dem_dir = os.path.abspath(topodir )
#
if not os.path.exists(dem_dir):
        os.makedirs(dem_dir)
if not os.path.exists(dem_dir+'/dem.grd'):
   #
   if dem is not None and os.path.exists(dem):
       os.symlink(os.path.abspath(dem),dem_dir+'/dem.grd')
#
# update mylist if inlist is an vailid list file...
#
mylist = read_list(inlist)
#
##
# s1a configure file
#
# Since 20240212, configure file will be created by pop_config.csh 
# 
# gmtsar/csh/config.s1a.txt
if not os.path.exists("config.s1a.txt"):
    gmtsar_home = os.environ['GMTSAR_HOME']
    config = gmtsar_home+'/gmtsar/csh/config.s1a.txt'
    #
    goStr = 'pop_config.csh S1_TOPS > config.s1a.txt'
    print(goStr)
    os.system(goStr)
    #
    if not os.path.exists('config.s1a.txt'):
        #
        # shutil.copyfile(config,"config.s1a.txt")
        # else:
        #
        print("Error: no configure file is available!!!!")
        sys.exit(-1)
    #
#
if os.path.exists('master.in'):
    dates = np.loadtxt('master.in',dtype='int')
    # print(dates)
    if len(dates.shape) == 0:
       master = dates
    else:
       master = dates[0]
#
if True:
    #
    raw = rawdir 
    if not os.path.exists(raw):
       os.makedirs(raw)
    #
    s1_tmp = '%s/S1_TMP' % datadir
    #
    s1_raw = '%s/S1_ZIP_RAW' % datadir
    if not os.path.exists(s1_raw):
        os.makedirs(s1_raw)
    #
    s1_unzip = '%s/S1_UNZIP' % datadir
    if not os.path.exists(s1_unzip):
        os.makedirs(s1_unzip)
        #
    #
    if not os.path.exists(s1_raw) or st==0:
        #
        if not os.path.exists(s1dir):
            print(" Err: we cannot find the folder of %s" % s1dir)
            sys.exit(-1)
        #

        sroi = [str(croi) for croi in roi]
        sroi = ','.join(sroi)
        goStr = 'pSAR_S1select_aws.py %s %s -searchstr "%s" -sd %s -ed %s' % (s1_raw,sroi,s1dir+'/S1*.SAFE',sd,ed)
        print(" Pre-step: %s" % goStr)
        os.system(goStr)
        #
    
    s1zips = glob.glob(s1_raw+'/S*.SAFE')
    #
    if os.path.exists(s1_raw) and len(s1zips)>0:
        s1dir = s1_raw
        #
        print(" pSAR_gmtsar_s1: now switch to a local zip folder of %s" % s1dir)
    #
    #
    flag = len(glob.glob(s1_unzip+'/S1*/'))>0 or len(glob.glob(s1_raw+'/S1*.SAFE'))>0 
    #
    if s1dir is None and not flag:
        print("ERROR: no S1 data is given!!!")
        sys.exit(-1)
    #

    #
    if st <= 1:
      if master is not None:
         print(' ROI of Input: %f,%f,%f,%f with master of %d' %(roi[0],roi[1],roi[2],roi[3],master))
      else:
         print(' ROI of Input: %f,%f,%f,%f without a master' %(roi[0],roi[1],roi[2],roi[3]))
      #
      iws,roi = rawdir2swathinfo('%s/S1_ZIP_RAW' % datadir,roi,master,pol,issave=False,plot=swathplot)
      iws,dem_roi = rawdir2swathinfo('%s/S1_ZIP_RAW' % datadir,roi,master,pol,plot=swathplot,iniws=iws,issave=True)
      #
      print(' ROI of DEM: %f,%f,%f,%f' %(dem_roi[0],dem_roi[1],dem_roi[2],dem_roi[3]))
      #
      if not os.path.exists('iws.in') or update:
        with open('iws.in','w') as fid:
          fid.write('%d %d %d\n' % (iws[0],iws[1],iws[2]))
      #
      # preparing dem data for insar
      #
      if dem is None and not os.path.exists('%s/dem.grd' % topodir):
         #
         os.chdir('topo')
         dem_ext = '%f,%f,%f,%f' % (dem_roi[0]-0.075,dem_roi[1]+0.075,\
                                    dem_roi[2]-0.075,dem_roi[3]+0.075)
         dembackup='-backup'
         #
         #
         # updated by FWP, since this version, Copernicus DEM (30m) is set as default dem source...
         # 2023/11/29
         #
         if dem_source.upper() == 'SRTM':
            goStr = 'pSAR_srtmdownload.py %s -output dem -fmt gmt %s' % (dem_ext,dembackup)
         else:
            goStr = 'pSAR_srtmdownload.py %s -output dem -fmt gmt %s' % (dem_ext,dembackup)
            
         print(" Updating DEM: %s " % goStr)
         os.system(goStr)
         #
         dem = os.path.abspath('dem.grd')
         os.chdir(topdir)
    # 
    if not os.path.exists('topo/dem.grd'):
        demgrd = glob.glob('%s/dem.grd' % topodir)
        if len(demgrd)<1:
            print("Error: no valid dem is found in %s!!! " % topodir)
            sys.exit(-1)
        if not os.path.exists('topo'):
            os.makedirs('topo')
        os.symlink(os.path.abspath(demgrd[0]),'topo/dem.grd')
        #
    if demonly:
        #
        print("  ")
        print(" ++++++++++++++++++++++++++++++++++++++++++++++")
        print(" Process: DEM should be ready now. Byebye!!! :)")
        print(" ++++++++++++++++++++++++++++++++++++++++++++++")
        sys.exit(-1)
        #
    # unzip 
    #
    n_zips = len(glob.glob(s1_raw+'/S1*.zip'))
    n_dirs = len(glob.glob(s1_unzip+'/S1*.SAFE'))
    #
    os.chdir(s1_raw)
    #
    # update EOFs first
    # by FWP, @SYSU, Guangzhou, 2020/02/04
    #
    if ueof:
       os.system('pSAR_s1zips2orb.py S1A*.zip')
       os.system('pSAR_s1zips2orb.py S1B*.zip')
    #
    # step 2: unzip S1*.zip into the local folder
    #
    #if st <=2 and et >=2:
      #
      # print(" FWP: %d %d" % (n_zips,n_dirs))
      #
      #if n_zips != n_dirs:
        # os.system('ginsar_unzip_parallel.sh $PWD %d ' % unzip_n_cpus)
        #os.system('pSAR_unzip_parallel.py $PWD %d %d -rawcheck' % (unzip_n_cpus, zipcheck))
    #
    os.chdir(topdir)
    #
    # link S1 folders into UNZIP
    unzipdirs = glob.glob(s1_raw+'/S*.SAFE/')
    #
    for cunzip in unzipdirs:
        #
        cdir_name = os.path.basename(os.path.dirname(cunzip))
        target_dir = os.path.abspath(s1_unzip)+'/'+cdir_name
        #
        if not os.path.exists(target_dir):
           if os.path.islink(target_dir):
               os.system('rm -f %s' % target_dir)
           #
           os.symlink(os.path.abspath(cunzip),target_dir)
           #
    #
    # make the folder of raw for s1 zips
    #
    raw_full = os.path.abspath(raw)
    #
    print(" st: %d in s1 processing..." % st)
    #
    #
    if roi is not None and st <= 2:
        # means a subset cutting is required
        os.chdir(s1_unzip)
        dirs = glob.glob('S1*.SAFE')
        #



        dates = s1dir2dates(dirs)
        dates = list(set(dates))
        dates.sort()
        #
        # cutting
        #
        unzip2raw(dates,raw_full,topdir,orbmodel)
        #
        #
        # clean raw folder
        # if there is any abnormal folder in raw, we will delete them first...
        checkrawdir()
#
if et >= 3:
    #
    print(" >>> raw_DIRs are all done!!! <<<<<")
    if True:
        #
        cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        #
        if os.path.exists('iws.in') and not update:
            with open('iws.in','r') as fid:
                cline = fid.readline()
                cline = cline.split('\n')[0].split()
                iws = [int(iw) for iw in cline]
        #
        if (iws is None and roi is not None) or update:
          print(" Progress: estimating swath IDs to be processed based on given ROI @ %s" % cnow)
          # 
          iws,dem_roi = rawdir2swathinfo('%s/S1_ZIP_RAW' % datadir,roi,master,pol,plot=swathplot,iniws=iws)
          print(" Progress: we are going to process swaths of 1_%d 2_%d 3_%d..." % (iws[0],iws[1],iws[2]))
        #
        if iws is None:
          iws = [1,1,1]
        #
        os.chdir(topdir)
        # 
        super_topdir = os.getcwd()
        #
        if master is None:
            if os.path.exists('master.in'):
                with open('master.in','r') as fid:
                    cline = fid.readline()
                    master = cline.split('\n')[0].strip()
                #
            else:
              cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
              print(" Progress: estimating optimal master acquisition @ %s" % cnow )
              #
              master = safedir2master('%s' % rawdir,iws=iws)
              with open('master.in','w') as fid:
                fid.write('%s\n' % master)
            #
        else:
           master = '%d' % master
           if not os.path.exists('master.in'):
               with open('master.in','w') as fid:
                   fid.write('%s\n' % master)
        #
        #
        if update:
            update_str = ' -update '
        else:
            update_str = ''
        #
        goStr = 'pSAR_gmtsar_dir2datalist.py %s data.in -master %s %s -eofmodel %s' % \
                (os.path.abspath(rawdir),master,update_str,orbmodel)
        print(" Progress: %s" % goStr)
        os.system(goStr)
        #
        cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        #
        # saving iws information into disk
        #
        iws_arr = np.array(iws)
        if unwrap_0 is None:
           if len(np.where(iws_arr != 0)[0])<2:
              unwrap_0 = unwrap_1
           else:
              unwrap_0 = 0.
        #
        os.chdir(super_topdir)
        if update or (not os.path.exists('iws.in')):
           with open('iws.in','w') as fid:
              fid.write('%d %d %d\n' % (iws[0],iws[1],iws[2]))
        #
        cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        os.chdir(super_topdir)
        print(" Progress: generating SLCs in individual raw folders @ %s " % cnow)
        #
        # updated by Wanpeng, Feng @ SYSU, Guangzhou, 2024/02/28
        # since this version, esd_mode and njob are available...
        # 
        raw2slcs(iws,rslc_refine=rslc_refine,njob=njob,esd_mode=esd_mode)
        #
        if et <= 4:
            print(" Progress: processing is stopped after SLC generation is done!")
            sys.exit(0)
        # 
        print(" Progress: generating baseline files in individual raw folders...")
        raw2baseline(iws,master=master,update=update)

        
        #
        print(" Progress: generating Inf pairs in individual raw folders ...")

        fdirs2infpairs(tmpbase,master,sbase,iws,update=update,minnum=minnum,season=season,mylist=mylist)

        #
        if method=='stamps':
           rlook = 1
           azlook = 1
        print(" Progress: checking working folder for interferometry in individual swath folder...")
        #

           
        prefolders4inf(iws)
        print(" Progress: creating configure files for parallel processing...")
        print("           Filter length: %d, multilooking NUM in R and Az: %d and %d " % \
                         (flength,rlook,azlook))
        #
        outcfg = 'batch_config.cfg'
        
        if method=="stamps":
           outcfg = 'batch_config_ps.cfg'           
           dir2infcfg(outcfg,step=1,master=master,toposhift=0,unwrap=unwrap_0,iws=iws,switch_land=switch_land,\
                flength=flength,rlook=rlook,azlook=azlook,interp_flag=interp_flag)
           cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
           print(" Progress: running interferometry @ %s" % cnow)
           
           run_inf_ps(cfg=outcfg,intf='intf.in',njob=njob,iws=iws,master=master)
           
           cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
           print(os.getcwd())
           print(" Progress: running merge and pre stamps @ %s" % cnow)
           merge_prestamps(iws=iws,master=master)
           sys.exit(0)      
             
        dir2infcfg(outcfg,step=1,master=master,toposhift=toposhift,unwrap=unwrap_0,iws=iws,switch_land=switch_land,\
                flength=flength,rlook=rlook,azlook=azlook,interp_flag=interp_flag)
        #
        #
        geoScript = super_topdir+'/proj_ra2ll.info.sh'
        #
        cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        print(" Progress: running interferometry @ %s" % cnow)
        run_inf(cfg=outcfg,intf='intf.in',njob=njob,iws=iws,master=master,\
                snaphu_alg=snaphu_alg,method=unwrap_alg,alpha=alpha,fftsize=fftsize)
        #
        print(" Progress: merging data if needed...")
        iws_str = [str(int(ciws)) for ciws in iws]
        iws_str = ",".join(iws_str)
        #
        if len(np.where(iws_arr != 0)[0])<2:
            print(" Progress: less than 2 swaths need to be processed. Stop here!")
            flag = np.where(iws_arr == 1)[0]+1
            goStr = 'sbas_gmtsar_burst.sh %d' % \
                     (flag)
            sys.exit(0) 
            
              
        #
        if len(np.where(iws_arr != 0)[0])>1:
          if len(np.where(iws_arr != 0)[0]) == 1:
              unwrap_threshold = unwrap_0
          else:
              unwrap_threshold = unwrap_1
          #
          goStr = 'pSAR_gmtsar_merge.py %s -master %s -unwrap_threshold %f -interp_flag %d' % \
                  (iws_str,master,unwrap_threshold, interp_flag)
          cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
          print(" Progress: %s @ %s" % (goStr,cnow))
          os.system(goStr)
          #
        os.chdir(super_topdir)
        #
        if len(np.where(iws_arr != 0)[0])>=1:
          os.chdir('merge')
          if unwrap_1 == 0:
             goStr = 'pSAR_gmtsar_merge2unwrap.py 0 %d -script %s -method %s -snaphu_alg %s' % \
                     (njob,geoScript,unwrap_alg,snaphu_alg)
          else:
             goStr = 'pSAR_gmtsar_merge2unwrap.py %f %d -script %s -method %s -snaphu_alg %s' % \
                     (unwrap_1,njob,geoScript,unwrap_alg,snaphu_alg)
        #
        cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        print(" Progress: %s @ %s" % (goStr,cnow))
        os.system(goStr)

        os.chdir(super_topdir)
        goStr = 'sbas_gmtsar_aws.sh'
        os.system(goStr)
        #
        if roidir is not None:
            if not os.path.exists(roidir):
                os.makedirs(roidir)
            #        
            flag_merge = np.where(np.array(iws,dtype='int')!=0)[0]
            #
            if len(flag_merge) < 2:
                intf_dir = 'F%d/intf_all/' % (flag_merge[0]+1)
                prfolder = '-prmFolder F%d' % (flag_merge[0]+1)
            else:
                intf_dir = 'merge'
                prfolder = ''
            #
            # updated by FWP, DATA/ is replaced by <datadir>
            #
            print(intf_dir,roidir,datadir,njob,prfolder)
            goStr = 'pSAR_gmtsar_s1insar2roi.py %s %s %s/S1_ZIP_RAW %d %s' % (intf_dir,roidir,datadir,njob,prfolder) 
            cnow = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
            print("  Progress: %s @ %s" % (goStr,cnow))
            os.system(goStr)
            #
            #
            if isclean:
                #
                print(" Progress: cleaning the working folder, including F*/, raw/ and %s/" % datadir)
                clean_dir(iws)
        
#
sys.exit(0)
# Good luck!
      
