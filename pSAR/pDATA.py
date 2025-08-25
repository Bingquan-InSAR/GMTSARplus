#! /usr/bin/env python
#
# A Python Module to handle different data in different formats
# The data formats supported in this module include ndk(GCMT), kml, geojson,
# specified coseismic GPS data. This can be growing quickly and bigger 
# with time, which hope to be very supportive in the future academic 
# activities...
# 
# ALOS2 CEOS format can also be supported since May 2017. 
# led2info() can return information 
# Created and Updated by Wanpeng Feng, @CCRS/NRCan, since 2016-11-14
#
# Since 2017-05-25, all python scripts, modules and any other python related 
# codes will be implemented with python 3.x...
# Some bugs due to the heavy changes cannot be avoided. 
# Btw, a module, math was also obsoluted since this version. All funtions in
# math will be replaced with numpy. Noted by Wanpeng Feng, @CCRS/NRCan, 
# 2017-05-25
#
###############################################################################
import numpy as np
import pSAR
import os
import sys
import pS1
import subprocess
try:
  import geojson
except:
  print(" pDATA: (Warning) geojson is not available")
try:
  import gdal
except:
  try:
    from osgeo import gdal
  except:
    print(" pDATA: (Warning) gdal is not available")
#
#
import csv
from datetime import datetime as dt
import xml.dom.minidom
import xml.etree.ElementTree as ET
#
import zipfile
#
# below moduel is used for reading a grd format file
#
import netCDF4 as nc
import shapely
from lxml import etree
import pSEIS
#
###############################################################################
def kml_line(inkml,tag_1='Placemark'):
   #
   DOMTree    = xml.dom.minidom.parse(inkml)
   collection = DOMTree.documentElement
   #
   tags       = collection.getElementsByTagName(tag_1)
   #
   pts_data = []
   for index in range(len(tags)):
     #
     # descrips
     cdata = []
     coorids = tags[index].getElementsByTagName("coordinates")
     for j in range(len(coorids)):
        #
        coords  = coorids[j].childNodes[0].data
        #
        ptstmp  = coords.split()
        outdata = np.zeros([len(ptstmp),3])
        for nk in range(len(ptstmp)):
            cdatas = ptstmp[nk].split(',')
            if len(cdatas)>2:
               outdata[nk,:] = [float(cdatas[0]),float(cdatas[1]),float(cdatas[2])]
            else:
               outdata[nk,:] = [float(cdatas[0]),float(cdatas[1]),0]
        #
        pts = outdata[:,0:2]
        #
        cdata.append(pts)
        #
     #
     cdata = np.array(cdata)
     pts_data.append(cdata[0,:,:])
   #
   return pts_data


def cmonoc_cgps_raw(in_sta):
    #
    properties = []
    data = []
    counter = 0
    with open(in_sta,'r') as fid:
        #
        for cline in fid:
            cline = cline.split('\n')[0]
            if 'YYYY.DECM' in cline:
                counter = counter + 1
                properties = cline.split()
            if counter > 0 and 'YYYY.DECM' not in cline:
                #
                tmp = cline.split()
                cdata = [float(ctmp) for ctmp in tmp]
                data.append(cdata)
            #
        #
    #
    return np.array(data),properties
def cmonoc_cgps_detrend(in_sta):
    #
    # cmonoc
    sta = []
    data = []
    counter = 0
    with open(in_sta,'r') as fid:
        #
        for cline in fid:
            cline = cline.split('\n')[0]
            if '4-character ID' in cline:
                tmp = cline.split(':')[1]
                sta = tmp
            if '# YYYYMMDD' in cline:
                counter = counter + 1
            if counter > 0 and '#' not in cline:
                #
                tmp = cline.split()
                cdata = [float(ctmp) for ctmp in tmp]
                data.append(cdata)
            #
        #
    #
    return np.array(data),sta
#
def zipcheck(in_zip):
    try:
      zipID = zipfile.ZipFile(in_zip)
    except:
      return False
    #
    try:
      ret = zipID.testzip()
      if ret is not None:
        return False
      else:
        return True
    except:
        return False
#
def zipcorrupt(in_zip):
    #
    sTr = 'zip -t %s > zip.T.log' % in_zip
    os.system(sTr)
    #
    flag = False
    with open('zip.T.log','r') as fid:
     for cline in fid:
        #
        if 'error:' in cline:
            flag = True
        elif 'bad zipfile' in cline:
            flag = True
    return flag
###############################################################################
def read_mif_pts(inmif):
    '''
    mapinfo
    MIF format for points
    '''
    outdata = []
    with open(inmif,'r') as fid:
        for cline in fid:
            tmp = cline.split('\n')[0]
            tmp = tmp.split()
            if len(tmp) > 2 and tmp[0].upper() == 'POINT':
                outdata.append([float(tmp[1]),float(tmp[2])])
            #
        #
    return np.array(outdata)
#
###############################################################################
#
def read_mif_lines(inmif):
    outdata = []
    with open(inmif,'r') as fid:
        for cline in fid:
            tmp = cline.split('\n')[0]
            tmp = tmp.split()
            goflag = False
            if len(tmp) > 0 and tmp[0].upper() == 'PLINE':
                nlines = int(tmp[1])
                tdata = []
                for i in range(nlines):
                    tline = fid.readline()
                    tline = tline.split('\n')[0].split()
                    tdata.append([float(tline[0]),float(tline[1])])
                goflag = True
            if goflag:
                outdata.append(np.array(tdata))
            #
        #
    #
    return outdata
#   
def mif2gmt(inmif,outgmt,mode='lines'):
    #
    if mode.upper() == 'LINES':
       data = read_mif_lines(inmif)
       #
    else:
       data = read_mif_pts(inmif)
       #
    with open(outgmt,'w') as fid:
        if mode.upper()=='LINES':
           for i in range(len(data)):
               fid.write('>\n')
               cdata = data[i]
               for j in range(cdata.shape[0]):
                  fid.write('%f %f\n' % (cdata[j,0],cdata[j,1]))
        else:
           for i in range(data.shape[0]):
               fid.write('%f %f\n' % (data[i,0],data[i,1]))
               
    return True
                   
#
def read_csm_metadata(indata):
    #
    # import stress model data shared from Southern California Earthquake Center
    # CSM, community stress model (CSM)
    # data and format descriptions are available at https://www.scec.org/research/csm
    #
    # stress data
    data1 = []
    # uncertainties 
    data2 = []
    #
    with open(indata,'r',encoding = "ISO-8859-1") as fid:
        for cline in fid:
            # cline = pSAR.util.bytestoutf8(cline)
            cline = cline.split('\n')[0]
            if '#' not in cline:
                ##
                tmp = cline.split()
                if tmp[3] == '1':
                    data1.append([float(ctmp) for ctmp in tmp])
                else:
                    data2.append([float(ctmp) for ctmp in tmp])
                #
            #
    return np.array(data1),np.array(data2)
