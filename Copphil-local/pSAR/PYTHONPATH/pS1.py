#! /usr/bin/env python
###############################################################################
# Sentinel-1 Utility Module for GMTSAR and InSAR Workflows
# Reorganized by Wanpeng Feng from pDATA and pGAMMA
# Created on July 27, 2017 | Updated by Bingquan Li and Ling Chang, June 24, 2025
#
# Purpose:
#   Provide functions for extracting metadata, parsing XML, selecting orbit files,
#   generating region of interest (ROI) geometries, and supporting Sentinel-1
#   preprocessing tasks for InSAR applications.
###############################################################################
import numpy as np
import os
import pSAR
import pDATA
import datetime
import shutil
import glob
import sys
from datetime import datetime, timedelta


#
try:
    from shapely.geometry import Polygon
except:
    pass
#
try:
    import geojson
except:
    1
    #
import xml.dom.minidom,glob
import zipfile
import shutil
#
def eof_res_fix(infile):
    #
    # since 31 Jan, 2023, the resorb EOF has thre lines more than previouse file, so remove the space lines 
    # due to this change, GMTSAR cannot work properly...
    # we temporarily to fix this issue by fixing the EOF 
    # written by Wanpeng Feng, @SYSU, Guangzhou, 2023/02/07
    #
    fid_out = open('_tmp.EOF','w')
    #
    with open(infile,'r') as fid:
        for cline in fid:
            # print(len(cline))
            if len(cline)>1:
                fid_out.write('%s' % cline)
                #
            #
        #
    fid_out.close()
    #
    if os.path.exists('_tmp.EOF'):
        os.system('mv _tmp.EOF %s' % infile)

#
def s1times2orb(startime,stoptime,model="RESORB",orbdir=None,mission='S1A',\
                        orbs=None,times=None,update=False):
    #
    # a new verion to avoid searching orbit path...
    # this is much faster than the oldversion of s1time2statevector()....
    #
    if orbdir is None:
       topdir = os.environ['S1_ORB']
       orbdir = topdir+'/aux_'+model.lower()
    #   
    st = pSAR.ts.timestr2jd(startime)
    et = pSAR.ts.timestr2jd(stoptime)
    #
    orbdir_tmp = orbdir+'/%s/' % mission.upper()
    #
    avt = (st+et)/2.
    #
    if orbs is None or times is None or update:
      if model.upper() == "RESORB":
         if orbdir is not None:
            # print(model,orbdir,mission)
            orbs,times = s1_resorb(in_resorb_dir=orbdir,mission=mission)
         else:
            orbs,times = s1_resorb(mission=mission)
      else:
         if orbdir is not None:
             orbs, times = s1_poeorb(in_poeorb_dir=orbdir,mission=mission)
         else:
             orbs, times = s1_poeorb(mission=mission)
    #
    # flag2 = times[:,1] >= et -> flag2 = times[:,2] >= et
    # times[:,0], starting time
    # times[:,1], ending time
    # times[:,2], creating time
    #
    flag1 = times[:,0] < st
    flag2 = times[:,1] > et
    flag3 = np.logical_and(times[:,0] < avt,times[:,1] > avt)
    flag0 = np.logical_and(flag1,flag2)
    #
    # orbs   = np.array(orbs)
    ctimes = times[flag0,:]
    outorb = orbs[flag0]
    #
    #
    if len(outorb)==0:
        outorb = orbs[flag3]
        ctimes = times[flag3,2]
    #
    #
    if len(outorb)==0:
        return "NULL",orbs,times
    if isinstance(outorb, np.str_) and os.path.exists(outorb):
        return outorb,orbs,times
    else:
        #
        outorb = outorb[ctimes[:,0]==np.min(ctimes[:,0])][0]
        return outorb,orbs,times
#
#
def s1xmlupdate(in_xml,outxml=None):
    #
    # To handle a bug in gmtsar in generating xml files
    # 
    if outxml is None:
       outxml = in_xml.split('.xml')[0] + '.tmp_xml'
    fid_out = open(outxml,'w')
    #
    with open(in_xml,'r') as fid:
        #
        for cline in fid:
            if 'coordinateConversionList' in cline:
                fid_out.write('   <coordinateConversionList count="0"></coordinateConversionList>\n');
            elif 'swathMergeList' in cline:
                fid_out.write('    <swathMergeList count="0"></swathMergeList>\n')
            else:
                fid_out.write(cline)
            #
        #
    fid_out.close()
    if os.path.exists(outxml):
        return True
    else:
        return False
#
def s1_poeorb(in_poeorb_dir="/home/wafeng/soft/InSAR/ORB/Sentinel_1/aux_poeorb/",\
              mission=None):
    #
    if mission is None:
        searchStr = ""
    else:
        searchStr = mission+"*"
    stafiles = glob.glob(in_poeorb_dir+"/%s/" % mission+searchStr+"*_POEORB_*.EOF")
    stafiles = np.array(stafiles)
    #
    timeinfo = np.zeros([stafiles.shape[0],3])
    for index in range(stafiles.shape[0]):
        #
        cfile = os.path.basename(stafiles[index]).split('_')
        times1 = pSAR.ts.dates2jd(cfile[6][1:])
        times2 = pSAR.ts.dates2jd(cfile[7][:-4])
        times0 = pSAR.ts.dates2jd(cfile[5])
        timeinfo[index,:] = [times1,times2,times0]
    #
    return stafiles, timeinfo
