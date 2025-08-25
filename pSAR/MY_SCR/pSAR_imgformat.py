#! /usr/bin/env python
#
#
#############################
import pSAR,sys,os,pDATA
import numpy as np
#
#
helpstr=\
'''
    %s <in_geo_tif> <out_img> -of [EHDr] -proj [None] -cor
           -ot [None in default]
    #############################################
    To generate Image files from a Geotiff
    -proj a projection file which can be generated with gdal
          for example, EPSG:4326 for
                        +proj=longlat +datum=WGS84 +no_defs 
    -cor  a flag for invalid pixel correction, False in default
    -ot   output format, in default an identical format is used 
          below are available formtas supported in GDAL,
          e.g. Byte/Int16/UInt16/UInt32/Int32/Float32/Float64/
             CInt16/CInt32/CFloat32/CFloat64}   
    Developed by Wanpeng Feng, @NRCan, 2016-07-20
    
'''

if len(sys.argv)<2:
   print(helpstr % sys.argv[0])
   sys.exit(-1)

#
ingeotiff = sys.argv[1]
outimg    = sys.argv[2]
of        = "EHDr"
ot        = None
proj      = None
iscor     = False
#
counter = 0
for ckey in sys.argv:
   counter += 1
   if ckey == '-ot':
      ot = sys.argv[counter]
   if ckey == "-of":
      of = sys.argv[counter]
   if ckey == '-proj':
      proj = sys.argv[counter]
   if ckey == '-cor':
      iscor = True
#
#
#
if __name__ == '__main__':
  #
  if os.path.exists(ingeotiff+'.rsc'):
     hdr = ingeotiff.split('.')[0] + '.hdr'
     #
     infmt = pSAR.roipac.roi_to_fmt(ingeotiff)
     #
     if not os.path.exists(hdr):
        pSAR.roipac.rsc2ehdr(ingeotiff+'.rsc',hdr,dtype=infmt)

  if proj is not None:   
     sproj = ' -a_srs %s ' % proj
  else:
     sproj = ''
  if ot is not None:
      ot_str = '-ot %s' % ot
  else:
      ot_str = ''
  #
  # since gdal3.6 or greater, GMT has been out of support...
  # now netCDwill be instead for GMT, by Wanpeng Feng, @SYSU, Guanzhou, 2023/1203
  #
  if of == 'GMT':
      of = 'netCDF'
  #
  command_1 = ('gdal_translate -a_srs "+proj=latlong +datum=WGS84" %s -of %s %s %s %s' % (ot_str,of,sproj,ingeotiff,outimg))
  print(" %s" % command_1)
  os.system(command_1)
  #
  if of.upper() == "EHDR":
    #
    ehdrdir = os.path.dirname(os.path.abspath(outimg))
    exts = os.path.basename(outimg).split('.')[-1]
    # bname    = os.path.basename(outimg).split('.')
    #
    ehdr_hdr = ehdrdir+'/'+os.path.basename(outimg)[:-len(exts)]+'hdr'
    #
    roi_rsc  = outimg+'.rsc'
    ginfo    = pSAR.roipac.ehdr_read(ehdr_hdr)
    #
    pSAR.roipac.info_to_rsc(ginfo,roi_rsc)
    #
    if iscor:
      #
      data = pSAR.roipac.roi_read(outimg)
      data[np.abs(data)>10000] = 0
      pSAR.roipac.roi_write(data,outimg)
