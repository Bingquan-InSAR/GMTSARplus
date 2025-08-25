#!/usr/bin/env python
#
#
##############################
import os
import sys
import glob
import pSAR
import pGMT
import numpy as np
#
if len(sys.argv) < 2:
   helpstr=\
   '''
      
      %s <outname_root, noting that no .tif is required.> -searchstr [*.tif in default]
                -update
                -s [as used for -searchstr]
      ++++++++++++++++++++++++++++++++++++++++++++
      To mosaic geotiff-format DEM files into an integrated one



      by Wanpeng Feng, @NRCan, 2016-08-08
      Updated by Wanpeng Feng, @NRCan, 2016-09-19
      ---
      gdal_merge.py is used for mosaicing...
      loging by wanpeng feng, @NRCan, April 3rd, 2017
  
   '''
   print(helpstr % sys.argv[0])
   sys.exit(-1)
#
if len(sys.argv) < 2:
   outname_root='Merg'
else:
   outname_root=sys.argv[1]
################################################
# Pre-settings
searchstr = "*.tif"
isupdate  = False          # fill bad value by global dem srtm15
globaldem = '/media/wafeng/FWP_backup/data/DEM/global/topo15.grd'
badvalue  = 12000
outgeotif = outname_root+'.tif'
outimg    = outname_root+'.img'
outhdr    = outname_root+'.hdr'
outrsc    = outimg+'.rsc'
outdem = outname_root+'_GLOB.img'
################################################
nkey = 0
for ckey in sys.argv:
    nkey += 1
    if ckey == "-searchstr":
       searchstr = sys.argv[nkey]
    if ckey == '-s':
       searchstr = sys.argv[nkey]
    if ckey == "-fmt":
       fmt = sys.argv[nkey]
    if ckey == "-update":
       isupdate=True
#################################################
#
geotifs     = glob.glob(searchstr)
str_geotifs = ' '.join(geotifs)
#
if not os.path.exists(outgeotif):
   #
   command_mosaicking=('gdal_merge.py -of GTiff -o %s %s' % (outgeotif,str_geotifs))
   print(' pSAR_demmosaic: %s' % command_mosaicking)
   os.system(command_mosaicking)
   #
else:
   #
   print(' pSAR_demmosaic: %s exists. Delete it if you want to re-create it.' % outgeotif)
#
if not os.path.exists(outimg):
   #
   command_translating = ('gdal_translate -of EHDr %s %s' % (outgeotif,outimg))
   print(' pSAR_demmosaic: %s' % command_translating)
   os.system(command_translating)
else:
   #
   print(' pSAR_demmosaic: %s exists. Delete it if you hope to re-create it again.' % outimg)
#
if (not os.path.exists(outrsc) and os.path.exists(outhdr)):
   pSAR.roipac.ehdr2rsc(outhdr,outrsc)
#
if not os.path.exists(outrsc):
   print(' pSAR_demmosaic: WARNING!!! %s cannot be found. Please check it carefully.' % outrsc)
#
if (os.path.exists(globaldem) and isupdate):
   print(' pSAR_demmosaic: To use %s to fill badvalue in %s' % (globaldem,outimg))
   if fmt == "Int16":
      cfmt='h'
   else:
      cfmt='f'
   flag = pGMT.gmt_globaldem2roiscale(globaldem,outimg,outdem,fmt=cfmt)
   #
   print(' pSAR_demmosaic: To use %s to fill badvalue in %s' % (outdem,outimg))

rawdem = pSAR.roipac.roi_read(outimg)
rawdem[np.isnan(rawdem)] = 0
rawdem[np.fabs(rawdem)>12000] = 0
#
if os.path.exists(outdem):
  #
  refdem = pSAR.roipac.roi_read(outdem)
  rawdem[np.fabs(rawdem)==0] = refdem[np.fabs(rawdem)==0]
#
#