###############################################################################
def s1_resorb(in_resorb_dir="/home/wafeng/soft/InSAR/ORB/Sentinel_1/aux_resorb/",\
              mission='S1A'):
    #
    #
    if mission is None:
        searchStr = ""
    else:
        searchStr = mission
    #
    # print(in_resorb_dir+"/"+searchStr+"*_RESORB_*.EOF")
    #
    stafiles = glob.glob(in_resorb_dir+"/%s/" % mission +searchStr+"*_RESORB_*.EOF")
    stafiles = np.array(stafiles)
    #
    timeinfo = np.zeros([stafiles.shape[0],3])
    #
    for index in range(stafiles.shape[0]):
        #
        cfile = os.path.basename(stafiles[index]).split('_')
        times1 = pSAR.ts.dates2jd(cfile[6][1:])
        times2 = pSAR.ts.dates2jd(cfile[7][:-4])
        times0 = pSAR.ts.dates2jd(cfile[5])
        timeinfo[index,:] = [times1,times2,times0]
    #
    return stafiles, timeinfo
#
def s1times2statevector(startime,stoptime,model="RESORB",orbdir=None,mission='S1A'):
    #
    if orbdir is None:
       topdir = os.environ['S1_ORB']
       orbdir = topdir+'/aux_'+model.lower()+'/'
    #
    #
    st = pSAR.ts.timestr2jd(startime)
    et = pSAR.ts.timestr2jd(stoptime)
    #
    avt = (st+et)/2.
    #
    if model.upper() == "RESORB":
       if orbdir is not None:
          orbs,times = s1_resorb(in_resorb_dir=orbdir,mission=mission)
       else:
          orbs,times = s1_resorb(mission=mission)
    else:
       if orbdir is not None:
           orbs, times = s1_poeorb(in_poeorb_dir=orbdir,mission=mission)
       else:
           orbs, times = s1_poeorb(mission=mission)
    #
    flag1 = times[:,0] <= st
    flag2 = times[:,1] >= et
    flag3 = np.logical_and(times[:,0] <= avt,times[:,1] >= avt)
    flag0 = np.logical_and(flag1,flag2)
    #
    # print(flag0.shape)
    orbs   = np.array(orbs)
    ctimes = times[flag0,2]
    outorb = orbs[flag0]
    if len(outorb)==0:
        outorb = orbs[flag3]
        ctimes = times[flag3,2]
    #
    #
    if len(outorb)==0:
        return "NULL"
    if isinstance(outorb, np.str_) and os.path.exists(outorb):
        return outorb
    else:
        #
        outorb = outorb[ctimes==np.max(ctimes)][0]
        return outorb
#
def s1zip2statevector(inzip,model='RESORB',isdir=False):
    #
    #
    zipfile = os.path.basename(inzip)
    if not isdir:
       zipfile = zipfile.split('.zip')[0]
    else:
       zipfile = os.path.basename(inzip).split('.SAFE')[0]
    #
    info = zipfile.split('_')
    #
    platform     = info[0]
    startTimeOri = info[5]
    stopTimeOri  = info[6]
    #
    startTime = datetime.datetime.strptime(startTimeOri,"%Y%m%dT%H%M%S").strftime('%Y-%m-%dT%H:%M:%S.0')
    stopTime  = datetime.datetime.strptime(stopTimeOri,"%Y%m%dT%H%M%S").strftime('%Y-%m-%dT%H:%M:%S.0')
    #
    #
    orbfile = s1times2statevector(startTime+'Z',stopTime+'Z',model=model.upper(),\
                      mission=platform)
    return orbfile
#
###############################################################################
def geojson2file(jason_features,outfile):
    #
    # geom_in_geojson = geojson.Feature(geometry=jason_features, properties={})
    # Note that geojson list from loadS1geojson cannot be directly used here.
    # by Wanpeng Feng, @SYSU, Guangzhou, 2019/03/31
    #
    with open(outfile,'w') as fid:
        geojson.dump(jason_features,fid);
    
    return True
#
def s1subswath2geopoly(inxml,isfile=True):
    #
    geopts = s1swathxml2geogrid(inxml,isfile=isfile)
    return s1swathgeopts2geopoly(geopts)
#
def s1swathgeopts2geopoly(geopts,t0=-10000,t1=10e50):
    #
    # print(geopts)
    j = geopts[:,1]
    uj = np.unique(j)
    # outdata = [None for ni in range(len(uj)-1)]
    outdata = []
    #
    for ni in range(len(uj)-1):
        cj = uj[ni]
        #
        cdata = geopts[geopts[:,1]==cj,:]
        mini = np.min(cdata[:,0])
        maxi = np.max(cdata[:,0])
        p1 = cdata[cdata[:,0]==mini,:]
        p2 = cdata[cdata[:,0]==maxi,:]
        #
        cj = uj[ni+1]
        #
        cdata = geopts[geopts[:,1]==cj,:]
        mini = np.min(cdata[:,0])
        maxi = np.max(cdata[:,0])
        p3 = cdata[cdata[:,0]==mini,:]
        p4 = cdata[cdata[:,0]==maxi,:]
        cpoly = np.zeros([5,2])
        cpoly[0,:] = p1[0,2:4]
        cpoly[1,:] = p2[0,2:4]
        cpoly[2,:] = p4[0,2:4]
        cpoly[3,:] = p3[0,2:4]
        cpoly[4,:] = p1[0,2:4]
        #
        azitInfo = np.vstack([p3[:,4],p4[:,4]])
        #
        tmin = azitInfo.min()
        tmax = azitInfo.max()
        #
        if t0 <= tmin and t1>= tmax:
           outdata.append(cpoly)
    #
    return outdata
#
def s1swathxml2dir(inxml,isfile=True):
    #
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    tag = collection.getElementsByTagName("pass")
    dirstr = tag[0].childNodes[0].data
    return dirstr
def s1swathxml2heading(inxml,isfile=True):
    #platformHeading
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    tag = collection.getElementsByTagName("platformHeading")
    azi = tag[0].childNodes[0].data
    return float(azi)
#
# return radar_frequency
#
def s1swathxml2wavelength(inxml,isfile=True):
    #
    c_speed = 299792458.0
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    tag = collection.getElementsByTagName("radarFrequency")
    frequency = tag[0].childNodes[0].data
    #
    return float(c_speed/float(frequency))