#
###############################################################################
def UNRGPS4psvelo(infile,outh,outu):
    # for e format
    # x,y,vx,vy,vx_err,vy_err,name
    #
    data,sta = loadUNRGPS(infile)
    # 
    # output horizontol
    #
    fid = open(outh,'w')
    for i in range(data.shape[0]):
        fid.write('%f %f %f %f %f %f %f %s\n' % \
                  (data[i,0],data[i,1],data[i,2],data[i,3],\
                  data[i,5],data[i,6],0.001,sta[i]))
        #
    #
    fid.close()
    #
    # now work for verical components
    #
    fid = open(outu,'w')
    for i in range(data.shape[0]):
        fid.write('%f %f %f %f %f %f %f %s\n' % \
                  (data[i,0],data[i,1],0,data[i,5],\
                  0,data[i,7],0.001,sta[i]))
        #
    #
    fid.close()
    
def writeUNRGPS(outfile,gpsdata,gpssta):#
    #
    fid = open(outfile,'w')
    fid.write("Sta    Lon       Lat       de(m)     dn(m)     du(m)    sde(m)   sdn(m)   sdu(m)\n")
    fid.write('================================================================================\n')
    for i in range(gpssta.shape[0]):
        fid.write('%s %f %f %f %f %f %f %f %f\n' % \
                  (gpssta[i],gpsdata[i,0],gpsdata[i,1],gpsdata[i,2],\
                   gpsdata[i,3],gpsdata[i,4],gpsdata[i,5],\
                   gpsdata[i,6],gpsdata[i,7]))
        #
    fid.close()
    if os.path.exists(outfile):
        return True
    else:
        return False
    #
def loadUNRGPS(in_gps):
    #
    # NNR, University of Nevada, Reno
    #
    # this function is used first to read coseismic GPS data
    # released by Nevada Geodetic Laborotory
    # 
    gpsdata = []
    gpssta  = []
    counter = 0
    with open(in_gps) as fid:
        for cline in fid:
            # to jump two lines (header)
            if counter > 1:
                cline = cline.split('\n')[0].split()
                gpssta.append(cline[0])
                gpsdata.append([float(cline[i+1]) for i in range(len(cline)-1)])
                #
            #
            counter += 1
        #
    return np.array(gpsdata),np.array(gpssta)
#
def loadGMTtable(in_table):
    #
    data = []
    cdata = []
    with open(in_table,'r') as fid:
        for cline in fid:
            cline = cline.split('\n')[0]
            if '>' in cline:
                if len(cdata)>0:
                    data.append(np.array(cdata))
                #
                cdata = []
            else:
                cdata.append([float(cf) for cf in cline.split()])
            #
        #
        if len(cdata)>0:
           data.append(np.array(cdata))
    return data
#
def htmldescrip2list(inhtmlstring):
    #
    #
    table = etree.HTML(inhtmlstring).find("body/table")
    rows = iter(table)
    headers = [col.text for col in next(rows)]
    outvalue = []
    for row in rows:
      values = [col.text for col in row]
      outvalue.append(values)
    #
    return outvalue, headers
#
def geotif2polygon(ingeotif):
    info,ext = geotif2info(ingeotif)
    return pSAR.roipac.ext2polygon(ext)
#
def geotif2info(ingeotif):
    #
    # read meta info directly from a geotiff file
    # a ROI_PAC like info structure will be prepared
    # for further use.
    # by Wanpeng Feng, @SYSU,Guangzhou, 2019/07/19
    #
    info,keys = pSAR.roipac.roipac_info()
    #
    mytifID = gdal.Open(ingeotif, gdal.GA_ReadOnly)
    GTIFInfo = mytifID.GetGeoTransform()
    cols = mytifID.RasterXSize
    rows = mytifID.RasterYSize
    #
    info['WIDTH']       = cols
    info['FILE_LENGTH'] = rows
    info['X_FIRST']     = GTIFInfo[0]
    info['X_MAX']       =  GTIFInfo[0] + (cols-1) * GTIFInfo[1]
    info['Y_FIRST']     = GTIFInfo[3]
    info['Y_MIN']       = GTIFInfo[3] + (rows-1) * GTIFInfo[5]
    info['X_STEP']      = GTIFInfo[1]
    info['Y_STEP']      = GTIFInfo[5]
    #
    ext = [info['X_FIRST'],info['X_MAX'],info['Y_MIN'],info['Y_FIRST']]
    #
    return info,ext
###############################################################################  
def ptsinpolygon(pts,poly):
    #
    # return a boolen array to mark points inside
    # True for inside in default
    #
    polyID = shapely.geometry.Polygon(poly)
    flag = np.zeros(pts.shape[0],dtype=bool)
    #
    for i in range(pts.shape[0]):
        cptID = shapely.geometry.Point(pts[i,0],pts[i,1])
        if polyID.contains(cptID):
            flag[i] = True
            # print('Yeah. Got one!!!')
        #
    #
    return flag
#
#
def read_geotif(ingeotif,noband=1):
    #
    # a new function to read geotiff into memory
    # extension can also be returned at the same time.
    #
    # added by FWP, @SYSU,Guangzhou, 2019/07/19
    #
    raster_dataset = gdal.OpenEx(ingeotif, gdal.GA_ReadOnly)
    #
    # return bands of a geotiff file
    # by FWP, @SYSU, Guangzhou, 2019/07/19
    #
    # bands = raster_dataset.RasterCount
    #
    ulx, xres, xskew, uly, yskew, yres  = raster_dataset.GetGeoTransform()
    lrx = ulx + (raster_dataset.RasterXSize * xres)
    lry = uly + (raster_dataset.RasterYSize * yres)
    #
    #
    ext = [ulx,lrx,lry,uly]
    #
    # geo_transform = raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjectionRef()
    #
    data = raster_dataset.GetRasterBand(1).ReadAsArray()
    return data,ext,proj
#
def overlapOftwopolygons(poly_1,poly_2):
    #
    P1 = shapely.geometry.Polygon(poly_1)
    P2 = shapely.geometry.Polygon(poly_2)
    #
    if P1.intersects(P2):
       P3 = P1.intersection(P2)
       return P3.area
    else:
       return 0
   #
###############################################################################
def geojson_size(in_geojson,mode='ALL'):
    #
    # return total file size: numbers and space space required
    #
    s1data = loadgeojson(in_geojson)
    #
    tolsize = 0
    num = 0
    for cdata  in s1data:
       #
       if mode.upper() == 'ALL':
          tolsize += float(cdata['properties']['size'].split()[0])
          num += 1
       elif mode.upper() == 'DES':
           if cdata['properties']['orbitdirection'] == "DESCENDING":
              tolsize += float(cdata['properties']['size'].split()[0])
              num += 1
       elif mode.upper() == 'ASC':
           if cdata['properties']['orbitdirection'] == "ASCENDING":
              tolsize += float(cdata['properties']['size'].split()[0])
              num += 1
    return tolsize,num
