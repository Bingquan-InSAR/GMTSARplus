#!/usr/bin/env python
#
#
import matplotlib.pyplot as plt
#
import numpy as np
import os
import sys
import glob
import netCDF4 as nc
#
def merge_phase(inlist):
    #
    outlist = inlist+'.phaseonly'
    #
    outfid = open(outlist,'w')
    #
    with open(inlist,'r') as fid:
        for cline in fid:
            inline = cline.split('\n')[0]
            inline = inline.replace('phasefilt.grd','phase.grd')
            outfid.write('%s\n' % inline)
            #
        #
    #
    outfid.close()
    #
    #
#
def grd_read(ingrd):
    #
    file_obj = nc.Dataset(ingrd)
    keys = file_obj.variables.keys()
    keys = list(keys)
    lon_key = 'lon'
    #
    if 'lon' not in keys:
        for i in range(len(keys)):
            if 'x' in keys[i]:
                lon_key = keys[i]
    #
    lat_key = 'lat'
    if 'lat' not in keys:
        for i in range(len(keys)):
           if 'y' in keys[i]:
              lat_key = keys[i]
    #
    lon = file_obj.variables[lon_key][:]
    lat = file_obj.variables[lat_key][:]
    phs = file_obj.variables['z'][:]
    if len(phs.shape)==1:
      for i in range(len(keys)):
          if 'dimen' in keys[i]:
            dim_key = keys[i]
            dims = file_obj.variables[dim_key][:]
            phs = np.reshape(phs,[dims[1],dims[0]])
    else:
      phs = np.flipud(phs)
    lon[lon>180] = lon[lon>180] - 360.
    ext = [lon.min(),lon.max(),lat.min(),lat.max()]
    #
    return phs,ext
#
def validgrd(cgrd):
    #
    validInd = []
    index = np.where(~np.isnan(cgrd))
    #
    return np.sort(np.unique(index[0]))
#
def gaps(grds):
    #
    # updated by Wanpeng Feng, @SYSU, Guangzhou, 2021/08/24
    #
    outdata = []
    validInd = None
    for grd in grds:
        #
        d1,ext = grd_read(grds[0])
        #
        if validInd is None:
           validInd = validgrd(d1)
           cenInd = int((validInd[0]+validInd[-1])/2) 
        #
        d = d1[cenInd,:]
        nans = np.isnan(d)
        d[~nans] = 0
        d[nans] = 1
        #
        index = np.where(d==1)[0]
        #
        if len(index)<2:
           ind1 = 0
           ind2 = d.shape[0]-10
        else:
           ind1 = index[index<1000]
           ind2 = index[index>1000]
           if len(ind1)==0:
               ind1 = np.array([0])
           if len(ind2)==0:
               ind2 = np.array([d.shape[0]-1])
        #
        #
        outdata.append([np.max(ind1),np.min(ind2),np.max(ind2)-np.min(ind2)])
    #
    return outdata
#
def list2grds(inlist):
    #
    grds = []
    with open(inlist,'r') as fid:
        for cline in fid:
            tmp = cline.split(':')
            grds.append(tmp[1].split('\n')[0])
        #
    #
    return grds
#
if len(sys.argv)<2:
    #
    helpstr = \
      '''
      %s <stem> -update -overlap [None in default] -phs
      +++++++++++++++++++++++++++++++++++++++++++++
      To redo merge_swath in the merge folder...

      In case that there are some gaps to be spotted in the merged grds, we can
      redo merging by resetting n1 and n2 by considering the null zone only...
      
      stem rootname of PRM
      
      ----
      Developed by FWP, @SYSU, Guangzhou, 2021/06/06  
      
      ----
      Fixed a bug by FWP, @SYSU, Guangzhou, 2021/08/24

      ----
      Force to merge phase files, updated by FWP, @SYSU, Guangzhou, 2022/11/06
      
      ---
      Reset -overlap as None in default, let merge_swath to determine the shift bins in default...
      by Wanpeng Feng, @SYSU, Guangzhou, 2023/12/05
stem
      '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
    #
#
update = False
overlap = None 
phs = False
#
#
for i,key in enumerate(sys.argv):
    #
    if key == '-phs':
        phs = True
    if key == '-overlap':
        overlap = int(sys.argv[i+1])
    if key == '-update':
        update = True
    #
#
#
if True:
    #
    #
    stem = sys.argv[1]
    #
    sgrds = list2grds('tmp_phaselist')
    #
    ns = gaps(sgrds)
    ns = np.array(ns)
    shiftN = ns[1:3,0]
    #
    n1 = shiftN[0]
    if shiftN.shape[0]<2:
        n2 = 0
    else:
        n2 = shiftN[1]
    #
    # print(ns,n1,n2)
    tmplist = ['tmp_masklist','tmp_corrlist','tmp_phaselist','tmp_amplist']
    outgrd = ['mask.grd','corr.grd','phasefilt.grd','amp.grd']
    #
    if phs:
       merge_phase(tmplist[2])
       cstem = 'phase.grd'
       #
       if overlap is None:
          goStr = 'merge_swath %s %s %s' % (tmplist[2]+'.phaseonly','phase.grd',cstem)
       else: 
          goStr = 'merge_swath %s %s %s %d %d' % (tmplist[2]+'.phaseonly','phase.grd',cstem,n1+overlap,n2+overlap)
       #
       if not os.path.exists('phase.grd'):
          #
          print(goStr)
          os.system(goStr)
       #
    #
    for i in range(len(tmplist)):
        #
        if overlap is None:
           goStr = 'merge_swath %s %s %s' % (tmplist[i],outgrd[i],stem)
        else:
           goStr = 'merge_swath %s %s %s %d %d' % (tmplist[i],outgrd[i],stem,n1+overlap,n2+overlap)
        #
        if not os.path.exists(outgrd[i]) or update:
          print(goStr)
          os.system(goStr)