#
def s1swathxml2incgrid(inxml,isfile=True):
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    collection = DOMTree.documentElement
    ids = collection.getElementsByTagName('geolocationGrid')
    gridIDs = ids[0].getElementsByTagName('geolocationGridPoint')
    outdata = []
    for cid in gridIDs:
        tag = cid.getElementsByTagName("latitude")
        lat = tag[0].childNodes[0].data
        tag = cid.getElementsByTagName("longitude")
        lon = tag[0].childNodes[0].data
        tag = cid.getElementsByTagName("incidenceAngle")
        inc = tag[0].childNodes[0].data
        outdata.append([float(lon),float(lat),float(inc)])
    #
    return np.array(outdata)
#
# xml for subswath 
def s1swathxml2inc(inxml,isfile=True):
    #
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    tag = collection.getElementsByTagName("incidenceAngleMidSwath")
    inc = tag[0].childNodes[0].data
    #
    return float(inc)
    #
def s1swathxml2iw(inxml,isfile=True,update=False):
    if update:
       flag = s1xmlupdate(inxml,outxml='tmp.xml')
       if flag:
          shutil.copy('tmp.xml',inxml)
    #
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    tags         = collection.getElementsByTagName("adsHeader")
    swathID = tags[0].getElementsByTagName("swath")
    swathinfo = swathID[0].childNodes[0].data
    return swathinfo
def s1swathxml2tinfo(inxml,isfile=True,update=False,\
                       fmt='%Y-%m-%dT%H:%M:%S.%f'):
    #
    if update:
       flag = s1xmlupdate(inxml,outxml='tmp.xml')
       if flag:
          shutil.copy('tmp.xml',inxml)
    #
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    #
    tags         = collection.getElementsByTagName("adsHeader")
    starttime_ID = tags[0].getElementsByTagName("startTime")
    stoptime_ID  = tags[0].getElementsByTagName("stopTime")
    starttime = starttime_ID[0].childNodes[0].data
    stoptime  = stoptime_ID[0].childNodes[0].data
    #
    return pSAR.ts.timestr2jd(starttime,fmt=fmt),\
           pSAR.ts.timestr2jd(stoptime,fmt=fmt)
    
# xml for subswath        
def s1swathxml2geogrid(inxml,isfile=True,update=False,\
                       fmt='%Y-%m-%dT%H:%M:%S.%f'):
    '''
    
    Parameters
    ----------
    inxml : TYPE
        DESCRIPTION.
    isfile : TYPE, optional
        DESCRIPTION. The default is True.
    update : TYPE, optional
        DESCRIPTION. The default is False.
    fmt : TYPE, optional
        DESCRIPTION. The default is '%Y-%m-%dT%H:%M:%S.%f'.

    Returns
    -------
    TYPE
        Updated by FWP, @SYSU, Guangzhou, 2020/04/14
        since this version, time information for single swath was provided.

    '''
    if update and isfile:
       flag = s1xmlupdate(inxml,outxml='_tmp')
       if flag:
          shutil.copy('_tmp',inxml)
    #
    if isfile:
        DOMTree    = xml.dom.minidom.parse(inxml)
    else:
        DOMTree    = xml.dom.minidom.parseString(inxml)
    #
    collection = DOMTree.documentElement
    #
    tags       = collection.getElementsByTagName("geolocationGrid")
    GPIDs      = tags[0].getElementsByTagName("geolocationGridPoint")
    outdata = []
    #
    for ni in range(len(GPIDs)):
        #
        # azimuth time, in julian time format
        azi_ID = GPIDs[ni].getElementsByTagName("azimuthTime")
        azt_jd  = pSAR.ts.timestr2jd(azi_ID[0].childNodes[0].data,fmt=fmt)
        # range time, in julian time format
        rng_ID = GPIDs[ni].getElementsByTagName("slantRangeTime")
        rng_jd  = float(rng_ID[0].childNodes[0].data)
        #
        cid   = GPIDs[ni].getElementsByTagName("line")
        line  = cid[0].childNodes[0].data
        cid   = GPIDs[ni].getElementsByTagName("pixel")
        pixel = cid[0].childNodes[0].data
        cid = GPIDs[ni].getElementsByTagName("latitude")
        lat = cid[0].childNodes[0].data
        cid = GPIDs[ni].getElementsByTagName("longitude")
        lon = cid[0].childNodes[0].data
        outdata.append([float(pixel),float(line),float(lon),float(lat),\
                        azt_jd,rng_jd])
    #
    return np.array(outdata)
#
def s1zipswathxml(inzip,pol='vv',swath=None):
    #
    try:
      zipid = zipfile.ZipFile(inzip)
      #
    except:
      zipid = None
    #
    xmls  = []
    if zipid is not None:
       # print(inzip)
       for cname in zipid.namelist():
           if pol.lower() in cname and '.tiff' in cname:
              cxml = os.path.basename(cname).split('.')[0]+'.xml'
              xmls.append(cxml)
    return xmls

def s1zip2swathxmlString(inzip,pol='vv'):
    #
    xmls = s1zipswathxml(inzip,pol=pol)
    if len(xmls) < 1:
        return []
    #
    try:
      zipid = zipfile.ZipFile(inzip)
      #
    except:
      zipid = None
    #
    info  = []
    if zipid is not None:
       # print(inzip)
       for cname in zipid.namelist():
           for cxml in xmls:
              if cxml == os.path.basename(cname):
                 info.append(zipid.read(cname))
    #
    return info,xmls
##Bingquan Li,@ITC, 2025/06/24
def s1safe2swathxmlString(insafe, pol='vv'):

    info = []
    xmls = []

    annotation_dir = os.path.join(insafe, "annotation")
    if not os.path.exists(annotation_dir):
        print(f"No annotation directory in {insafe}")
        return [], []

    for fname in sorted(os.listdir(annotation_dir)):
        fpath = os.path.join(annotation_dir, fname)
        if pol.lower() in fname.lower() and fname.endswith(".xml"):
            try:
                with open(fpath, "rb") as f:
                    info.append(f.read())
                    xmls.append(fname)
            except Exception as e:
                print(f"Error reading {fpath}: {e}")
    
    return info, xmls