#
def loadgeojson(in_geojson):
    #
    # a geojson file will be generated by sentinelsat in searching mode
    #
    # s1datas, the returned s1information, a list type 
    # by Wanpeng Feng, @CCRS/NRCan, 2018-11-24
    # 
    injsons = geojson.load(open(in_geojson,'r'))
    s1datas = injsons.features
    #
    return s1datas
def geojson_unique(ingeojsons):
    #
    # return unique geojsons
    #
    ids = np.zeros([len(ingeojsons),36],dtype=str)
    for i in range(len(ingeojsons)):
       #
       # times = ingeojsons[i]['properties']['beginposition']
       # OrbDir = ingeojsons[i]['properties']["orbitdirection"]
       # title = ingeojsons[i]['properties']['title']
       # track = ingeojsons[i]['properties']['lastrelativeorbitnumber']
       tmp = list(ingeojsons[i]['properties']['id'])
       ids[i,:] = tmp[:] 
       # 
    #
    u, indices = np.unique(ids, return_index=True,axis=0)
    return indices
#
def geotif_GetExtent(gt,cols,rows):
    #
    # return extension of a geotiff file.
    # by using gdal
    # added by Wanpeng Feng, @SYSU, 2019/03/15
    #
    ''' Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    '''
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])
            #print x,y
        yarr.reverse()
    return ext
#
#
def geotif_data(intif,bandNUM=1):
    #
    # read data from geotiff format file by using gdal  
    # added by Wanpeng Feng, @SYSU, 2019/03/15
    # 
    mytifID = gdal.Open(intif)
    #
    if mytifID is not None: 
       # print ("band count: " + str(src_ds.RasterCount))
       BNDS = mytifID.RasterCount
    else:
       BNDS = 0
    if BNDS > 0 and bandNUM <= BNDS:
       band = mytifID.GetRasterBand(1)
       arr = band.ReadAsArray()
       #Vmean = arr.mean()
    else:
       arr = None
    return arr,BNDS
    
def geotif_extent(intif):
    #
    # read geotiff files to return geo-extension, 4 corners (lon,lat)
    # added by Wanpeng Feng, @SYSU, Guangzhou
    # 
    mytifID = gdal.Open(intif)
    GTIFInfo = mytifID.GetGeoTransform()
    cols = mytifID.RasterXSize
    rows = mytifID.RasterYSize
    ext  = geotif_GetExtent(GTIFInfo,cols,rows)
    # 
    
    return ext
    
def aloscorners2polygon(roi):
    #
    poly = np.zeros([5,2])
    #
    croi = np.reshape(np.array(roi),[4,2])
    lats = np.copy(croi[:,0])
    lons = np.copy(croi[:,1])
    croi[:,0] = lons
    croi[:,1] = lats
    poly[0,:] = croi[0,:]
    poly[1,:] = croi[1,:]
    poly[2,:] = croi[3,:]
    poly[3,:] = croi[2,:]
    poly[4,:] = croi[0,:]
    return poly
def read_asfaloscsv(incsv):
    #
    noid = 0
    data = []
    with open(incsv,'r') as fid:
       for cline in fid:
           if noid > 0:
              cline = pSAR.util.bytestoutf8(cline)
              cline = cline.split('\n')[0]
              tmp = cline.split(',')
              # print(tmp)
              tmp = [ctmp.split('"')[1] for ctmp in tmp]
              data.append(tmp)
           #
           noid += 1
    #
    return data

def findfileinzip(inzip,insearch):
    #
    outfile = []
    # make sure input zip is a good one!!!
    # 
    try:
       zf = zipfile.ZipFile(inzip, 'r')
    except:
       zf = None
    if zf is not None:
       for cfile in zf.namelist():
           if insearch in cfile:
               outfile.append(cfile)
    return outfile
#
def s1zip2date(czip):
    '''
    extract date information directly from zip file
    '''
    # tmp = czip.split('_')[5][0:8]
    return czip.split('_')[5][0:8]
#
def s1kml2files(in_kml):
    #
    DOMTree    = xml.dom.minidom.parse(in_kml)
    collection = DOMTree.documentElement
    #
    tags       = collection.getElementsByTagName("Placemark")
    names  = []
    for ni in range(len(tags)):
        # 
        tagID = tags[ni].getElementsByTagName("name") # [0].childNodes
        #
        for nj in range(len(tagID)):
          cname = tagID[nj].childNodes[0].data
          names.append(cname+'.zip')
       #
    #
    return names
#
###############################################################################
#
def read_emsccsv(in_csv):
    counter = 0
    outdata = []
    outime  = []
    with open(in_csv,'r') as fid:
        for cline in fid:
           cline = pSAR.util.bytestoutf8(cline)
           if counter > 0:
              cline = cline.split('\n')[0]
              tmp   = cline.split(';')
              ctime = tmp[0]+'T'+tmp[1]
              outime.append(ctime)
              cdata = [float(tmp[3]),float(tmp[2]),float(tmp[4]),float(tmp[7])]
              outdata.append(cdata)
           counter += 1
    return np.array(outdata),np.array(outime)
#
###############################################################################
def grd2lonlat(ingrd):
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
    #
    return lon,lat
#
def grd_update(ingrd,data):
    # update data in ingrd
    #
    grdID = nc.Dataset(ingrd,'r+')
    grdID.variables['z'][:] = data
    grdID.close()
    return True
#
def grd_read(ingrd):
    #
    file_obj = nc.Dataset(ingrd)
    keys = file_obj.variables.keys()
    keys = list(keys)
    lon_key = 'lon'
    z_key   = 'z'
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
    if 'z' not in keys:
        z_key = 'Band1'
    #
    lon = file_obj.variables[lon_key][:]
    lat = file_obj.variables[lat_key][:]
    phs = file_obj.variables[z_key][:]
    # print(phs.shape)
    #
    if len(phs.shape)==1:
      for i in range(len(keys)):
          if 'dimen' in keys[i]:
            dim_key = keys[i]
            dims = file_obj.variables[dim_key][:]
            phs = np.reshape(phs,[dims[1],dims[0]])
    else:
      phs = np.flipud(phs)
    #
    lon[lon>180] = lon[lon>180] - 360. 
    ext = [lon.min(),lon.max(),lat.min(),lat.max()]
    #
    info,info_keys = pSAR.roipac.roipac_info()
    #
    info['FILE_LENGTH'] = phs.shape[0]
    info['WIDTH']       = phs.shape[1]
    info['X_STEP']      = (lon.max()-lon.min()) / (lon.shape[0] - 1)
    info['Y_STEP']      = (lat.min()-lat.max()) / (lat.shape[0] - 1)
    info['X_FIRST']     = lon.min()
    info['Y_FIRST']     = lat.max()
    #
    # tx,ty,uz,zl = pSAR.utm_conversion.from_latlon(\
    #              lat.mean(),lon.mean(), force_zone_number=None,\
    #              force_zone_letter=None)
    #
    #
    return info,ext,phs
