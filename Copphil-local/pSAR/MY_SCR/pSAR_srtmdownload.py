#!/usr/bin/env python
#
#
import shutil
import os
import sys
import numpy as np
import elevation
import math
import pSAR
import glob
#
def backupsrtm(in_folder,out_folder):
    #
    for ctif in glob.glob(in_folder+'/*/*.tif'):
        if os.path.exists(ctif) and not os.path.islink(ctif):
            #
            cname = os.path.basename(ctif)
            tif_folder = cname[0:3]
            tif_target = out_folder+'/%s/%s' % (tif_folder,cname)
            if not os.path.exists( out_folder+'/%s' % tif_folder):
                os.makedirs(out_folder+'/%s' % tif_folder)
            #
            if not os.path.exists(tif_target):
                #
                print(ctif,tif_target)
                shutil.copyfile(ctif,tif_target)
            #
        #
    #
    return True
def linksrtmsTOlocal(minx,maxx,miny,maxy,srtm_dir,outdir):
    #
    if minx < 0:
        minx = minx - 1
    if miny < 0:
        miny = miny - 1
    #
    #
    for lat in range(int(minx),int(maxx)+1,1):
      if lat>0:
         LAT_S = 'N'
      else:
         LAT_S = 'S'
      #
      for lon in range(int(miny),int(maxy)+1,1):
          if lon>0:
              LON_S='E'
          else:
              LON_S='W'
          #
          LAT_INFO = '%s%02d' % (LAT_S,lat)
          targetTIF = '%s%02d%s%03d.tif' % (LAT_S,abs(lat),LON_S,abs(lon))
          #
          tif_fullpath = srtm_dir+'/cache/%s/%s' % (LAT_INFO,targetTIF)
          #
          print(" TargetTIF: %s, %s" % (tif_fullpath,targetTIF))
          if not os.path.exists(outdir+'/%s/' % LAT_INFO):
              os.makedirs(outdir+'/%s/' % LAT_INFO)
          #
          if  not os.path.exists(outdir+'/%s/%s' % (LAT_INFO,targetTIF)) and os.path.exists(tif_fullpath):
              os.symlink(tif_fullpath,outdir+'/%s/%s' % (LAT_INFO,targetTIF))
          #
      #
    return 0
def getsrtm_home():
    #
    try:
        srtm_home = os.environ['SRTM_HOME']
    except:
        srtm_home = os.getcwd()
    return srtm_home
#
srtm_home = getsrtm_home()
if len(sys.argv) < 2:
   #srtm_home = os.environ['SRTM_HOME']
   helpstr = \
   '''

   %s <left_lon>,<right_lon>,<lower_lat>,<upper_lat> 
      -output [geotif.tif in deafult] 
      -cachedir [%s in deafult]
      -srtm3
      -output [gdem in default]
      -xinv [3, in default]
      -yinv [3, in default]
      -fmt [GMT in default]
      -backup [False in default]
      -backuponly [backup only with this option]
   +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   To download SRTM data automatically with the Python module, elevation.
   Due to a limitation in the elevation, there are limited numbers of tiles 
   being allowed to download. 
   
   Developed by Wanpeng Feng, @CCRS/NRCan, 2018-06-12
   
   Updated by FWP, @SYSU, Guangzhou, 2021/02/03
    since this version, the required SRTM tif tiles will be linked into the local folder...
    so any users in the server should have not any permission issues when using this script...

   '''
   print(helpstr % (sys.argv[0],srtm_home))
   sys.exit(-1)
#
backup = False
fmt       = 'GMT'
srtm      = 'SRTM1'
output    = 'gdem'
cachedir  = srtm_home
backuponly = False
#
xinv = 2 
yinv = 2
#
for i,ckey in enumerate(sys.argv):
    if ckey == '-backuponly':
        backuponly = True
        backup = True
    if ckey == '-backup':
        backup = True
    if ckey == '-fmt':
        fmt = sys.argv[i+1]
    if ckey == '-cachedir':
        cachedir = sys.argv[i+1]
    if ckey == '-srtm3':
       srtm = 'SRTM3'
    if ckey == '-output':
       output = sys.argv[i+1]
    if ckey == '-xinv':
        xinv = float(sys.argv[i+1])
    if ckey == '-yinv':
        yinv = float(sys.argv[i+1])