def s1zip2manifestString(inzip):
    #
    try:
      zipid = zipfile.ZipFile(inzip)
      #
    except:
      zipid = None
    #
    info  = None
    if zipid is not None:
       # print(inzip)
       for cname in zipid.namelist():
           # print(cname)
           if 'manifest.safe' in cname:
              try:
                 info = zipid.read(cname)
              except:
                 print("%s is broken!!!" % inzip)
    return info  
#Bingquan Li,@ITC, 2025/06/24 
def s1safe2manifestString(insafe):

    manifest_path = os.path.join(insafe, 'manifest.safe')
    info = None
    try:
        with open(manifest_path, 'rb') as f:
            info = f.read()
    except Exception as e:
        print(f"Error reading {manifest_path}: {e}")
    return info


def s1zip2date(inzip):
    info = s1zip2manifestString(inzip)
    return s1manifest2date(info,isfile=False)

def s1safe2date(inzip):
    info = s1safe2manifestString(inzip)
    return s1manifest2date(info,isfile=False)

def s1zip2track(inzip):
    #
    info = s1zip2manifestString(inzip)
    return s1manifest2track(info,isfile=False)

def s1safe2track(inzip):
    #
    info = s1safe2manifestString(inzip)
    return s1manifest2track(info,isfile=False)

def s1zip2aux(inzip):
    #
    manifest_info = s1zip2manifestString(inzip)
    return s1manifest2aux(manifest_info,isfile=False)
#
def s1safe2aux(inzip):
    #
    manifest_info = s1safe2manifestString(inzip)
    return s1manifest2aux(manifest_info,isfile=False)

def s1manifest2platform(manifestinfo,isfile=True):
    #
    if isfile:
        DOMTree = xml.dom.minidom.parse(manifestinfo)
    else:
        DOMTree = xml.dom.minidom.parseString(manifestinfo)
    #
    collection = DOMTree.documentElement   
    tags  = collection.getElementsByTagName("safe:platform")
    conts = tags[0].getElementsByTagName("safe:number")
    return conts[0].childNodes[0].data
#
def s1manifest2aux(manifestinfo,isfile=True):
    #
    # read aux. calibration file from manifest
    #
    if isfile:
        DOMTree = xml.dom.minidom.parse(manifestinfo)
    else:
        DOMTree = xml.dom.minidom.parseString(manifestinfo)
    #
    collection = DOMTree.documentElement
    tags = collection.getElementsByTagName("resource")
    #
    outres = {}
    outres['RESORB'] = ''
    outres['INS']    = ''
    outres['CAL']    = ''
    outres['PP1']    = ''
    outres['POEORB'] = ''
    #
    for tag in tags:
        cfile = tag.getAttribute("name")
        if 'AUX_PP1' in cfile:
            outres['PP1'] = cfile.split('/')[-1]
        if 'AUX_CAL' in cfile:
            outres['CAL'] = cfile.split('/')[-1]
        if 'AUX_INS' in cfile:
            outres['INS'] = cfile.split('/')[-1]
        if 'AUX_RESORB' in cfile:
            outres['RESORB'] = cfile.split('/')[-1]
            outres['POEORB'] = outres['RESORB']
        if 'AUX_POE' in cfile:
            outres['POEORB'] = cfile.split('/')[-1]
            outres['RESORB'] = outres['POEORB']
    return outres
    #
#
###############################################################################
#        
def s1manifest2parse(manifestinfo,isfile=True):
    #
    # parse a manifest SAFE format structure variable
    # This could directly import from a ZIP file
    #
    if isfile:
        DOMTree = xml.dom.minidom.parse(manifestinfo)
    else:
        DOMTree = xml.dom.minidom.parseString(manifestinfo)
    #
    collection = DOMTree.documentElement
    timeinformation   = 'XXXXX'
    tags       = collection.getElementsByTagName("safe:acquisitionPeriod")
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:startTime")
       if len(conts) > 0:
          timeinformation = ("%s" % conts[0].childNodes[0].data)
    #
    # flight direction
    #
    flight_dir = "XXXXX"
    #
    tags       = collection.getElementsByTagName("s1:pass")
    if len(tags) > 0:
       flight_dir = ("%s" % tags[0].childNodes[0].data)
    #
    # slicenumber, number of bursts
    slicenumber = "XXXXX"
    #
    tags       = collection.getElementsByTagName("s1sarl1:sliceNumber")
    if len(tags) > 0:
       slicenumber = ("%s" % tags[0].childNodes[0].data)
    #
    # Mode
    sensormode = "XXXXX"
    #
    tags       = collection.getElementsByTagName("s1sarl1:mode")
    if len(tags) > 0:
       sensormode = ("%s" % tags[0].childNodes[0].data)
    #
    # safe:platform
    #
    platform   = 'Sentinel-1'
    tags       = collection.getElementsByTagName("safe:platform")
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:number")
       if len(conts) > 0:
          platform = ("%s%s" % (platform,conts[0].childNodes[0].data))
    #
    # RelativeTracknumber
    relativetrack   = '000'
    tags       = collection.getElementsByTagName("safe:orbitReference")
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:relativeOrbitNumber")
       if len(conts) > 0:
          relativetrack = ("%s" % conts[0].childNodes[0].data)
    #
    descri = ("%-25s : %s\n%-25s : %s\n%-25s : %s\n%-25s : %s\n%-25s : %s\n%-25s : %s" % \
                                                       ("AcquisitionTime", timeinformation,\
                                                        "Platform",        platform,\
                                                        "ImagingMode",     sensormode,\
                                                        "Direction",       flight_dir,\
                                                        "Slicenumber",     slicenumber,\
                                                        "RelativeOrbitNumber", relativetrack))
    tags       = collection.getElementsByTagName("safe:footPrint")
    #
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("gml:coordinates")[0]
    footPrintData = conts.childNodes[0].data.split()
    #
    return descri,footPrintData