#
def read_usgscsv(in_csv):
    #
    counter = 0
    outdata = []
    outtime = []
    with open(in_csv,'r') as fid:
      #
      for cline in fid:
         cline = pSAR.util.bytestoutf8(cline)
         #
         if counter > 0:
            cline = cline.split('\n')[0]
            tmp = cline.split(',')
            #
            # fix an error by FWP, @SYSU, Guangzhou, 2019/07/01
            #
            # outtime.append(tmp[0])
            try:
               outtime.append(tmp[0])
               cdata = [float(tmp[i]) for i in range(1,5)]
               outdata.append(cdata)
            except:
               print(cline)
         else:
            print(cline)
         counter += 1
    return np.array(outdata),outtime
#
###############################################################################
#
def read_psvelo(in_data):
    #
    # only one formwat is supported for now
    # x y vx vy sigx sigy cor [name]
    sts = []
    vel = []
    with open(in_data,'r') as fid:
       for cline in fid:
           cline = pSAR.util.bytestoutf8(cline)
           cline = cline.split('\n')[0].split()
           if len(cline) == 8:
              sts.append(cline[6])
           #
           cdata = [float(cline[i]) for i in range(7)]
           vel.append(cdata)
    #
    vel = np.array(vel)
    return vel, sts
#
def bytestoutf8(t):
    '''
    To convert a bytes-like variable to utf8
    '''
    if isinstance(t,bytes):
        return t.decode("utf-8")
    return t
#
def zipinlist(czip,ziplist):
    '''
    Check if czip exists already
    Yes, return a True or
    No,  return a False
    '''
    flag = False
    zipname = os.path.basename(czip)
    for index in range(ziplist.shape[0]):
        if zipname in ziplist[index]:
            flag = True 
    #
    return flag
#
###############################################################################
def auig2csv2data(incsv):
    #
    # Read ALOS2 data into separate KML with beam and track information
    # by Wanpeng Feng, @CCRS/NRCan, 2017-05-02
    #
    outdata = []
    counter = 0
    atts    = []
    with open(incsv,'r') as csvid:
        csvreader = csv.reader(csvid,delimiter=',')
        for row in csvreader:
            #
            counter += 1
            if counter == 1:
                atts = np.array(row).T
            if (len(row) > 0 and counter > 1):
               nrow = np.array(row).T
               #print(nrow.shape)
               outdata.append(nrow)
        #
    #
    return np.array(outdata),atts
#
def seasonalsearch(indate,smonth,emonth):
    '''
    indate a time informaiton in yyyymmddThhMMss.ss
    
    '''
    if emonth < smonth:
       smonth = [smonth,0]
       emonth = [12,emonth]
    else:
       smonth = [smonth]
       emonth = [emonth]
    # f
    cmonth = int(indate[4:6])
    #
    for ind in range(len(smonth)):
      if (cmonth >= smonth[ind] and cmonth <= emonth[ind]):
        flag = True
      else:
        flag = False
      if ind == 0:
          finalflag = flag
      else:
          finalflag = finalflag or flag
          
    #
    return finalflag      
#
###############################################################################
def locs2disk(in_locs,stas,outfile):
    #
    # A function to write locations, values and other numerical information and 
    # station names into an ascii file
    # developed by Wanpeng Feng, @NRCan, 2017-02-20
    #
    fid = open(outfile,'w')
    for ind in range(in_locs.shape[0]):
        cdata = np.reshape(in_locs[ind,:],in_locs.shape[1])
        #
        cstr  = '   '.join([str(ci) for ci in cdata])
        cstr  = cstr+'    '+stas[ind]
        fid.write("%s\n" % cstr)
    #
    fid.close()
    if os.path.exists(outfile):
        return True
    else:
        return False
#        
###############################################################################
#        
def locsofpts(in_list):
    '''
    To read an ascii file that records points information including 
    locations and station names
    
    for examples,
    <lon> <lat> <station_names>
    '''
    locs = []
    stas = []
    fid = open(in_list,'r')
    for cline in fid:
        cline = cline.split('\n')[0]
        tmp   = cline.split()
        locs.append([float(tmp[0]),float(tmp[1])])
        stas.append(tmp[2])
    #
    return np.array(locs),np.array(stas)
#    
###############################################################################  
# 
def s1geojsonTOkml(s1_json,outkml):
    #
    s1_data = loadS1geojson(s1_json)
    #
    kml_s,kml_e,polystr_s,polystr_e = kml_poly()
    #
    fid = open(outkml,'w')
    fid.write(kml_s % outkml)
    #
    for ind in range(len(s1_data)):
        #
        cpoly = s1_data[ind]["geometry"]["coordinates"]
        # print(cpoly)
        cpoly = np.array(cpoly)
        #
        if len(cpoly.shape)>2:
           cpoly = cpoly[0,:,:]
        #
        #
        descri = s1_data[ind]["properties"]
        outstr = pS1.s1strcut2str(descri)
        
        cname = descri["identifier"]
        #
        fid.write(polystr_s % (cname,outstr))
        #
        for index in range(cpoly.shape[0]):
            #
            outloc = '              ' + str(cpoly[index,0]) + ',' + \
                                        str(cpoly[index,1]) + ',0\n'
            fid.write(outloc)
        #
        fid.write(polystr_e)
        #
    #    
    fid.write(kml_e)
    fid.close()
    #
    if os.path.exists(outkml):
        return True
    else:
        return False
###############################################################################
def loadS1geojson(in_geojson):
    #
    # a geojson file will be generated by sentinelsat in searching mode
    #
    injsons = geojson.load(open(in_geojson,'r'))
    s1datas = injsons.features
    return s1datas
#
###############################################################################
def ext2geojson(ext,outname):
    #
    #
    polygon = pSAR.roipac.ext2polygon(ext)
    s_sTr = \
'''{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
    '''
    e_sTr=\
    '''
              ]
        ]
      }
    }
  ]
}
    '''
    fid = open(outname,'w')
    fid.write(s_sTr)
    #
    for ni in range(polygon.shape[0]):
        #
        fid.write('               %s\n' % "[")
        fid.write('                  %f,\n' % polygon[ni,0])
        fid.write('                  %f\n' % polygon[ni,1])
        if ni == polygon.shape[0]-1:
            fid.write('               %s\n' % "]")
        else:
            fid.write('               %s\n' % "],")
    fid.write(e_sTr)
    fid.close()
    #
    if os.path.exists(outname):
        return True
    else:
        return False
