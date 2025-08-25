#!/usr/bin/env python
#
#
import glob
import pGMT5SAR
import pDATA
import pSAR
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pGMT
from scipy.interpolate import griddata
import shutil
#
def vec2incazi(e,n,u):
    #
    inc = np.arccos(u)
    sin_inc = np.sin(inc)
    azi = np.arctan2(n/np.sin(inc),-e/np.sin(inc))
    return azi * 180/np.pi, inc*180/np.pi
#
#
if len(sys.argv)<4:
    #
    #
    helpstr = \
        '''
        %s <in_phs> <root_out_vec> <prm> -dem <dem_data default in GRD> -sat [ALOS in default]
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        To calculate projection vectors for geocoded interfergorams...

        <in_phs>         geocoded phase in ROI_PAC format, grd may be ok for future consideration.
        <root_out_vec>   a root name for output results
        -dem <dem_data>  a dem data that will be required to extract dem inforamtion ...
        -sat             satellite used in calculatin, i.e. ALOS, ENVISAT, S1....     
        
        This is a python version of make_los_ascii.csh from GMTSAR; and this version should be
        more robust than the csh.

        Written by Wanpeng Feng, @SYSU, Gungzhou, 20200927
              
        '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
    #
    #

#
# 
pSAR.util.log(sys.argv)
#
#
if True:
  #
  prm = sys.argv[3]
  dem = None
  sat = 'ALOS'
  in_phs = sys.argv[1]
  out_root = sys.argv[2]
  #
  #
  for i,key in enumerate(sys.argv):
      #
      if key == '-dem':
          dem = sys.argv[i+1]
      if key == '-sat':
          sat = sys.argv[i+1]

  # 
  if os.path.exists(out_root+'.inc') and os.path.exists(out_root+'.azi'):
      print(" Congrats: all files have been done!!!")
      sys.exit(-1)
  #
  #######################################################3
  #
  if in_phs[-3::] == 'grd':
      info,ext,data = pDATA.grd_read(in_phs)
      if not os.path.exists(in_phs+'.rsc'):
          pSAR.roipac.info_to_rsc(info,in_phs+'.rsc')
      #
  else:
      info,ext = pSAR.roipac.rsc_read(in_phs+'.rsc')
  #
  lons = np.linspace(ext[0]-0.05,ext[1]+0.05,num = int((ext[1]+0.05 - ext[0] + 0.05)/0.01))
  lats = np.linspace(ext[2]-0.05,ext[3]+0.05,num = int((ext[3]+0.05 - ext[2] + 0.05)/0.01))
  xv, yv = np.meshgrid(lons, lats, sparse=False, indexing='ij')
  #
  xv[xv > 180] = xv[xv > 180] - 360
  # plt.plot(xv[:],yv[:],'or')
  # plt.show()
  #
  xy = np.vstack([xv.ravel(),yv.ravel()]).T
  xy_f = '_llt.gmt'
  np.savetxt(xy_f,xy,fmt='%f %f')
  #
  flag,lld,err = pGMT.gmt_grdtrack(dem,xy_f)
  #
  #  SAT_look IMG-HH-ALOS2327893300-200618-WBDR1.1__D-F3.PRM < _lld.gmt > _llv.gmt
  outvel = '_llv.gmt'
  #
  goStr = 'SAT_look %s < %s > %s' % (prm,err,outvel)
  print(" GMTSAR: %s" % goStr)
  # 
  prminfo = pGMT5SAR.prm2info(prm)
  ledfile = prminfo["led_file"]
  if not os.path.exists(ledfile):
     leds = glob.glob('../../F*/intf_all/*/%s' % ledfile) 
     if len(leds)>0:
        cled = os.path.abspath(leds[0])
        os.system('ln -s %s %s ' % (cled,ledfile))
     else:
        printf(" Error: NO led file is available ...")
        sys.exit(-1)
        #
  #
  os.system(goStr)
  #
  indata = np.loadtxt(outvel)
  #
  # print(indata.shape)
  ev = indata[:,-3]
  nv = indata[:,-2]
  uv = indata[:,-1]
  #
  lonm,latm = pSAR.roipac.rsc_to_llm(in_phs+'.rsc')
  lonm[lonm>180] = lonm[lonm>180] - 360
  #
  # print(lonm.shape,latm.shape)
  #aps = griddata(xys, ts_data, (grid_x, grid_y), method=method)
  e_arr = griddata(indata[:,0:2],ev,(lonm,latm),method = 'linear')
  n_arr = griddata(indata[:,0:2],nv,(lonm,latm),method = 'linear')
  u_arr = griddata(indata[:,0:2],uv,(lonm,latm),method = 'linear')
  #
  #
  e_arr_file = out_root+'.e'
  n_arr_file = out_root+'.n'
  u_arr_file = out_root+'.u'
  #
  pSAR.roipac.roi_write(e_arr,e_arr_file)
  pSAR.roipac.roi_write(n_arr,n_arr_file)
  pSAR.roipac.roi_write(u_arr,u_arr_file)
  shutil.copyfile(in_phs+'.rsc',e_arr_file+'.rsc')
  shutil.copyfile(in_phs+'.rsc',n_arr_file+'.rsc')
  shutil.copyfile(in_phs+'.rsc',u_arr_file+'.rsc')
  #
  # env to inc/azi
  #
  # vec2incazi(e,n,u)
  azi,inc = vec2incazi(e_arr,n_arr,u_arr)
  inc_file = out_root+'.inc'
  azi_file = out_root+'.azi'
  #
  pSAR.roipac.roi_write(inc,inc_file)
  pSAR.roipac.roi_write(azi,azi_file)
  #
  shutil.copyfile(in_phs+'.rsc',azi_file+'.rsc')
  shutil.copyfile(in_phs+'.rsc',inc_file+'.rsc')
  #err = 