#
def s1TOPS2manifest(inzip,islog=True,swathxml=False):
    #
    output_manifest = []
    #
    try:
      zf            = zipfile.ZipFile(inzip)
      zip_files     = zf.namelist()
      czip_dir_name = os.path.dirname(os.path.abspath(inzip))
      #
      for cname in zip_files:
         #
         root_name    = os.path.basename(cname)
         dir_name     = os.path.dirname(cname)
         cur_dir_name = os.getcwd()
         #
         ext = cname.split('.')[-1]
         predir = os.path.basename(os.path.dirname(cname))
         if ext == "xml" and predir == "annotation" and swathxml:
            bname = os.path.basename(cname)
            pol = bname.split('-')[3]
            swath = bname.split('-')[1]
            # print(" %s : %s" % (cname,pol))
            cxml = os.path.basename(inzip).split('.')[0]+'.'+swath+'.'+pol+'.xml'
            zf.extract(cname)
            shutil.move(cname,cxml)
         #
         if root_name == "manifest.safe":
            c_dir_name   = os.path.basename(dir_name);
            c_root_name,ext = os.path.splitext(c_dir_name)
            output_manifest = c_root_name + ".manifest"
            output_manifest = os.path.join(czip_dir_name,output_manifest)
            zf.extract(cname)
            shutil.move(cname,output_manifest)
            if islog:
               print(" %s : %s" % (inzip,os.path.basename(output_manifest)))
            if cur_dir_name != dir_name:
               shutil.rmtree(dir_name,ignore_errors=False)
            #  
    except:
      print(' ERROR: %s' % inzip)
    return output_manifest
###############################################################################     
#       
def s1strcut2str(in_struc):
    #
    # updated by Wanpeng Feng, @NRCan, 2017-04-04
    #
    # print(in_struc.keys())
    relativeorbnumber = 'XXXXX'
    orbitdirection    = 'XXXXX'
    polarisationmode  = 'XXXXX'
    
    if "id" in in_struc.keys():
        product_id = in_struc["id"]
        # product_id = product_id.encode(encoding='UTF-8')
    else:
        product_id = "XXXX"
    if "Relative orbit (start)" in in_struc.keys():
        relativeorbnumber = in_struc["Relative orbit (start)"]
    if "relativeorbitnumber" in in_struc.keys():
        relativeorbnumber = in_struc["relativeorbitnumber"]
    #    
    if "polarisationmode" in in_struc.keys():
        polarisationmode = in_struc["polarisationmode"]
    if "Polarization" in in_struc.keys():
        polarisationmode = in_struc["Polarization"]
    #
    if "identifier" in in_struc.keys():
        identifier = in_struc["identifier"]
        # identifier = identifier.encode('utf-8')
    else:
        identifier = "XXX"
    #
    if "orbitdirection" in in_struc.keys():
        orbitdirection = in_struc["orbitdirection"]
    if "Pass direction" in in_struc.keys():
        orbitdirection = in_struc["Pass direction"]
        # orbitdirection = orbitdirection.encode(encoding='UTF-8')
    #
    outstr = ("%-25s : %s\n %-25s : %s\n %-25s : %s\n %-25s : %s\n %-25s : %s\n" % \
              ("Identifier",identifier,\
               "Orbitdirection",orbitdirection,\
               "Product_id",product_id,\
               "relativeorbitnum",relativeorbnumber,\
               'polarisationmode',polarisationmode))
    #
    return outstr
#   
###############################################################################
#
def s1geojsonTOkml(s1_json,outkml,roi=None,isfile=True):
    #
    if isfile:
       s1_data = loadS1geojson(s1_json)
    else:
       s1_data = s1_json
    #
    kml_s,kml_e,polystr_s,polystr_e = pDATA.kml_poly()
    #
    fid = open(outkml,'w')
    fid.write(kml_s % outkml)
    if roi is not None:
       roipolygon = Polygon(roi)
    #
    for ind in range(len(s1_data)):
        #
        flag1 = s1_data[ind]["geometry"]
        overLapflag = True
        if flag1 is None:
           uid = s1_data[ind]['properties']['id']
           #
           # search online with data ID
           # updated by Wanpeng Feng, @CCRS/NRCan, 2017-10-03
           #
           from sentinelsat.sentinel import SentinelAPI
           import geomet.wkt
           api = SentinelAPI("s1wpfeng", "skyflow2008", \
                             'https://scihub.copernicus.eu/dhus')
           descri = api.get_product_odata(uid,full=True)
           cpoly = geomet.wkt.loads(descri['footprint'])
           cpoly = cpoly['coordinates']
           cname = descri['title']
           outstr = s1strcut2str(descri)
           #
        else:
           cpoly = s1_data[ind]["geometry"]["coordinates"]
           #
           descri = s1_data[ind]["properties"]
           outstr = s1strcut2str(descri)
        cpoly = np.array(cpoly)
        #
        # print(cpoly.shape)
        #
        # since sentinelsat 0.12
        if len(cpoly.shape)==3:
           cpoly = cpoly[0,:,:]
        #
        # since setninelsat 0.13
        if len(cpoly.shape)==4:
            cpoly = cpoly[0,0,:,:]
        # print(cpoly.shape)
        #
        #
        if roi is not None:
           cpolygon = Polygon(cpoly)
           overLapflag = roipolygon.intersects(cpolygon)
        if 'identifier' in descri:
          cname = descri["identifier"]
        #
        if overLapflag:
          #
          # a filter is added here for filtering the data
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
#
###############################################################################
def s1geojson2info(in_geojson):
    #
    outinfo = []
    jsoninfo = loadS1geojson(in_geojson)
    for cjson in jsoninfo:
        #
        track = cjson['properties']['lastrelativeorbitnumber']
        filename = cjson['properties']['filename']
        dates = cjson['properties']['beginposition']
        outinfo.append([filename,track,dates])
    #
    return np.array(outinfo)