###############################################################################        
def hyDD_read(inhyDD,refdate=None):
    #
    data = np.loadtxt(inhyDD)
    lons = data[:,2]
    lats = data[:,1]
    deps = data[:,3]
    mags = data[:,16]
    yyyy = data[:,10]
    mm   = data[:,11]
    dd   = data[:,12]
    yyyy = yyyy.astype('int')
    mm   = mm.astype("int")
    dd   = dd.astype("int")
    yyyy = np.array(map(str,yyyy))
    mm   = np.array(map(str,mm))
    dd   = np.array(map(str,dd))
    dates= []
    diffdates= np.copy(lons) * 0.
    #
    for index in range(dd.shape[0]):
        cmm,cdd = mm[index],dd[index]
        if len(cmm)==1:
            cmm = '0'+cmm
        if len(cdd)==1:
            cdd = '0'+cdd
        dates.append(yyyy[index] + cmm + cdd)
        if refdate is not None:
            # sbas has been transitioned to "ts" since early 2017
            #
            diffdates[index] = pSAR.ts.diff2dates(refdate,\
                     yyyy[index] + cmm + cdd)
    dates = np.array(dates)
    #
    return lons,lats,deps,mags,diffdates,dates
#
###############################################################################
#
def gcmtndks2output(inndks,outgmt,magthreshold=0.,minlon=-180.,maxlon=180.,\
                    minlat=-90.,maxlat=90.):
    #
    for ni in range(len(inndks)):
        gcmtndk4gmtplot(inndks[ni],outgmt,magthreshold=magthreshold,\
                    minlon=minlon,maxlon=maxlon,minlat=minlat,maxlat=maxlat)
        
    #
    return True
###############################################################################
#
def gcmtndk4gmtplot(inndk,outgmt,magthreshold=None,minlon=-180.,maxlon=180.,\
                    minlat=-90.,maxlat=90.,strikeonly=False,thrustonly=False,\
                        normalonly=False):
    
    #
    gcmtinfo,gcmtnames = gcmtndk(inndk)
    #
    #
    print(" Tol %d events." % gcmtinfo.shape[0])
    # adjusting all events ranging from -180 to 180 in longititude
    # by Wanpeng Feng, @Ottawa, 2017-01-02
    #
    gcmtinfo[gcmtinfo[:,0]>180,0] = gcmtinfo[gcmtinfo[:,0]>180,0] - 360
    print(" Tol %d events." % gcmtinfo.shape[0])
    #
    #
    print(" ROI: %f/%f/%f/%f " % (minlon,maxlon,minlat,maxlat))
    #
    flag1 = np.logical_and(gcmtinfo[:,0]>=minlon,gcmtinfo[:,0]<=maxlon)
    flag2 = np.logical_and(gcmtinfo[:,1]>=minlat,gcmtinfo[:,1]<=maxlat)
    #
    # slice arrange based on given ROI region by giving 
    # (minlon,maxlon,minlat,maxlat)
    gcmtnames = gcmtnames[np.where(flag1 & flag2),:][0]
    gcmtinfo  = gcmtinfo[np.where(flag1 & flag2),:][0]
    #
    if gcmtinfo.shape[0]>0 and magthreshold is not None:  
       #                 
       gcmtnames = gcmtnames[gcmtinfo[:,6]>magthreshold,0]
       gcmtinfo  = gcmtinfo[gcmtinfo[:,6]>magthreshold,:]
    #
    print(" Now you have %d events left after filtering..." % gcmtinfo.shape[0])
    #
    #
    # get arrays of strike, dip and rake for first planes
    #
    mstr = gcmtinfo[:,3]
    mdip = gcmtinfo[:,4]
    mrak = gcmtinfo[:,5]
    flag = pSEIS.arr_mecsort(mstr,mdip,mrak)
    # 
    # print(flag.shape,mstr.shape)
    #
    if strikeonly:
        #
        gcmtinfo = gcmtinfo[flag==1,:]
        gcmtnames = gcmtnames[flag==1]
        # print(gcmtinfo.shape)
    if thrustonly:
        #
        gcmtinfo = gcmtinfo[flag==3,:]
        gcmtnames = gcmtnames[flag==3]
    if normalonly:
        #
        gcmtinfo = gcmtinfo[flag==2,:]
        gcmtnames = gcmtnames[flag==2]
    # print(gcmtinfo.shape)                                    #
    print(" Now you have %d events left after filtering..." % gcmtinfo.shape[0])
    if gcmtinfo.shape[0] > 0:
       #
       fid = open(outgmt,'w')
       for index in range(gcmtinfo.shape[0]):
           #
           fid.write("%f %f %f %f %f %f %f %f %f %s\n" % (\
                     gcmtinfo[index,0],gcmtinfo[index,1],\
                     gcmtinfo[index,2],gcmtinfo[index,3],\
                     gcmtinfo[index,4],gcmtinfo[index,5],\
                     gcmtinfo[index,6],gcmtinfo[index,7],\
                     gcmtinfo[index,8],gcmtnames[index]))
    
       fid.close()
       #
    if os.path.exists(outgmt):
        return True
    else:
        return False
#        
###############################################################################
#  
def gcmtndk(inndk):
    #
    fid = open(inndk,'r')
    nline = 0
    gcmt_a   =[]
    gcmt_name=[]
    goflag = True
    for cline in fid:
        cline = bytestoutf8(cline)
        cline = cline.split('\n')[0]
        if cline[0] == "<":
            goflag = False
        else:
            goflag = True
        if goflag:
           nline += 1
        if nline > 5:
            nline = 1
        #
        if nline == 1 and goflag:
           #
           tmp = cline.split()
           dbname    = cline[0:4]
           eventdate = cline[5:15]
           eventtime = cline[16:26]
           #
           dbname = dbname.rstrip().lstrip()
           #
           if dbname == "":
              #
              mag1,mag2  = float(tmp[5]),float(tmp[6])
              eventinfo  = [float(tmp[3]),float(tmp[2]),float(tmp[4]),mag2]
           else:
              mag1,mag2  = float(tmp[6]),float(tmp[7])
              eventinfo  = [float(tmp[4]),float(tmp[3]),float(tmp[5]),mag2]
           #
           # print(eventdate,eventtime)
           #
           eventloc   = cline[56:81]  
           #
        if nline == 5 and goflag:
           #
           planes = cline[57:81].split()
           planes = np.array(planes, dtype='|S4')
           planes = planes.astype(np.float32)
           #
           gcmt_a.append([eventinfo[0],eventinfo[1],eventinfo[2],planes[0],\
                planes[1],planes[2],eventinfo[3],eventinfo[0],eventinfo[1]])
           gcmt_name.append([eventdate+"_"+eventtime,dbname,eventloc])
           #
        # print(eventinfo,eventloc)
    #
    fid.close()
    gcmt_a    = np.array(gcmt_a)
    gcmt_name = np.array(gcmt_name) 
    return gcmt_a,gcmt_name
