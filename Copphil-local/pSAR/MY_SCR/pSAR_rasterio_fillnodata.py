#!/usr/bin/env python
#
#
import os
import sys
import pSAR
import numpy as np
#
import warnings
import rasterio
import netCDF4 as nc
#
from rasterio.fill import fillnodata
warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)
#
def write_netcdf(fn,refgrd,indata):
    #
    indata[indata==0] = np.nan
    #
    with nc.Dataset(refgrd) as src, nc.Dataset(fn, "w") as dst:
      #
      # copy attributes
      for name in src.ncattrs():
          dst.setncattr(name, src.getncattr(name))
      # copy dimensions
      for name, dimension in src.dimensions.items():
          dst.createDimension(
              name, (len(dimension) if not dimension.isunlimited else None))
      # copy all file data except for the excluded
      for name, variable in src.variables.items():
          x = dst.createVariable(name, variable.datatype, variable.dimensions,fill_value=np.nan)
          if name == 'z':
              a = dst.variables[name]
              a.long_name= 'z'
              minv = np.min(indata[~np.isnan(indata)])
              maxv = np.max(indata[~np.isnan(indata)])
              #
              a.actual_range = [minv,maxv]
              dst.variables[name][:] = np.flipud(indata)
          else:
              dst.variables[name][:] = src.variables[name][:]
          
      #
    
if len(sys.argv)<3:
    #
    helpstr = \
        '''
        %s <in_roi> <out_roi> -mdist [50 in default]
                              -eps [10**-5 in default]
                              -smooth [0 in default]
        ++++++++++++++++++++++++++++++++++++++++++++++
        To fill no-data holes in an image with interpolation
        Note that grdfile in gmtsar processing folders is in netCDF format.
        raterio cannot write a netCDF well, we have to turn to netCDF4-python
        

        dependency:
        rasterio
        

        by Wanpeng Feng, @SYSU, 2021/10/14


        '''
    #
    print(helpstr % sys.argv[0])
    sys.exit(0)
#
#
############################################################
max_search_dist = 300 
eps = 10**-5
smooth_factor = 0
#
for i,key in enumerate(sys.argv):
    #
    if key == '-smooth':
        smooth_factor = int(sys.argv[i+1])
    if key == '-mdist':
        max_search_dist = float(sys.argv[i+1])
    if key == '-eps':
        eps = float(sys.argv[i+1])
        #
    #
#
#
if True:
    #
    infile = sys.argv[1]
    out_roi = sys.argv[2]
    #
    ext = infile.split('.')[-1]
    #
    #
    flag = 0
    if ext.upper() == 'GRD':
       #
       raster = rasterio.open(infile)
       meta = raster.meta
       data = raster.read(1)
       #
       flag = 1
    else:
       info,_ = pSAR.roipac.rsc_read(infile+'.rsc')
       #
       data = pSAR.roipac.roi_read(infile)
    #
    flagdata = np.copy(data)
    # flagdata = flagdata.astype('float')
    flagdata[flagdata<-15000] = 0
    flagdata[np.isnan(flagdata)] = 0
    flagdata[np.isinf(flagdata)] = 0
    # flagdata[flagdata<eps] = 0
    mask_arr = flagdata != 0
    #
    #
    arr_filled = fillnodata(data.astype('float'), mask=mask_arr, \
            max_search_distance=max_search_dist, \
            smoothing_iterations=smooth_factor)
    #
    flagdata = np.copy(arr_filled)
    flagdata[flagdata<-15000] = 0
    flagdata[np.isnan(flagdata)] = 0
    flagdata[np.isinf(flagdata)] = 0
    # flagdata[flagdata<eps] = 0
    mask_arr = flagdata != 0
    #
    arr_filled = fillnodata(flagdata,mask=mask_arr, \
            max_search_distance=max_search_dist, \
            smoothing_iterations=smooth_factor)
    #
    #　arr_filled.astype('float')
    # arr_filled[flagdata<eps] = 0
    #
    # arr_filled = fillnodata(arr_filled, mask=mask_arr, \
    #         max_search_distance=max_search_dist, \
    #         smoothing_iterations=smooth_factor)
    #
    if flag == 0:
       pSAR.roipac.roi_write(arr_filled,out_roi)
       pSAR.roipac.info_to_rsc(info,out_roi+'.rsc')
    else:
       #
       if meta['driver'] == 'netCDF':
          write_netcdf(out_roi,infile,arr_filled)
       else:
          with rasterio.open(out_roi, "w", **meta) as dest:
              dest.write(arr_filled.astype(meta['dtype']),1)

