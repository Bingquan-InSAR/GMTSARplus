#!/usr/bin/env python
#
#
import pSAR
import os
import sys
import glob
#
#
# 
if True:
    cdir = os.getcwd()
    updir = os.path.basename(os.path.dirname(cdir))
    tmpPRM = glob.glob('*.PRM')
    if len(tmpPRM) == 0:
        print("Error: no PRM is available!!!")
        sys.exit(-1)
        #
    if updir.upper() == 'MERGE':
       #
       prm = 'supermaster.PRM'
       dem = 'dem.grd'
    else:
       prms = glob.glob('S1*ALL_F*.PRM')
       prms.sort()
       prm = prms[0]  
       dem = '../../topo/dem.grd'
    #
    #
    geoGRD = 'unwrap_ll.grd'
    if not os.path.exists(geoGRD):
       geoGRD = 'phasefilt_ll.grd'
    #
    if os.path.exists(geoGRD):
        goStr = 'pSAR_gmtsar_los2projvec.py %s losvec %s -dem %s' % (geoGRD, prm, dem)
        print(goStr)
        os.system(goStr)
    else:
        print("No geocoded GRD filese are avaialbe!!!")
        #
        