#    
############################################################################### 
#   
def imgdataconv(ingeotiff,grd,ishelp=False,of='GMT',ot='Float32'):
    #
    if ishelp:
       print("%s" % sys.argv)
       print("+++++++++++++++++++++++")
       print("To convert image data format by gdal_translate")
       print("Developed by Wanpeng Feng, @NRCan, 2016-11-14")
       return False
    #
    if not os.path.exists(ingeotiff):
       print("%s does not exist. Check it before to rerun." % ingeotiff)
       return False
    #
    command_STR=("gdal_translate -of %s -ot %s %s %s" % (of,ot,ingeotiff,grd))
    flag,info,errors = pdata_run(command_STR)
    if flag == 0:
       return True
    else:
       print(info)
       return False
#
###############################################################################
def GEGRL_Interseismic_GPS(infile):
    #
    names = []
    data  = []
    fid = open(infile,'r')
    for cline in fid:
      cline = pSAR.util.bytestoutf8(cline)
      cline = cline.split('\n')[0].split()
      names.append(cline[0])
      cdata = np.array(cline[1:8])
      cdata = cdata.astype(np.float32)
      data.append([cdata[0],cdata[1],cdata[2],cdata[3],cdata[4],cdata[5],cdata[6]])
    fid.close()
    #
    data         = np.array(data)
    gpsstas      = np.array(names)
    #
    gpsdata      = np.zeros([data.shape[0],8])
    gpsdata[:,0] = data[:,0]
    gpsdata[:,1] = data[:,1]
    gpsdata[:,2] = data[:,2]
    gpsdata[:,3] = data[:,4]
    gpsdata[:,4] = data[:,3]
    gpsdata[:,5] = data[:,5]
    #
    return gpsdata,gpsstas
#
###############################################################################
def pdata_run(sTr):
    #
    #
    print(' pGAMMA: %s' % sTr)
    fout          = open('pdata_error.inf','a')
    output        = subprocess.Popen(sTr,stdout=subprocess.PIPE,\
                                     stderr=fout,shell=True)
    flag          = output.wait()
    prints,errors = output.communicate()
    fout.close()
    #
    return flag,prints,errors
    
###############################################################################
def YK17_intgps(infile):
    #
    sta = []
    gps = []
    with open(infile,'r') as fid:
        #
        for cline in fid:
            cline = cline.split('\n')[0]
            tmp = cline.split()
            sta.append(tmp[0])
            gps.append([float(tmp[1]),float(tmp[2]),\
                        float(tmp[3]),float(tmp[4]),0,0,float(tmp[5]),0.])
    return np.array(gps),np.array(sta,dtype='str')
#
def NZ16_cosgps(infile):
    '''
    The function to read coseismic GPS data for 
    the 2016 Mw7.8 New Zealand earthquake
    '''
    if not os.path.exists(infile):
        print(" %s cannot be found. Check first." % infile)
        sys.exit(-1)
    #
    fid = open(infile,'r')
    counter = 0
    sta = []
    gps = []
    for cline in fid:
        counter += 1
        if counter > 2:
           cline = cline.split('\n')[0] 
           tmp = cline.split()
           sta.append(tmp[0])
           gps.append([float(tmp[1]),float(tmp[2]),\
                       float(tmp[3]),float(tmp[4]),\
                       float(tmp[5]),float(tmp[6]),\
                       float(tmp[7]),float(tmp[8])])
    #
    fid.close()
    sta = np.array(sta)
    gps = np.array(gps)
    return gps,sta

#
###############################################################################
#
def loadKMLFile(fname):
    tree = ET.parse(fname)  # Build the element tree (in memory)...
    return tree             # ... and return the element tree as the result
#    
def saveKMLFile(fname, tree):
    '''Write current content of the tree to the file of the fname.'''    
    tree.write(fname, 'utf-8', True)

###############################################################################
#
def lls2dist(p1,p2):
    '''
    To calculate the distance between two points
    return the distance in kml between two points (p1,p2)
    
    '''
    #
    x1,y1,zone,zonel = pSAR.utm_conversion.from_latlon(p1[1],p1[0])
    x2,y2,zone,zonel = pSAR.utm_conversion.from_latlon(p2[1],p2[0],\
                                        force_zone_number=zone,\
                                        force_zone_letter=zonel)
    dist  = np.hypot(x1-x2,y1-y2)
    dist  = dist / 1000
    #
    return dist
###############################################################################
def import_dartloc(indart):
    #
    fid = open(indart,'r')
    dartloc  = []
    dartname = []
    for cline in fid:
        cline = cline.split('\n')[0]
        tmp   = cline.split()
        tmp   = [x for x in tmp if x]
        # print(cline)
        dartloc.append([float(tmp[2]),float(tmp[1])])
        dartname.append(tmp[0])
    #
    dartloc = np.array(dartloc)
    #
    dartname = np.array(dartname)
    return dartloc,dartname        
#        
###############################################################################
###############################################################################      
def import_usgseq(incvs,jumpline=1):
    #
    fid = open(incvs,'r')
    outdata = []
    counter = 0
    for cline in fid:
        counter+= 1
        if counter > jumpline:
           cline = cline.split('\n')[0]
           tmp   = cline.split(',')
           #print(tmp[0])
           dt_info =  dt.strptime(tmp[0],'%Y-%m-%dT%H:%M:%S.%fZ')
           years   = dt_info.year + float(dt_info.strftime('%j'))/365.
           #
           #
           # year, lon, lat, depth, mag
           outdata.append([years,float(tmp[2]),float(tmp[1]),\
                           float(tmp[3]),float(tmp[4])])
    #
    fid.close()
    outdata = np.array(outdata)
    # print(outdata[:,0])
    return outdata
#
###############################################################################
def import_mgmt(in_gmt):
    data = []
    cdata = []
    with open(in_gmt,'r') as fid:
        for cline in fid:
            cline = bytestoutf8(cline)
            cline = cline.split('\n')[0]
            #
            if '>' in cline:
                #
                if len(cdata)> 0:
                    data.append(np.array(cdata))
                cdata = []
            else:
                tdata = cline.split()
                tdata = [float(tdata[i]) for i in range(len(tdata))]
                cdata.append(tdata)
        #
        if len(cdata) > 0:
           data.append(np.array(cdata))
        #
    return data     
#             
def import_InSAR_inp(inp,xyz):
    #
    data  = np.loadtxt(inp)
    fid   = open(xyz,'r')
    cpoly = [] 
    tpoly = [] # totalpoly
    mindex = []
    ninp = 0
    for cline in fid:
        cline = bytestoutf8(cline)
        cline = cline.split('\n')[0]
        if ">" in cline:
           ninp = 0
           cpoly = []
        else:
           cline = cline.split('\n')[0]
           tmp = cline.split(' ')
           tmp = [x for x in tmp if x]
           cpoly.append([float(tmp[0]),float(tmp[1])])
           # tpoly.append([float(tmp[0]),float(tmp[1])])
           ninp += 1
        if ninp == 5:
           ninp = 0
           npoly = np.array(cpoly)
           cpoly = []
           meanx = np.mean(npoly[:,0])
           meany = np.mean(npoly[:,1])
           mdist = np.sqrt((data[:,0] - meanx) ** 2 + (data[:,1] - meany) ** 2)
           ind   = np.argmin(mdist)
           mindex.append(ind)
           cdata = np.reshape(npoly,[1,10])
           tpoly.append(cdata)
    fid.close()
    #  
    tpoly = np.array(tpoly)
    mindex = np.array(mindex)
    data   = data[mindex,:]
    return tpoly,data