#
def loadS1geojson(in_geojson):
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
#
###############################################################################
#
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
#
############################################################################### 
#
def s1dir_burstinROI(cdir,roi,pol='vv'):
    #
    polygons = pSAR.roipac.ext2polygon(roi)
    refpolyID = Polygon(polygons)
    #
    xmls = glob.glob(cdir+'/annotation/*%s*.xml' % pol)
    #
    outflag = False
    outdata = []
    #
    for cxml in xmls:
        xmlpolys = s1subswath2geopoly(cxml,isfile=True)
        for k in range(len(xmlpolys)):
             #
             cpoly = xmlpolys[k]
             _tmp_polyID = Polygon(cpoly)
             flag = refpolyID.intersects(_tmp_polyID)
             #
             if flag:
                 outflag = True
                 outdata.append(cpoly)
        #
    #
    return outflag,outdata
#            
def s1manifest2dir(in_manifest,isfile=True):
    #
    if isfile:
       DOMTree = xml.dom.minidom.parse(in_manifest)
    else:
       DOMTree = xml.dom.minidom.parseString(in_manifest)
    #
    collection = DOMTree.documentElement
    #
    tags       = collection.getElementsByTagName(\
                 "s1:pass")
    dirs       = []
    if len(tags) > 0:
       for ni in range(len(tags)):
          dirs.append(tags[ni].childNodes[0].data)
       #
    return dirs[0]       
#
def s1manifest2pol(in_manifest,isfile=True):
    #
    if isfile:
       DOMTree = xml.dom.minidom.parse(in_manifest)
    else:
       DOMTree = xml.dom.minidom.parseString(in_manifest)
    #
    collection = DOMTree.documentElement
    #
    tags       = collection.getElementsByTagName(\
                 "s1sarl1:transmitterReceiverPolarisation")
    pol        = []
    if len(tags) > 0:
       for ni in range(len(tags)):
          pol.append(tags[ni].childNodes[0].data)
       #
    return np.array(pol)
#
###############################################################################
def s1manifestsort(manifests):
    #
    datadates = np.array([s1manifest2date(csafe) for csafe in manifests],\
                         dtype='int32')
    index = np.argsort(datadates)
    # manifests = np.array(manifests)[index]
    return np.array(manifests)[index]
#
def s1manifest2date(in_manifest,isfile=True):
    #
    outtime = s1manifest2time(in_manifest,isfile=isfile)
    cdate   = outtime.split('T')[0]
    cdate   = cdate.replace("-","")
    return cdate
#
###############################################################################
def s1dir2orb(ins1dir,cdate,orbdir=None,model='RESORB'):
    '''
    
    Parameters
    ----------
    ins1dir : string
        a local S1 directory.
    orbdir : string, optional
        local S1 directory. The default is None.

    Returns
    -------
    None.

    '''
    #
    orbdir = os.environ['S1_ORB']+'/aux_%s/' % (model.lower())
    input_date = datetime.strptime(cdate, '%Y%m%d')


    previous_day = input_date - timedelta(days=1)
    next_day = input_date + timedelta(days=1)


    previous_day_str = previous_day.strftime('%Y%m%d')
    next_day_str = next_day.strftime('%Y%m%d')
    
    orb_file_temp = orbdir+'/'+ins1dir[:3]+'*V'+previous_day_str+'*'+next_day_str+'*'
    orb_files = glob.glob(orb_file_temp)

    #os.system('eof --sentinel-file "%s" --force-asf' %ins1dir)
    #orb_files = glob.glob(os.path.join(curr_dir,'*EOF'))
    for orb_file in orb_files:
        outflag = True
        return orb_file,outflag
    
###############################################################################
#
def s1zip2orb(inzip,model='RESORB',orbdir=None):
    #
    # state vectors saved in original manifest.safe were adapted from
    # a released RESORB file, which has been stated in manfest.safe.
    # function, s1zip2aux(<in_zip>) can return the exact file name from safe
    # file.
    # developed by Wanpeng Feng, @SYSU, Guangzhou, 2020/01/26
    #
    safeinfo = s1zip2aux(inzip)
    orb = safeinfo['RESORB']
    if orbdir is None:
        orbdir=os.environ['S1_ORB']+'/aux_%s/' % model.lower()
    target_orb = os.path.join(orbdir,orb)
    outflag = False
    if os.path.exists(target_orb):
        outflag = True
    return target_orb, outflag