#
# logging
#
pSAR.util.log(sys.argv)
#
topdir = os.getcwd()
#
if True:
  roi = sys.argv[1].split(',')
  #
  lowcor = [float(sys.argv[1].split(',')[0]),float(sys.argv[1].split(',')[2])]
  uppcor = [float(sys.argv[1].split(',')[1]),float(sys.argv[1].split(',')[3])]
  #
  #
  lonstep = math.ceil((uppcor[0]-lowcor[0])/xinv)
  latstep = math.ceil((uppcor[1]-lowcor[1])/yinv)
  print(" +++++++++++++++++++++++++++++++++++++++++++++++++")
  print(" + Lon: %f - %f Lat: %f - %f" % (uppcor[0],lowcor[0],uppcor[1],lowcor[1]))
  print(" + Steps in LON: %d Steps in LAT: %d" % (lonstep,latstep))
  print(" +++++++++++++++++++++++++++++++++++++++++++++++++")
  lons = np.linspace(lowcor[0],uppcor[0],num=lonstep+1)
  lats = np.linspace(lowcor[1],uppcor[1],num=latstep+1)
  # print(lons,lats)
  if cachedir is not None:
      srtmdir = cachedir
  else:
      srtmdir = os.getcwd() 
  #
  # to make output folder specific and related to the output dem
  #
  outdir = '%s_%s' % (output,srtm)
  #
  outdir_srtm = '%s/%s' % (outdir,srtm)
  #
  #
  if not os.path.exists(outdir):
     os.makedirs(outdir)
  #
  counter = 0
  for i in range(len(lons)-1):
     for j in range(len(lats)-1):
        #
        counter += 1
        outtif = 'Mosaic_%d.tif' % counter
        #
        linksrtmsTOlocal(lats[j],lats[j+1],lons[i],lons[i+1],srtmdir+'/%s' % srtm,(outdir+'/%s/cache' % srtm))
        # 
        goEIO = 'eio --product %s --cache_dir %s clip -o %s --bounds %f %f %f %f' % \
                 (srtm,os.getcwd()+'/'+outdir, outtif, lons[i],lats[j],lons[i+1],lats[j+1])
        # goEIO = 'eio --product %s --cache_dir %s clip -o %s --bounds %f %f %f %f' % \
        #         (srtm,srtmdir,outtif,lons[i],lats[j],lons[i+1],lats[j+1])
        print(' %s' % goEIO)
        if not os.path.exists(outtif):
           os.system(goEIO)
        if backup:
           backupsrtm(outdir_srtm+'/cache',srtmdir+'/%s/cache' % srtm)
  #
  os.system('rm  Mosaic*.tif -f')
  #
  if backup:
     backupsrtm(outdir_srtm+'/cache',srtmdir+'/%s/cache' % srtm)
  if backuponly:
     print(" SRTM: exiting now as only backup is required!!!")
     sys.exit(-1)
  #
  os.chdir(outdir)
  #
  # change a way to mosaic dem data
  # 
  if True:
    #
    # for cmosaic in glob.glob('Mosai*.tif'):
    #     os.system('rm %s -f' % cmosaic)
    #
    tifs_dir = 'tmp_DIRS'
    if not os.path.exists(tifs_dir):
        os.makedirs(tifs_dir)
    #
    print('%s/%s/cache/*/*.tif' % (os.getcwd(),srtm))
    for ctif in glob.glob('%s/%s/cache/*/*.tif' % (os.getcwd(),srtm)):
      goLinks = 'ln -s %s %s/%s' % (ctif,tifs_dir,os.path.basename(ctif))
      if not os.path.islink('%s/%s' % (tifs_dir,os.path.basename(ctif))):
         os.system(goLinks)
    #
    #
    # mosaicGo = 'pSAR_demmosaic.py %s -searchstr "Mosai*.tif"' % (output)
    mosaicGo = 'pSAR_demmosaic.py %s_tmp -searchstr "%s/*.tif"' % (output,tifs_dir)
    #
    if not os.path.exists('%s.tif' % output):
       print(' %s' % mosaicGo) 
       os.system(mosaicGo)
       #
       gdalwarp_GO = 'gdal_translate -of %s -projwin %s %s %s %s %s %s' % \
             ('GTiff',roi[0],roi[3],roi[1],roi[2],output+'_tmp.tif',output+'.tif')
       #      #
       print(gdalwarp_GO)
       os.system(gdalwarp_GO)
       print(os.getcwd())
       #
       if os.path.exists(output+'_tmp.tif'):
           os.system('rm -- %s' % output+'_tmp.tif')
  #
  os.chdir(topdir)
  os.chdir(output+"_SRTM1/")
  #
  gammadem = '%s.dem' % output
  if fmt.upper() == 'ROI':
     print(" FWP", os.getcwd())
     goStr = 'pSAR_imgformat.py %s %s -of EHdr' % (output+'.tif',topdir+'/'+output+'.img')
     print(goStr)
     os.system(goStr)
  if fmt.upper() == 'GMT':
     goStr = 'pSAR_imgformat.py %s %s -of netCDF' % (output+'.tif',topdir+'/'+output+'.grd')
     print(goStr)
     os.system(goStr)
  if fmt.upper() == 'GAMMA' and not os.path.exists(gammadem):
     #
     goStr = 'pSAR_imgformat.py %s %s -of EHdr' % (output+'.tif',output+'_TMP.img')
     goGamma = 'ginsar_ehdr2gamma.sh %s_TMP.hdr %s_TMP.img %s' % (output,output,topdir+'/'+output)
     os.system(goGamma)
  #
  os.chdir(topdir)