#  
###############################################################################
#     
def import_downsampledINP(inp,xyz,gmt_outpoly):
    #
    data  = np.loadtxt(inp)
    fid   = open(xyz,'r')
    outid = open(gmt_outpoly,'w')
    ninp  = 0
    cpoly = [] 
    tpoly = [] # totalpoly
    for cline in fid:
        cline = bytestoutf8(cline)
        cline = cline.split('\n')[0]
        if ">" in cline:
           ninp = 0
        else:
           cline = cline.split('\n')[0]
           tmp = cline.split(' ')
           tmp = [x for x in tmp if x]
           cpoly.append([float(tmp[0]),float(tmp[1])])
           tpoly.append([float(tmp[0]),float(tmp[1])])
           ninp += 1
        if ninp == 5:
           #
           ninp = 0
           npoly = np.array(cpoly)
           cpoly = []
           meanx = np.mean(npoly[:,0])
           meany = np.mean(npoly[:,1])
           mdist = np.sqrt((data[:,0] - meanx) ** 2 + (data[:,1] - meany) ** 2)
           ind   = np.argmin(mdist)
           val   = data[ind,2]
           #
           outid.write("> -Z%f \n" % val)
           cpoly = []
           #
           for ck in range(5):
               outid.write("%f %f\n" % (npoly[ck,0],npoly[ck,1]))
           #
    #
    fid.close()
    outid.close()          
    if os.path.exists(gmt_outpoly):
       tpoly = np.array(tpoly)
       return tpoly,data,True
    else:
       return tpoly,data,False
#
###############################################################################  
#
def export_psmeca(outfoc,data,stas):
    #
    dfmt = ['%f' for i in range(9)]
    dfmt = ' '.join(dfmt)
    if len(stas) == 0:
        #
        flag = False
        fmt = dfmt+'\n'
    else:
        flag = True
        fmt = dfmt + ' %s\n'
    with open(outfoc,'w') as fid:
        for i in range(data.shape[0]):
            cdata = [data[i,j] for j in range(9)]
            if flag:
               #
               fid.write(fmt % tuple(cdata+[stas[i]]))
            else:
               fid.write(fmt % tuple(cdata))
    return True
#
###############################################################################
#
def import_psmeca(infoc,mode='A'):
    #
    data = []
    names= []
    #
    fid = open(infoc,'r')
    for cline in fid:
        cline = cline.split('\n')[0]
        tmp   = cline.split(' ')
        # remove space only
        tmp = [x for x in tmp if x]
        #
        # This is only option supported at the moment.
        # 2018-06-12
        #
        if mode.upper()=='A':
           data.append([float(tmp[0]),float(tmp[1]),float(tmp[2]),float(tmp[3]),\
                     float(tmp[4]),float(tmp[5]),float(tmp[6]),\
                     float(tmp[7]),float(tmp[8])])
           if len(tmp) > 9:
              names.append(tmp[9])
           else:
              names.append('')
    #
    data = np.array(data)
    return data,names         
    
###############################################################################    
def lonlat2utm(lon,lat,zoneNum,zoneLetter):
    #
    utmx = np.copy(lon)
    utmy = np.copy(lat)
    for ni in range(lon.shape[0]):
        utmx[ni],utmy[ni] = pSAR.from_latlon(lat[ni],lon[ni],\
                               force_zone_numer=zoneNum,force_zone_letter=zoneLetter)
    #
    return utmx,utmy
###############################################################################
def utm2lonlat(x,y,zoneNum,zoneLetter):
    outx = np.copy(x)
    outy = np.copy(y)
    for ni in range(x.shape[0]):
        outy[ni],outx[ni] = pSAR.utm_conversion.to_latlon(x[ni],y[ni],zoneNum,zoneLetter)
    #
    return outx, outy

############################################################################### 
def kml_tabel(in_str):
    #
    # in_str, a list for keys used for a built-up of kml table
    #
    kml_tab_s = \
'''
<ExtendedData>
    <SchemaData schemaUrl="#OGRGeoJSON">
'''
    kml_tab_c = ['\t<SimpleData name="%s">%%s</SimpleData>\n' % c_att for c_att in in_str]
    kml_tab_c = ''.join(kml_tab_c)
    kml_tab_e = \
'''</SchemaData>
</ExtendedData>
'''
    kml_tab = kml_tab_s + kml_tab_c + kml_tab_e
    return kml_tab
#
#
#
def kml_polyline():
    #
    # color 
    # ff0000ff red
    # ff00ff00  solid green
    kml_s='''<?xml version="1.0" encoding="utf-8" ?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document><Folder><name>OGRGeoJSON</name>
<Schema name="OGRGeoJSON" id="OGRGeoJSON">
	<SimpleField name="Name" type="string"></SimpleField>
	<SimpleField name="Description" type="string"></SimpleField>
	<SimpleField name="ltype" type="string"></SimpleField>
	<SimpleField name="Source" type="string"></SimpleField>
	<SimpleField name="Y" type="float"></SimpleField>
	<SimpleField name="X" type="float"></SimpleField>
	<SimpleField name="Type" type="string"></SimpleField>
	<SimpleField name="Id" type="int"></SimpleField>
</Schema>'''
    kml_polyline='''<Placemark>
	<name>%s</name>
	<Style><LineStyle><color>ff0000ff</color></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style>
	<ExtendedData><SchemaData schemaUrl="#OGRGeoJSON">
		<SimpleData name="Name">%s</SimpleData>
		<SimpleData name="ltype">1411</SimpleData>
		<SimpleData name="Source">FWP</SimpleData>
		<SimpleData name="Y">%f</SimpleData>
		<SimpleData name="X">%f</SimpleData>
        <SimpleData name="Dip">%f</SimpleData>
		<SimpleData name="Strike">%f</SimpleData>
	</SchemaData></ExtendedData>
      <LineString><coordinates>%s</coordinates></LineString>
  </Placemark>'''
    kml_e=\
'''</Folder></Document></kml>'''
    return kml_s,kml_e,kml_polyline

#
###############################################################################
def kml_pts():
    kml_s='''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.0"> <Document>'''
    kml_e='''</Document>
</kml>'''
    pts_s=\
'''     <Placemark>
          <name>%s</name>
          <description>%s</description>
          <styleUrl>#m_ylw-pushpin</styleUrl>
          <Point>
            <Camera>
                  <altitudeMode>clampedToGround</altitudeMode>
            </Camera>
            <styleUrl>#m_ylw-pushpin</styleUrl>
            <coordinates>%s</coordinates>
          </Point>
        </Placemark>\n'''
    return kml_s,kml_e,pts_s