#
def s1safe2statevector(in_manifest,model='RESORB',\
      orbdir=None,\
      fmt='%Y-%m-%dT%H:%M:%S.%f'):
    #
    # updated by Wanpeng Feng, @SYSU
    # to get orbidir from system
    if orbdir is None:
        orbdir = os.environ['S1_ORB']
    #
    mission = s1manifest2num(in_manifest)
    startTime,stopTime = s1manifest2Tcoverage(in_manifest)
    startTime_num = pSAR.ts.timestr2jd(startTime,fmt=fmt)
    stopTime_num  = pSAR.ts.timestr2jd(stopTime,fmt=fmt)
    dataMean_time = (startTime_num + stopTime_num) / 2
    dataMean_stime= pSAR.ts.jd2timestr(dataMean_time,fmt=fmt)
    #
    tinfo  = datetime.datetime.strptime(dataMean_stime,fmt)
    cyear  = tinfo.year
    #
    stas  = glob.glob(orbdir+'/*_V%s*.EOF' % cyear)
    if tinfo.month < 10:
        cmonth = '0%d' % tinfo.month
    else:
        cmonth = '%d' % tinfo.month
    #
    if model.upper() == 'RESORB':
        searchdir = orbdir + '/aux_resorb/'
    if model.upper() == 'POEORB':
        searchdir = orbdir + '/aux_poeorb/'
    #
    # print(searchdir,"S1%s" % mission,cyear,cmonth)
    stas  = glob.glob(searchdir+'/S1%s_*_V%s%s*.EOF' % (mission,cyear,cmonth))
    #
    outsta = 'None'
    if len(stas) > 0:
      # list to numpy array
      #
      stas = np.array(stas)
      times = [[pSAR.ts.timestr2jd(\
              os.path.basename(cfile).split('.')[0].split('_')[6][1::],\
              fmt='%Y%m%dT%H%M%S'),\
              pSAR.ts.timestr2jd(\
              os.path.basename(cfile).split('.')[0].split('_')[7],\
              fmt='%Y%m%dT%H%M%S')] for cfile in stas]
      #
      times = np.array(times)
      # 
      flag1 = times[:,0] <= startTime_num
      flag2 = times[:,1] >= stopTime_num
      flag = flag1*flag2
      outsta = stas[flag]
      #
      if isinstance(outsta, (list, tuple, np.ndarray)):
          outsta = outsta[0]
    return outsta    
#
def s1manifest2num(in_manifest):
    #
    DOMTree    = xml.dom.minidom.parse(in_manifest)
    collection = DOMTree.documentElement
    #
    tags       = collection.getElementsByTagName("safe:platform")
    num        = []
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:number")
       if len(conts) > 0:
          num = ("%s" % conts[0].childNodes[0].data)
    return num
#
def s1manifest2Tcoverage(in_manifest):
    DOMTree    = xml.dom.minidom.parse(in_manifest)
    collection = DOMTree.documentElement
    startTime  = 'None'
    stopTime   = 'None'
    tags       = collection.getElementsByTagName("safe:acquisitionPeriod")
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:startTime")
       if len(conts) > 0:
          startTime = ("%s" % conts[0].childNodes[0].data)
       conts = tags[0].getElementsByTagName("safe:stopTime")
       if len(conts) > 0:
          stopTime = ("%s" % conts[0].childNodes[0].data)
    return startTime,stopTime
#
###############################################################################
#
def s1footprint2polygon(infootprint):
    #
    polys = np.zeros([5,2])
    #
    polys[0,:] = [float(infootprint[0].split(',')[1]),\
                  float(infootprint[0].split(',')[0])]
    polys[1,:] = [float(infootprint[1].split(',')[1]),\
                  float(infootprint[1].split(',')[0])]
    polys[2,:] = [float(infootprint[2].split(',')[1]),\
                  float(infootprint[2].split(',')[0])]
    polys[3,:] = [float(infootprint[3].split(',')[1]),\
                  float(infootprint[3].split(',')[0])]
    polys[4,:] = polys[0,:]
    return polys
#
#
def s1manifest2time(in_manifest,isfile=True):
    #
    # done by Wanpeng Feng, @NRCan, 2017-02-15
    #
    if isfile:
       DOMTree = xml.dom.minidom.parse(in_manifest)
    else:
       DOMTree = xml.dom.minidom.parseString(in_manifest)  
    #
    collection = DOMTree.documentElement
    timeinformation   = 'XXXXX'
    tags       = collection.getElementsByTagName("safe:acquisitionPeriod")
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:startTime")
       if len(conts) > 0:
          timeinformation = ("%s" % conts[0].childNodes[0].data)

    return timeinformation 
#  
###############################################################################
#  
def s1manifest2track(in_manifest,isfile=True):
    #
    # done by Wanpeng Feng, @NRCan, 2017-02-15
    #
    if isfile:
       DOMTree = xml.dom.minidom.parse(in_manifest)
    else:
       #
       DOMTree = xml.dom.minidom.parseString(in_manifest)
    #
    collection = DOMTree.documentElement
    relativetrack   = '000'
    tags       = collection.getElementsByTagName("safe:orbitReference")
    if len(tags) > 0:
       conts = tags[0].getElementsByTagName("safe:relativeOrbitNumber")
       if len(conts) > 0:
          relativetrack = ("%s" % conts[0].childNodes[0].data)
    return relativetrack
#    
############################################################################### 
#   
def s1manifest2ROI(in_manifest,isfile=True):
    #
    if isfile:
       DOMTree = xml.dom.minidom.parse(in_manifest)
    else:
       DOMTree = xml.dom.minidom.parseString(in_manifest)
    #
    collection = DOMTree.documentElement
    #
    spoly = []
    tags       = collection.getElementsByTagName("safe:footPrint")
    #
    if len(tags) > 0:
      # 
      conts = tags[0].getElementsByTagName("gml:coordinates")[0]
      footPrintData = conts.childNodes[0].data.split()
      #
      for cdata in footPrintData:
         #
         data = cdata.split(',')
         # print("%f %f" % (float(data[0]),float(data[1])))
         spoly.append([float(data[1]),float(data[0])])
    #
    return np.array(spoly)
#
###############################################################################
#
def s1dirtoROI(indir):
    #
    xmlfile = glob.glob(indir+'/*.manifest')
    #
    if len(xmlfile) < 1:
       return [0,0,0,0]
    #
    counter = 0
    for cxml in xmlfile:
      #
      cpoly = s1manifest2ROI(cxml)
      if len(cpoly)>0:
         counter += 1
         if counter < 2:
            spoly = cpoly
         else:
            spoly = np.vstack((spoly,cpoly))
      #
    #
    return [np.min(spoly[:,0]),np.max(spoly[:,0]),\
            np.min(spoly[:,1]),np.max(spoly[:,1])]
    #
###############################################################################    
def s1_stack2master(cdir):
    #
    dirs = glob.glob(cdir+'/2*T*/')
    dates = []
    for cdir in dirs:
        cdir = os.path.basename(os.path.dirname(cdir))
        master = cdir.split('-')[0]
        slave = cdir.split('-')[1]
        dates.append([int(master),int(slave)])
    #
    dates = np.array(dates,dtype='int')
    dates = dates.ravel()
    udates = np.unique(dates)
    ndates = np.copy(udates)
    for i in range(udates.shape[0]):
        ndates[i] = sum(dates == udates[i])
    master = udates[ndates == np.max(ndates)]
    return udates,master

def s1_create_tab(indir,outtab,fullpath=True):
    '''
    To create tab 
    '''
    indir=os.path.abspath(indir)
    fid=open(outtab,'w')
    rng = [1,2,3]
    for index in range(3):
      slc=glob.glob(indir+'/*iw'+str(rng[index])+'*.slc')
      slc_par=glob.glob(indir+'/*iw'+str(rng[index])+'*.slc.par')
      slc_tops=glob.glob(indir+'/*iw'+str(rng[index])+'*.tops_par')
      if len(slc)>0:
        if fullpath:
           fid.write("%s %s %s\n" % (slc[0],slc_par[0],slc_tops[0]))
        else:
           fid.write("%s %s %s\n" % (os.path.basename(slc[0]),\
                                     os.path.basename(slc_par[0]),\
                                     os.path.basename(slc_tops[0])))

    fid.close()
    if os.path.exists(outtab):
        return True
    else:
        return False
#
def s1coregmeancor(in_quality_sta):
    #
    means = []
    with open(in_quality_sta,'r') as fid:
        #counter = 0
        goflag = 0
        for cline in fid:
            cline = pSAR.util.bytestoutf8(cline)
            if goflag == 1:
                tmp = cline.split()
                if len(tmp) != 9:
                    goflag = 0
                else:
                    means.append([float(tmp[5][1::]),float(tmp[4])])
            if "IW  overlap" in cline:
                goflag = 1
        #
    #
    #
    data = np.array(means)
    fracs = data[:,1]
    cors = data[:,0]
    if len(data) > 0:
        return np.max(cors[cors!=0]) * 1.5,np.min(fracs[fracs!=0.]) 
    else:
        return 0.,0.
#
def s1coregquality(in_quality_sta):
    #
    offsets = []
    with open(in_quality_sta,'r') as fid:
        #counter = 0
        for cline in fid:
            cline = pSAR.util.bytestoutf8(cline)
            if "azimuth_pixel_offset" in cline:
                cline = cline.split('\n')[0]
                cline = cline.split()
                offsets.append(cline[1])
    #
    if len(offsets)>0:
        return offsets[-1]
    else:
        return None
#    
def cdirtab(cdir):
    #
    slcs = glob.glob(cdir+'/*iw*.slc')
    if len(slcs)>0:
       slcdate = os.path.basename(slcs[0])
       slcdate = slcdate[0:8]
       itab = 'SLC_tab_'+slcdate
       dir2tab(cdir,cdir+'/'+itab)
       #
    #
    return True
#
def dir2tab(cdir,itab):
    '''
    To create tops SLC tab 
    by Wanpeng Feng, @CCRS/NRCan, 2017-07-18
    
    '''
    slcs = glob.glob(cdir+'/*.slc')
    with open(itab,'w') as fid:
       for slc in slcs:
         slc_bname = os.path.basename(slc).split('.slc')[0]
         slc = os.path.abspath(slc)
         slcdir = os.path.dirname(slc)
         slc_par = os.path.join(slcdir,slc_bname+'.slc.par')
         slc_tops = os.path.join(slcdir,slc_bname+'.tops_par')
         fid.write('%s %s %s\n' % (slc,slc_par,slc_tops))
    #
    if os.path.exists(itab):
       return True
    else:
       return False
###############################################################################
def TOPSDIR2time(cdirs):
    '''
    cdirs is a collection of TOPS folders...
    
    '''
    times = []
    for cdir in cdirs:
       #
       manifest = cdir+'/manifest.safe'
       ctime    = s1totime(manifest)
       times.append(ctime)
    #
    stimes = [float(mstime.split('T')[1]) for mstime in times]
    oindex = np.argsort(np.array(stimes))
    return times,oindex
#
###############################################################################
#
def s1totime(insafe,isfile=True):
    '''
    Return the start time information of a TOPS acquisition
    by Wanpeng Feng, @CCRS/NRCan, 2017-05-10
    
    '''
    if isfile:
       DOMTree = xml.dom.minidom.parse(insafe)
    else:
       DOMTree = xml.dom.minidom.parseString(insafe)
    #
    collection = DOMTree.documentElement
    #
    #
    tags       = collection.getElementsByTagName("safe:acquisitionPeriod")
    #
    timeinformation = None
    #
    if len(tags) > 0:
       #
       conts = tags[0].getElementsByTagName("safe:startTime")
       #
       if len(conts) > 0:
          timeinformation = ("%s" % conts[0].childNodes[0].data)
          timeinformation = timeinformation.replace("-","")
          timeinformation = timeinformation.replace(":","")
    #      
    return timeinformation
#
###############################################################################
#
def s1tocorners(insafe,isfile=True):
    #
    #
    if isfile:
       DOMTree    = xml.dom.minidom.parse(insafe)
    else:
       DOMTree    = xml.dom.minidom.parseString(insafe)
    #
    collection = DOMTree.documentElement
    #
    tags       = collection.getElementsByTagName("safe:footPrint")
    #
    spoly = []
    #
    if len(tags) > 0:
       #
       conts = tags[0].getElementsByTagName("gml:coordinates")[0]
       footPrintData = conts.childNodes[0].data.split()
       for cdata in footPrintData:
         data = cdata.split(',')
         #
         # print("%f %f" % (float(data[0]),float(data[1])))
         spoly.append([float(data[1]),float(data[0])])
         #
    corners = np.array(spoly)
    return corners
    