#
###############################################################################
#
def kml_poly(in_tab=None,poly_color="ff7faa00"):
    #
    # the change made on 25/11/2018 may cause some problems in the previous scripts
    # Now the fill color can be allowed to specify for any individual polygon.
    # by Wanpeng Feng, @SYSU, 2018-11-25
    #
    kml_s=\
'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>%s</name>
    <open>1</open>
        <Style id="s_ylw-pushpin">
                <IconStyle>
                        <scale>1.1</scale>
                        <Icon>
                        <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
                        </Icon>
                        <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
                </IconStyle>
                <LineStyle>
                        <color>ff7faa00</color>
                        <width>3</width>
                </LineStyle>
                <PolyStyle> 
                        <color>7f0000ff</color>
                        <colorMode>normal</colorMode>
                        <fill>1</fill>
                </PolyStyle>
        </Style>\n'''
    kml_e=\
    ''' </Document>
</kml>'''
    #
    # description
    #
    kml_tab = '<description>%s</description>'
    if in_tab is not None:
       kml_tab = kml_tabel(in_tab)
    #
    if poly_color is not None:
       polystr_s=\
'''     <Placemark> 
          <name>%%s</name>%s
          <Polygon>
            <tessellate>1</tessellate>
            <extrude>1</extrude>
            <altitudeMode>clampedToGround</altitudeMode>
            <style>
              <LineStyle>
			   <color>ff7faa00</color>
			   <width>5</width>
		      </LineStyle>
		      <PolyStyle>
			    <color>%s</color>
			    <outline>1</outline>
		      </PolyStyle>
            </style>
            <outerBoundaryIs>
            <LinearRing>
              <coordinates>\n''' % (kml_tab,poly_color)
    else:
       polystr_s=\
'''     <Placemark> 
          <name>%%s</name>%s
          <Polygon>
            <tessellate>1</tessellate>
            <extrude>1</extrude>
            <altitudeMode>clampedToGround</altitudeMode>
            <style>
              <LineStyle>
			   <color>ff7faa00</color>
			   <width>5</width>
		      </LineStyle>
		      <PolyStyle>
			    <color>%%s</color>
			    <outline>1</outline>
		      </PolyStyle>
            </style>
            <outerBoundaryIs>
            <LinearRing>
              <coordinates>\n''' % kml_tab
       
                 
    polystr_e=\
'''         </coordinates>
            </LinearRing>
            </outerBoundaryIs>
          </Polygon>
        </Placemark>\n'''
    #
    return kml_s,kml_e,polystr_s,polystr_e
###############################################################################  
def asfcsv(incsv):
    #
    atts = []
    data = []
    with open(incsv,'r') as fid:
        atts = fid.readline().split('\n')[0].split(',')
        for cline in fid:
            tmp = cline.split('\n')[0].split(',')
            tmp = [ctmp.split('"')[1] for ctmp in tmp]
            data.append(tmp)
    #
    return data,atts
#
def strarr_to_num(inlist):
    #
    # convert string list to numeric list
    #
    counter = 0
    for celement in inlist:
        inlist[counter] = float(celement)
        counter += 1
    #
    return inlist
###############################################################################
def import_metois2012GPS(infile,outgps):
    #
    # read GPS file that was released in Metois 2012, JGR paper
    #
    fid = open(infile,'r')
    outloc=[]
    outsta=[]
    for cline in fid:
        tmp = cline.split('\n')[0]
        tmp = tmp.split('\t')
        # remove space
        tmp = [x for x in tmp if x]
        tmp = [np.nan if x=="-" else x for x in tmp]
        #
        lon,lat,ev,ee,nv,ne,uv,ue=float(tmp[1]),float(tmp[2]),\
                                  float(tmp[3]),float(tmp[6]),\
                                  float(tmp[4]),float(tmp[7]),\
                                  float(tmp[5]),float(tmp[8])
        outsta.append(tmp[0])
        outloc.append([lon,lat,ev/1000,nv/1000,\
                       ee/1000,ne/1000,uv/1000,ue/1000])
    #
    outloc = np.array(outloc)
    #
    write_gps(outloc,outsta,outgps,njump=6);
    #
###############################################################################
def import_gps(infile,model=1,njump=None):
    '''
    Read gps in a specific format that was used by Dr. Yunfeng Tian, for Chile 
    GPS data
    '''
    fid    = open(infile,'r')
    outloc = []
    outsta = []
    no     = 0
    for cline in fid:
        #
        # Ignore the comments with a "#" start
        #
        no += 1
        if "*" in cline:
            startid = no
        if no > startid:
           tmp = cline.split('\n')[0]
           tmp = tmp.split('\r')[0]
           tmp = tmp.split(' ')
           tmp = [x for x in tmp if x]
           #
           if model == 1:
              lon,lat,ev,ee,nv,ne,uv,ue=tmp[0],tmp[1],tmp[4],tmp[5],tmp[2],\
              tmp[3],tmp[6],tmp[7]
           else:
              lon,lat,ev,ee,nv,ne,uv,ue=tmp[0],tmp[1],tmp[10],tmp[5],tmp[9],\
              tmp[3],tmp[11],tmp[7]
           #
           staname=tmp[8].upper()
           outloc.append([float(lon),float(lat),float(ev),float(nv),float(ee),\
                          float(ne),float(uv),float(ue)])
           outsta.append(staname)
    #
    outloc = np.array(outloc)
    return outloc,outsta
###############################################################################
def write_gps_psvelo(data,sta,outname):
    #
    # output a file in "e" format defined in psvelo
    fid = open(outname,'w')
    for i in range(data.shape[0]):
        #
        if len(sta) > 0:
            csta = sta[i]
        else:
            csta = ''
        fid.write('%f %f %f %f %f %f %f %s\n' % (data[i,0],data[i,1],data[i,2],\
                                                 data[i,3],data[i,4],data[i,5],\
                                                 data[i,6],csta))
    #
    fid.close()
    #
    return True
def write_gps(data,sta,outname,njump=1):
    #
    # write GPS to disk in a specific format, from Dr. Tian
    #
    data[data[:,0]>180,0] = data[data[:,0]>180,0] - 360
    fid = open(outname,'w')
    for ni in range(njump-1):
        fid.write("# GPS Data in Tian's format.\n")
    #
    fid.write("*   lontitude    latitude      disp_N    "+\
              "sig_N    disp_E     sig_E  disp_U     sig_U  site \n")
    ndata = data.shape[0]
    for ni in range(ndata):
        #
        # a bug was fixed...
        # by Wanpeng Feng, @Ottawa, 2017-01-02
        #
        fid.write("%f %f %f %f %f %f %f %f %s\n" % (data[ni,0],data[ni,1],\
                                                    data[ni,3],data[ni,5],\
                                                    data[ni,2],data[ni,4],\
                                                    data[ni,6],data[ni,7],\
                                                    sta[ni]))
    #
    fid.close()
