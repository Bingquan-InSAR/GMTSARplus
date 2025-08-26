#!/usr/bin/env python
"""
  pGMT is a python-based module to drive GMT plotting a figure.
  Expecially format conversion between other data formats and 
  GMT grid (GRD) can be implemented with internal functions.
  <data conversion> could be considered with GDAL in future
  
  #
  In default, the gmt commands should come from GMT5.2.x or later version.
  
  Created on Mon May 23 21:11:33 2016
  @author: Wanpeng Feng, @Ottawa, Canada
  
"""
import sys,os,pSAR, numpy as np
import subprocess
import shutil
import pDATA
###############################################################################
def gmt_kml(outkml,minlon,maxlon,minlat,maxlat,png=''):
    #
    kmlstr = \
'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
<Document>
	<name>%s</name>
	<GroundOverlay>
		<name>GMT Image Overlay</name>
		<Icon>
			<href>%s</href>
		</Icon>
		<altitudeMode>clampToGround</altitudeMode>
		<LatLonBox>
			<north>%f</north>
			<south>%f</south>
			<east>%f</east>
			<west>%f</west>
		</LatLonBox>
		<Region>
		<LatLonAltBox>
			<north>%f</north>
			<south>%f</south>
			<east>%f</east>
			<west>%f</west>
		</LatLonAltBox>
		</Region>
	</GroundOverlay>
</Document>
</kml>'''
    with open(outkml,'w') as fid:
       fid.write(kmlstr % (png,png,maxlat,minlat,maxlon,minlon,maxlat,minlat,maxlon,minlon))
    #
    if os.path.exists(outkml):
       return True
    else:
       return False
#
###############################################################################
#
def gmt_run(cmd_str):
    #
    output        = subprocess.Popen(cmd_str,stdout=subprocess.PIPE,\
                                     stderr=subprocess.PIPE,shell=True)
    flag          = output.wait()
    prints,errors = output.communicate()
    #
    prints = pSAR.util.bytestoutf8(prints)
    return flag,prints,errors
#
###############################################################################
#
def gmt_optmapscalelen(xmin,xmax,ymin,ymax,gmt_proj,inlen=400,perc=0.3333):
    '''
    Return an optimal length (km) for plotting a map scale, which should be 
    a number.
    mapproject will be used to calculate the distance between two boundaries.
    '''
    latmean=(ymin+ymax)/2.
    #
    if gmt_proj[2] == 'X':
        cgmt_proj = gmt_proj.replace('X','M')
    else:
        cgmt_proj = gmt_proj
    #
    gmt_R='-R%f/%f/%f/%f' % (xmin,xmax,ymin,ymax)
    gmt_G='-G%s/%s/k' % (xmin,latmean)
    refll='%f %f' % (xmax,latmean)
    print('echo %s | gmt mapproject %s %s %s' % (refll,gmt_R,cgmt_proj,gmt_G))
    mapproject_run='echo %s | gmt mapproject %s %s %s' % (refll,gmt_R,\
                                                          cgmt_proj,gmt_G)
    flag,info,err = gmt_run(mapproject_run)
    print(flag,info,err,"1111")
    if flag == 0:
       tollength = info.split('\n')[0].split('\t')[2]
       reflen = float(tollength) * perc
    #
    while (inlen > reflen):
        inlen = int(inlen / 2.)
    return inlen
#
###############################################################################
#
def gmt_mroi2ext(rois):
    #
    roi,ginc = gmt_rois2gext(rois[0],rois[1])
    if rois.shape[0] > 2:
        for ni in range(rois.shape[0]-2):
            crsc = rois[ni+2]+'.rsc'
            ginfo,gext = pSAR.roipac.rsc_read(crsc)
            if gext[0] < roi[0]:
               xmin = gext[0]
            else:
               xmin = roi[0]
            if gext[1] > roi[1]:
               xmax = gext[1]
            else:
               xmax = roi[1]
            #
            if gext[2] < roi[2]:
               ymin = gext[2]
            else:
               ymin = roi[2]
            #    
            if gext[3] > roi[3]:
               ymax = gext[3]
            else:
               ymax = roi[3]
            #
            roi = [xmin,xmax,ymin,ymax]
    #
    return roi
###############################################################################    
def gmt_rois2gext(roi1,roi2):
    #
    #
    rsc1 = roi1 + '.rsc'
    rsc2 = roi2 + '.rsc'
    ginfo1,gext1 = pSAR.roipac.rsc_read(rsc1)
    ginfo2,gext2 = pSAR.roipac.rsc_read(rsc2)
    #
    if gext1[0] < gext2[0]:
        xmin = gext1[0]
    else:
        xmin = gext2[0]
    if gext1[1] > gext2[1]:
        xmax = gext1[1]
    else:
        xmax = gext2[1]
    #
    if gext1[2] < gext2[2]:
        ymin = gext1[2]
    else:
        ymin = gext2[2]
    #    
    if gext1[3] > gext2[3]:
        ymax = gext1[3]
    else:
        ymax = gext2[3]
    gext = [xmin,xmax,ymin,ymax]
    #
    if float(ginfo1['X_STEP']) > float(ginfo2['X_STEP']):
        ginc = float(ginfo1['X_STEP'])
    else:
        ginc = float(ginfo2['X_STEP'])
    #
    return gext,ginc
###############################################################################
def gmt_grdlandmask(output,gext,inc,gshhg='/home/wafeng/soft/gmt/gshhg-gmt-2.3.7'):
    #gmt grdlandmask -G$output.grd $mregion $inc -Df
    #
    gmt_command = 'gmt gmtset DIR_GSHHG=%s' % gshhg
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    #
    gmt_command = 'gmt grdlandmask -G%s %s %s -Df' % (output,gext,inc)
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    if os.path.exists(output):
        #
        return True
    else:
        return False
#
def gmt_sardir(x0,y0,gmt_outps,rlen=3,azi=-13.,sardir='r',\
               athick='0.25i',lthick='0.1i',gmt_d='-D0/0'):
    #
    # pSIMP was not released with gInSAR, which is not used 
    # by any function of gInSAR either
    # I moved this step, loading pSIMP within this local function
    # @NRCan, 2017-02-22
    #
    try:
      #
      import pSIMP
      #
    except ImportError:
      #
      print(" ++++++++++++++++++++++++++++++++++++++++")
      print(" + ERROR: pSIMP cannot be found.")
      print(" ++++++++++++++++++++++++++++++++++++++++")
      sys.exit(-1)
    #
    azi = 270 - float(azi) 
    aziprof = pSIMP.simp_pt2profile(x0,y0,90-float(azi),rlen,mode="r")
    losprof = pSIMP.simp_pt2profile(np.mean(aziprof[:,0]),\
                                    np.mean(aziprof[:,1]),\
                                    (90.-azi) - 270.,rlen/2.,mode="r")
    #
    fid = open('aziprof.arrow','w')
    fid.write('%f %f %f %s' % (x0,y0,azi-180,athick))
    fid.close()
    fid = open('losprof.arrow','w')
    #
    if sardir.upper() == "R":
       fid.write('%f %f %f %s' % (losprof[0,0],losprof[0,1],azi-270,lthick))
    else:
       # left looking
       fid.write('%f %f %f %s' % (losprof[0,0],losprof[0,1],azi-90,lthick))
    fid.close()
    #
    gmt_faults('aziprof.arrow',gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='',\
               gmt_proj='-J',gmt_lp='-W1.5p',\
               gmt_d=gmt_d,gmt_ls='-Sv0.1i+ea',gmt_G='-Gblack')
    gmt_faults('losprof.arrow',gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='',\
               gmt_proj='-J',gmt_lp='-W1p',\
               gmt_d=gmt_d,gmt_ls='-Sv0.055i+ea',gmt_G='-Gblack')
    #
    return True
    #
    # gmt_faults(subductiongmt,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='',\
    # gmt_ext='-R',gmt_proj='-J',gmt_lp='-W3p,139/0/0',gmt_ls='-Sf0.8i/0.01i+l+t+o0.5i')
    #
###############################################################################
#
def gmt_grdclip(ingrd,outgrd,si='-Si'):
    #
    gmt_sTr=(" gmt grdclip %s -G%s %s" % (ingrd,outgrd,si))
    print(gmt_sTr)
    #
    flag,info,errs = gmt_run(gmt_sTr)
    return flag
###############################################################################
#    
def gmt_roi2xyz(roi,outxyz):
    #
    roi_rsc   = roi+'.rsc'
    if os.path.exists(roi_rsc) is False:
       print(" pGMT: ERROR!!!! %s cannot be found. " % roi_rsc)
       sys.exit(-1)
    #
    fmt       = pSAR.roipac.roi_to_fmt(roi)
    data      = pSAR.roipac.roi_read(roi,dtype=fmt)
    lonm,latm = pSAR.roipac.rsc_to_llm(roi_rsc)  
    #
    data = np.nan_to_num(data)
    zlon = lonm[data!=0]
    zlat = latm[data!=0]
    zdat = data[data!=0]
    #
    xyz  = np.vstack((zlon,zlat,zdat))
    #
    xyz  = xyz.transpose()
    #
    # outxyz = roi+'.xyz'
    pSAR.roipac.roi_write(xyz,outxyz)
    #
    if os.path.exists(outxyz):
        return True
    else:
        return False
###############################################################################
def gmt_grdeditbygrd(grd,ingrd):
    #
    gmt_command = ("gmt grdedit %s -R%s" % (grd,ingrd))
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    return True
#   
def gmt_grdedit(grd,gext='',gmt_r=False):
    #
    '''
      Sensitive for the format, pixel registration or gridline registration
    '''
    gmt_t = ''
    if gmt_r:
        gmt_t = '-T'
    #
    gmt_command=("gmt grdedit %s %s -A %s" % (grd,gext,gmt_t))
    #
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    #
    if os.path.exists(grd):
        return True
    else:
        return False
###############################################################################
def gmt_dem2roibyrsc(indemgrd,inphsrsc,outdemgrd,dtype=None,gmt_r='-r',interp='b',is180=False,model=1):
    #
    # this is not perfectly right...
    #
    info,ext = pSAR.roipac.rsc_read(inphsrsc)
    if is180:
        for i in range(4):
            if ext[i] > 180:
                ext[i] = ext[i] - 360
            #
        #
    #
    gmt_gext = ("-R%s/%s/%s/%s" % (str(ext[0]),str(ext[1]),str(ext[2]),str(ext[3])))
    gmt_ext  = ("-R0/%d/0/%d" % (int(info["WIDTH"]),int(info["FILE_LENGTH"])))
    gmt_ginc = '-I%s/%s' % (info['X_STEP'],info['Y_STEP'][1::])
    #
    # bname = outdemgrd.split('.')[0]
    #
    cutgrd= outdemgrd+'.cut.grd'
    gmt_grdcut(indemgrd,cutgrd,gext=gmt_gext)  
    #
    if model==1:
      gmt_grdedit(cutgrd,gext=gmt_ext)
      #
      gmt_inc = "-I1/1"
      #
      # Now we fix registration with a way of pixel...
      # by Wanpeng Feng, @NRCan, 2016-11-24
      #
      gmt_grdsample(cutgrd,outdemgrd,gr=gmt_r,gext='',ginc=gmt_inc,interp=interp)
      gmt_grdedit(outdemgrd,gext=gmt_gext)
    else:
      # pSAR.roipac.roi_to_xyz(cphs,roixyz,scale=1,of='b',nozero=True,isnan=True)
      roixyz = '_tmp.z'
      gmt_grd2xyz(cutgrd,roixyz,isbin=True)
      gmt_xyz2grd(roixyz,outdemgrd,gmt_r='',surface=False,dtype=dtype,gext=gmt_gext,ginc=gmt_ginc)
      #
      if os.path.exists(roixyz):
          os.remove(roixyz)
      #
    os.remove(cutgrd)
    #
    if os.path.exists(outdemgrd):
        return True
    else:
        return False 
###############################################################################        
#
def gmt_dem2roi(indemgrd,inphsgrd,outdemgrd,gmt_r=''):
    #
    # gmt_r flag for pixe registration mode in making grd file
    #
    gmt_gext = gmt_grd2gext(inphsgrd)
    # 
    #
    bname = os.path.basename(outdemgrd).split('.')[0]
    cutgrd= bname+'_CUT.grd'
    gmt_grdcut(indemgrd,cutgrd,gext=gmt_gext)
    #
    gmt_ext = gmt_grd2gext(inphsgrd,mode='rec',gmt_r=gmt_r)
    gmt_grdedit(cutgrd,gext=gmt_ext)
    gmt_inc = "-I1/1"
    #
    # force output grd in pixel registration
    #
    gmt_grdsample(cutgrd,outdemgrd,gext=gmt_ext,gr=gmt_r,\
                  ginc=gmt_inc,interp='b')
    gmt_grdedit(outdemgrd,gext=gmt_gext)
    os.remove(cutgrd)
    #
    if os.path.exists(outdemgrd):
        return True
    else:
        return False
###############################################################################
def gmt_global(roi,gmt_outps,gmt_proj='-J',gmt_xoff='-X3i',gmt_yoff='-Y3i',gmt_mapsize='2i',\
                   gmt_outpoly='Global_Inpoly.inp',gmt_iscov='-O',\
                   gmt_ptonly=False,gmt_iscon='-K',gmt_ptsize='2p',gmt_D='-Dl',\
                   gmt_lp='-W2p,red',gmt_pts=None,gmt_ptls='-S+2p,black',gext="-R",\
                   gmt_ptf='-F+a0+f7p,Helvetica,255/255/255+jC',gmt_txtD='-D0/0'):
                            
    #
    meanx = (roi[0] + roi[1]) / 2.
    meany = (roi[2] + roi[3]) / 2.      
    #
    if gmt_proj == "-J":
        gmt_proj = ('-JG%f/%f/%s' % (meanx,meany,gmt_mapsize))
        gext="-Rg"
    else:
        gmt_proj = gmt_proj
        gext = gext
    gmt_pscoast(gmt_outps,gmt_proj=gmt_proj,gmt_ext=gext,\
                            gmt_G='-Ggray40',gmt_iscon='-K',\
                            gmt_iscov=gmt_iscov,gmt_I='',gmt_Bx='',gmt_By='',\
                            gmt_snew='',\
                            gmt_N='',gmt_S='-Slightblue',gmt_xoff=gmt_xoff,\
                            gmt_yoff=gmt_yoff,gmt_P='-P',gmt_D=gmt_D)  
    #
    polygon = []
    polygon.append([roi[0],roi[2]])
    polygon.append([roi[0],roi[3]])     
    polygon.append([roi[1],roi[3]])
    polygon.append([roi[1],roi[2]])  
    polygon.append([roi[0],roi[2]])
    #
    polygon = np.array(polygon)
    if not os.path.exists(gmt_outpoly):
        np.savetxt(gmt_outpoly,polygon,fmt="%f %f",newline="\n")
    #
    #
    
    if gmt_pts is not None:
        ploc = gmt_pts[0]
        pname= gmt_pts[1]
        #
        for ni in range(ploc.shape[0]):
            #
            gmt_points(ploc[ni,0],ploc[ni,1],gmt_outps,gmt_iscov='-O',\
                   gmt_iscon='-K',gmt_B='',\
                   gmt_ext='-R',gmt_proj='-J',gmt_lp='-W0.01p,white',\
                   gmt_ls=gmt_ptls,gmt_fillc='-Gred')
            #
            gmt_pstext(ploc[ni,0],ploc[ni,1],pname[ni],gmt_outps,\
              gmt_f=gmt_ptf, gmt_g='-G0/0/0',gmt_ext='-R', gmt_proj='-J',\
              gmt_B='',gmt_iscov='-O', gmt_xoff='-X0i',gmt_w='-W0.1p',\
              gmt_yoff='-Y0i',gmt_iscon='-K', gmt_n='',gmt_D=gmt_txtD)
    #    
    if not gmt_ptonly: 
       gmt_psxy_mline(gmt_outpoly,gmt_outps,gmt_iscov='-O',\
                   gmt_iscon=gmt_iscon,gmt_B='', gmt_ext='-R',gmt_proj='-J',\
                   gmt_lp=gmt_lp)
    else:
       gmt_points(meanx,meany,gmt_outps,gmt_iscov='-O',gmt_iscon=gmt_iscon,\
                   gmt_B='', gmt_ext='-R',gmt_proj='-J',gmt_lp='-W',\
                   gmt_ls=('-Sa%s,red' % gmt_ptsize),gmt_fillc='-Gred')
           
    #               
    return True                             
###############################################################################    
def gmt_psmeca(infoc,gmt_outps,gmt_proj='-J',gmt_ext='-R',gmt_G='-Gred',\
               gmt_iscon='-K', gmt_iscov='-O',gmt_W='-W2p,black',gmt_I='',\
               gmt_C='-CblackP2p',gmt_B='',gmt_snew='', gmt_L='',\
               gmt_S='"-Sa0.3/10p/1p"',gmt_xoff='-X0i',\
               gmt_yoff='-Y0i',gmt_P='-P',gmt_D='',gmt_t=''):
    '''            
    gmt_C  attributes of locations of focal mechanims -C<color>P<point_size>
    '''      
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #                   
    #
    gmt_command=("gmt psmeca %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % \
                  (infoc,gmt_proj,gmt_ext,gmt_iscon,\
                   gmt_D,gmt_W,gmt_G,gmt_iscov,gmt_I,gmt_S,\
                   gmt_xoff,gmt_yoff,gmt_L,gmt_C,gmt_B,\
                   gmt_P,gmt_t,gmt_snew,gmt_outstr,gmt_outps))
    print(" pGMT: %s " % gmt_command)
    flag,info,errs = gmt_run(gmt_command)
    return flag
###############################################################################
def gmt_pscoast(gmt_outps,gmt_proj='-J',gmt_ext='-R',gmt_G='-Ggray50',gmt_iscon='-K',\
                            gmt_iscov='-O',gmt_I='-I2/0.25p,blue',gmt_Bx='',\
                            gmt_By='',gmt_snew='',\
                            gmt_N='-N1/0.25p',gmt_S='-Slightblue',gmt_xoff='-X0i',\
                            gmt_yoff='-Y0i',gmt_P='-P',gmt_D='-Dh',gshhg_dir=None):
    #                     
    gshhg_env = ""
    if gshhg_dir is not None:
       gshhg_env = "--DIR_GSHHG=%s" % gshhg_dir
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #                        
    gmt_command=("gmt pscoast %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % \
                 (gmt_proj,gmt_ext,gmt_iscon,\
                  gmt_D,gmt_G,gmt_iscov,gmt_I,gmt_S,\
                  gmt_xoff,gmt_yoff,gmt_N,gmt_Bx,gmt_By,\
                  gmt_P,gmt_snew,gshhg_env,gmt_outstr,gmt_outps))
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    return True
###############################################################################
def gmt_batch_run(runs):
    with open(runs,'r') as fid:  
        for cline in fid:
            cline = pSAR.util.bytestoutf8(cline)
            cline = cline.split('\n')[0]
            print(' pGMT: %s ' % cline)
            flag,info,errs = gmt_run(cline)
    return True
def gmt_export(command,outfile,mode='a'):
    #
    with open(outfile,mode) as fid:
        fid.write('%s\n' % command)
    return True
#
###############################################################################
#
def gmt_pslegend(in_legend,gmt_outps,gmt_proj='-J',gmt_ext='-R',\
                  gmt_iscon='-K',gmt_t='-t20',\
                  gmt_iscov='-O',gmt_ruler='-L',\
                  gmt_B='',gmt_F='-F+gwhite+r',\
                  gmt_D='-Dx0.5i/0.5i+w5i/3.3i+jBL+l1.2',\
                  gmt_xoff='-X0i',gmt_yoff='-Y0i',gmt_P='-P'):
    '''
    gmt_t flag for transparency, 0-100. 0 in default is for opaque
    gmt_B none in default, "-BESWN -Baf" gives all annotations in four boundaries
    gmt_F option for background of the legend
    gmt_D option the location of the legend on the map
          -Dx0.5i/0.5i+w5i/3.3i+jBL+l1.2 means
          1) <x> defines reference point at <0.5i,0.5i> for plot coordinates 
          2) <+w> defines width of the legend window
          3) <+j> justify the location of the legend window with respect to 
             the anchor point. bottom-left "BL" in default
          
    
    '''
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #                        
    gmt_command = ("gmt pslegend %s %s %s %s %s %s %s %s %s %s %s %s %s %s" \
                 % (in_legend,gmt_proj,gmt_ext,gmt_iscon,\
                    gmt_D,gmt_iscov,gmt_t,\
                    gmt_xoff,gmt_yoff,gmt_F,\
                    gmt_P,gmt_B,gmt_outstr,gmt_outps))
    print(' pGMT: %s' % gmt_command)
    flag,info,err = gmt_run(gmt_command)
    return flag
###############################################################################
#
def gmt_psbasemap(gmt_outps,gmt_proj='-J',gmt_ext='-R',\
                  gmt_d='-Dj',gmt_iscon='-K',norun=False,\
                  gmt_iscov='-O',gmt_ruler='-L',\
                  gmt_Bx='',gmt_By='',gmt_snew='',\
                  gmt_log='',gmt_xoff='-X0i',gmt_yoff='-Y0i',gmt_P='-P'):
    # gmt_ruler can be something like
    # -Lx0.4i/0.3i+w500k+lScale(km)                        
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #                        
    gmt_command=("gmt psbasemap %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" \
                 % (gmt_proj,gmt_ext,gmt_iscon,\
                    gmt_d,gmt_iscov,gmt_ruler,\
                    gmt_xoff,gmt_yoff,gmt_log,gmt_Bx,gmt_By,\
                    gmt_P,gmt_snew,gmt_outstr,gmt_outps))
    #
    print(" pGMT: %s " % gmt_command)
    #
    if norun:
       flag = gmt_command
    else:
       flag,info,errs = gmt_run(gmt_command)
    #
    return flag
###############################################################################
def gmt_grd2gext(grd,mode='geo',gmt_r='',force0=False):
    #
    ginfo,gerr = gmt_grdinfo(grd)
    xmin       = np.float64(ginfo['X_FIRST'])
    xmax       = np.float64(ginfo['X_MAX'])
    if force0:
        if xmin < 0:
            xmin = 360  + xmin
        if xmax < 0:
            xmax = 360. + xmax
    if mode.upper()=="GEO":
        if force0:
           gmt_ext = ('-R%11.10f/%11.10f/%10.10/%10.10f'%(xmin,xmax,\
                                       float(ginfo['Y_MIN']),float(ginfo['Y_FIRST'])))
        else:
           gmt_ext = ('-R%11.6f/%11.6f/%10.6f/%10.6f'%(float(ginfo['X_FIRST']),\
                                       float(ginfo['X_MAX']),\
                                       float(ginfo['Y_MIN']),\
                                       float(ginfo['Y_FIRST'])))
    else:
        if gmt_r.upper().strip() == '-R':
           gmt_ext = ('-R0/%s/0/%s'%(ginfo['WIDTH'],ginfo['FILE_LENGTH'])) 
        else:
           gmt_ext = ('-R1/%s/1/%s'%(ginfo['WIDTH'],ginfo['FILE_LENGTH']))  
    # gmt_inc = ('-I%s/%f' % (ginfo['X_STEP'],float(ginfo['Y_STEP']) * -1.))
    gmt_ext = gmt_ext.replace(" ","")
    return gmt_ext
###############################################################################
def gmt_grd2inc(grd,scale=1):
    #
    ginfo,gerr = gmt_grdinfo(grd)
    # gmt_ext = ('-R%s/%s/%s/%s'%(ginfo['X_FIRST'],\
    #                             ginfo['X_MAX'],ginfo['Y_MIN'],ginfo['Y_FIRST']))
    gmt_inc = ('-I%f/%f' % (float(ginfo['X_STEP'])*scale,\
                                  float(ginfo['Y_STEP']) * -1*scale))
    return gmt_inc
###############################################################################    
def gmt_grdmask(maskfile,outgrd,gext='',ginc=''):
    #
    gmt_command=("gmt grdmask %s -G%s %s %s -A" % (maskfile,outgrd,gext,ginc))
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    if os.path.exists(outgrd):
       return True
    else:
       return False
###############################################################################    
def gmt_grdmath(outgrd,gext='',grd1='',grd2='',gmath=''):
    #
    #
    gmt_command=("gmt grdmath %s %s %s %s = %s" % (gext,grd1,grd2,gmath,outgrd))
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    if os.path.exists(outgrd):
       return True
    else:
       return False    
    
###############################################################################    
def gmt_grdsample(grd,outgrd,gext='',gr='',ginc='',interp='n'):
    #
    # Updated by Wanpeng Feng, @NRCan, 2016-11-24
    # We need to fix a pixel registration
    # Then all pixels could be x0-x1/pixelsize, rather than x0-x1/pixelsize +1 for gridline 
    # ---
    # interp can be "n","b","c","l"
    #
    # Since now, default interp is changed to "n", near-neighbor, @NRCan, 2017-03-09
    #
    gmt_command=("gmt grdsample %s -G%s -n%s %s %s %s" % (grd,outgrd,interp,gext,ginc,gr))
    print(" pGMT: %s" % gmt_command)
    flag,info,err = gmt_run(gmt_command)
    return flag 
###############################################################################
def gmt_grdcontour(grd,gmt_outps,gmt_cpt='-C',gmt_A='-Aa5+f10p',gmt_proj='-J',\
                   gmt_iscon='-K',gmt_iscov='-O',gmt_gext='-R',\
                   gmt_s='-S4',gmt_W='-W1p,blue'):
    #
    # gmt_s is added @SYSU,Guangzhou, 2019/08/09
    #     which is a factor for smoothing
    #
    gmt_command=("gmt grdcontour %s %s %s %s %s %s %s %s %s >>%s" % \
                 (grd,gmt_proj,gmt_gext,gmt_s,\
                  gmt_cpt,gmt_A,gmt_iscon,\
                  gmt_W,gmt_iscov,gmt_outps))
    print(" pGMT: %s " % gmt_command)
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()
    return True
###############################################################################
def gmt_grdcut(grd,outgrd,gext=''):
    #
    gmt_command = ("gmt grdcut %s -G%s %s" % (grd,outgrd,gext))
    print(" pGMT: %s " % gmt_command)
    #
    flag,info,errs = gmt_run(gmt_command)
    if flag >= 0:
       gext = gmt_grd2gext(outgrd)
       return flag,gext
    else:
       return flag,None
###############################################################################
def gmt_globaldem2roiscale(indemgrd,roi,outdem,fmt='Int16'):
    #
    rsc = roi+'.rsc'
    if not os.path.exists(rsc):
        print(' pGMT: ERROR! %s cannot be found.' % rsc)
        return False
    #
    gext,ginc=gmt_rsc2ext(rsc)
    outgrd = outdem+'.grd'
    sampledgrd = outdem + '.sampled.grd'
    # demxyz     = outdem + '.xyz'
    #
    gmt_grdcut(indemgrd,outgrd,gext=gext)
    gmt_grdedit(outgrd,gext=gext)
    gmt_grdsample(outgrd,sampledgrd,ginc=ginc)
    # gmt_grd2xyz(sampledgrd,demxyz)
    # gmt_xyz2grd(demxyz,outgrd,gext=gext,ginc=ginc)
    gmt_grd2roi(sampledgrd,outdem,refrsc=rsc,fmt=fmt)
    #
    if os.path.exists(outdem):
        return True
    else:
        return False
        
###############################################################################
def gmt_grdtrack(grd,xy):
    #
    outllt = '_lld.gmt'
    gmt_command = ("gmt grdtrack %s -G%s > %s" % (xy,grd,outllt))
    print(" pGMT: %s " % gmt_command)
    os.system(gmt_command)
    # infodata = []
    infodata = np.loadtxt(outllt)
    if os.path.exists(outllt):
        flag = True
        err = outllt
    else:
        flag = False
        err = 'ERR'
    return flag,infodata,err
#
###############################################################################
#
def gmt_grd2roi(grd,roi,refrsc=None,ginfo=None,fmt='f',driver='gmt'):
    # ginfo could be given since 2020/04/19
    # updated by FWP, @SYSU, Guangzhou
    #
    ginfo,gerror = gmt_grdinfo(grd,gmt_info=ginfo)
    #
    #
    if not os.path.exists(grd):
       print(" %s cannot be found" % grd)
       sys.exit(-1)
    if (refrsc is not None and os.path.exists(refrsc)):
        print(' pGMT: reference RSC is %s' % refrsc)
        cinfo,ext = pSAR.roipac.rsc_read(refrsc)
        #
        cinfo['X_STEP']      = ginfo['X_STEP']
        cinfo['Y_STEP']      = ginfo['Y_STEP']
        cinfo['WIDTH']       = ginfo['WIDTH']
        cinfo['FILE_LENGTH'] = ginfo['FILE_LENGTH']
        cinfo['X_FIRST']     = ginfo['X_FIRST']
        cinfo['Y_FIRST']     = ginfo['Y_FIRST']
        #
        # Updated by Wanpeng Feng, @NRCan, 2017-02-08
        # X_MAX and Y_MIN in previouscinfo were not updated in default...
        #
        cinfo['X_MAX']       = str(float(ginfo['X_FIRST']) + \
                                   float(ginfo['X_STEP']) * (float(ginfo['WIDTH'])-1))
        cinfo['Y_MIN']       = str(float(ginfo['Y_FIRST']) + \
                                   float(ginfo['Y_STEP']) * (float(ginfo['FILE_LENGTH'])-1)) 
    else:
        cinfo = ginfo
    #
    if driver.upper() == 'GMT':
      gmt_command = ("gmt grd2xyz %s -ZTL%s >%s" % (grd,fmt,roi))
      print(" pGMT: %s " % gmt_command)
      subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
      subinfo.wait()
      #
      pSAR.roipac.info_to_rsc(cinfo,roi+'.rsc')
      #
    else:
      gdal_command = 'gdal_translate -a_srs "+proj=latlong +datum=WGS84" -of EHdr %s %s' % (grd,roi) 
      print(gdal_command)
      #
      subinfo = subprocess.Popen(gdal_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
      subinfo.wait()
      #
      pSAR.roipac.info_to_rsc(cinfo,roi+'.rsc')
      #
    if os.path.exists(roi):
       return True
    else:
       return False
###############################################################################
def gmt_psvelo(vec,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='-B',gmt_n='',\
                   gmt_ext='-R',gmt_proj='-J',gmt_lp='-W',gmt_sigscale=2.,\
                   gmt_a='-A0.3p',gmt_se='-Se0.2/0.39/18',gmt_fillc='-Gred',\
                   gmt_xoff='-X0i',gmt_yoff='-Y0i',gmt_l='-L',isfile=False):
    #
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'           
    if isfile:
       gmt_command = ('gmt psvelo %s -E %s %s %s %s %s %s %s %s %s %s %s -P %s -D%f %s %s %s' % \
                  (vec,gmt_proj,\
                 gmt_ext,gmt_a,gmt_lp,gmt_iscov,gmt_iscon,gmt_se,gmt_fillc,\
                 gmt_xoff,gmt_yoff,gmt_l,gmt_B,gmt_sigscale,gmt_n,gmt_outstr,gmt_outps))
    else:         
       gmt_command = ('echo %f %f %f %f %f %f %f |gmt psvelo -E %s %s %s %s %s %s %s %s %s %s -P %s %s -D%f %s %s %s' % \
                  (vec[0],vec[1],vec[2],vec[3],vec[4],vec[5],vec[6],gmt_proj,\
                   gmt_ext,gmt_a,gmt_lp,gmt_iscov,gmt_iscon,gmt_se,gmt_fillc,\
                   gmt_xoff,gmt_yoff,gmt_B,gmt_l,gmt_sigscale,gmt_n,gmt_outstr,\
                   gmt_outps))  
    #
    print(' pGMT: %s' % gmt_command)      
    flag,info,errs = gmt_run(gmt_command)
    return True      
#         
###############################################################################     
def gmt_aftershocks(infile,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='-B',\
                   gmt_ext='-R',gmt_proj='-J',gmt_C='-C',gmt_lp='-W',\
                   gmt_xoff='-X0i',gmt_yoff='-Y0i',gmt_ls='-S+2p,black',\
                   gmt_w=None,gmt_fillc='-Gblack'):
    # 
    #
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'         
    if gmt_w is not None:
        gmt_lp = gmt_w
    #
    gmt_command = ('gmt psxy %s %s %s %s %s %s %s %s %s %s %s %s -P %s %s'% \
                   (infile,gmt_proj,gmt_ext,gmt_ls,gmt_lp,gmt_iscov,\
                    gmt_iscon,gmt_B,gmt_fillc,gmt_C,\
                    gmt_xoff,gmt_yoff,gmt_outstr,gmt_outps))     
                 
    #
    print(' pGMT: %s' % gmt_command)      
    flag,info,errs = gmt_run(gmt_command) 
    return flag,info,errs    
###############################################################################                 
def gmt_points(x,y,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='-B',gmt_n='',\
                   gmt_ext='-R',gmt_proj='-J',gmt_lp='-W',gmt_xoff='-X0i',\
                   gmt_yoff='-Y0i',gmt_ls='-S+2p,black',gmt_fillc='-Gblack'):
    # 
    #
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'                    
    gmt_command = ('echo %f %f |gmt psxy -P %s %s %s %s %s %s %s %s %s %s %s %s %s' % \
                (x,y,gmt_proj,gmt_B,\
                 gmt_ext,gmt_ls,gmt_lp,\
                 gmt_iscov,gmt_iscon,gmt_fillc,\
                 gmt_xoff,gmt_yoff,gmt_n,gmt_outstr,gmt_outps))     
                 
    #
    print(' pGMT: %s' % gmt_command)      
    flag,info,errs = gmt_run(gmt_command)
    return flag,info,errs    
###############################################################################
def gmt_distfault(infault,gmt_outps,gmt_iscov='-O',\
                  gmt_iscon='-K',gmt_B='',gmt_G='',\
                   gmt_ext='-R',gmt_proj='-J',\
                   gmt_W='-W',gmt_C='-C',gmt_xoff='-X0i',\
                   gmt_yoff='-Y0i',gmt_Bx='',gmt_By='',gmt_P='-P',gmt_L=''):
    #
      
    #               
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'    
    #         
    gmt_command=('gmt psxy %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s'\
                 % (infault,gmt_proj,\
                 gmt_ext,gmt_C,gmt_W,\
                 gmt_iscov,gmt_iscon,gmt_G,gmt_xoff,gmt_yoff,\
                 gmt_B,gmt_Bx,gmt_By,gmt_P,gmt_L,gmt_outstr,gmt_outps))
    #
    print(' pGMT: %s' % gmt_command)             
    flag,info,errs = gmt_run(gmt_command) 
    return flag     
###############################################################################
def gmt_faults(infault,gmt_outps,gmt_iscov='-O',\
               gmt_iscon='-K',gmt_B='-B',gmt_G='-Gred',\
               gmt_xoff='-X0i',gmt_yoff='-Y0i',gmt_ext='-R',gmt_proj='-J',gmt_d='-D0/0',\
               gmt_lp='-W',gmt_ls='-Sf0.5p,red'):
    #
    # gmt_ls can be -Sf0.5p/2p+l+o for left-leteral slip
    # gmt_ls can be -Sf0.5p/2p+r+o for right-leteral slip   
    # gmt_ls can be -St0.5p/2p+r+o for thrust
    # gmt_d is a keyword to specify a system shift 
    # MAP_ANNOT_OFFSET_PRIMARY is the option to control ofsets between arrow 
    # and the fault line.
    #
    # 
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'    
    #         
    gmt_command=('gmt psxy "%s" %s %s %s %s %s %s %s -P %s %s %s %s %s %s'% \
                 (infault,gmt_proj,\
                 gmt_ext,gmt_ls,gmt_lp,gmt_iscov,gmt_iscon,\
                 gmt_G,gmt_B,gmt_d,gmt_xoff,gmt_yoff,gmt_outstr,gmt_outps))
    #
    print(" pGMT: %s" % gmt_command)
    flag,info,errs = gmt_run(gmt_command)
    return flag,info,errs
###############################################################################         
def gmt_pshistogram(infile,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='-B',\
                   gmt_ext='-R',gmt_proj='-J',gmt_xoff='-X0i',gmt_g='',\
                   gmt_yoff='-Y0i',gmt_l='-L0.5p,blue',gmt_a='-A',\
                   gmt_n='-N0',gmt_w='-W2+b',gmt_z='-Z1'):
    '''
    gmt_z, types of histogram
    0: counts, 1: frequency
    '''
    #
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #
    gmt_command=('gmt pshistogram %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s'%\
                 (infile,gmt_proj,gmt_w,gmt_n,gmt_a,gmt_z,\
                 gmt_ext,gmt_l,gmt_iscov,gmt_iscon,gmt_xoff,\
                 gmt_yoff,gmt_B,gmt_g,gmt_outstr,gmt_outps))
    #
    print(' pGMT: %s' % gmt_command)
    #
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait() 
    return True
#     
###############################################################################
#         
def gmt_psxyz(ingmt,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='-B',\
              gmt_ext='-R',gmt_proj='-J',gmt_xoff='-X0i',gmt_yoff='-Y0i',\
              gmt_lp='-W0.5p,red',gmt_p='-P',gmt_pv='-pz135/30+v10/5',\
              gmt_ls='-Sf0.5p,red',gmt_c='',gmt_g='',gmt_l='',\
              gmt_w='-W0.5p,gray'):
    #
    # gmt_l flag for filling polygons.  -L for yes and <no> for not
    #
    # gmt_g color for filling a polygon/or all polygons
    #       -G- turn filling off
    # gmt_lp  line properties
    #       -W- turn outline off
    # gmt_vp is perspective view
    # Examples from GMT official website
    # gmt psxyz -R-75/-60/-50/-40/0/999 -JM-67.5/-45/16 -JZ8\
    #     -W1p,black -pz135/30+v10/5 -O >> mag.ps
    #
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #
    if gmt_w is not None:
        gmt_lp = gmt_w
    #
    gmt_command=('gmt psxyz %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s' % \
                 (ingmt,gmt_proj,gmt_c,gmt_pv,gmt_l,\
                  gmt_ext,gmt_lp,gmt_iscov,gmt_iscon,gmt_ls,gmt_xoff,\
                  gmt_yoff,gmt_B,gmt_g,gmt_p,gmt_outstr,gmt_outps))
    #
    print(' pGMT: %s' % gmt_command)
    flag,info,errs = gmt_run(gmt_command)
    #
    return flag,info,errs
#
###############################################################################
#    
def gmt_psxy_mline(infile,gmt_outps,gmt_iscov='-O',gmt_iscon='-K',gmt_B='-B',\
                   gmt_ext='-R',gmt_proj='-J',gmt_xoff='-X0i',gmt_g='',\
                   gmt_yoff='-Y0i',gmt_lp='-W0.5p,red',gmt_p='-P',gmt_t='',\
                   gmt_l=''):
    #
    '''
    gmt_t flag for transparency
    gmt_l -L to force the data as a closed polygon
    '''
    if gmt_iscov.upper()=="-O":
       gmt_outstr='>>'
    else:
       gmt_outstr='>'
    #
    gmt_command=('gmt psxy %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s'% \
                 (infile,gmt_proj,gmt_l,\
                 gmt_ext,gmt_lp,gmt_iscov,gmt_iscon,gmt_xoff,gmt_t,\
                 gmt_yoff,gmt_B,gmt_g,gmt_p,gmt_outstr,gmt_outps))
    print(' pGMT: %s' % gmt_command)
    #
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait() 
    return True
###############################################################################
def gmt_psrose(inp,gmt_outps,gmt_a='-Ar10',\
              gmt_g='-G',gmt_ext='-R', gmt_proj='-JX2i',gmt_s='-Sn',\
              gmt_B='-B',gmt_iscov='-O',gmt_xoff='-X0i',gmt_w='-W0.1p',\
              gmt_yoff='-Y0i',gmt_iscon='-K'):
    #
    if gmt_iscov.upper().strip()=="-O":
        gmt_outstr='>>'
    else:
        gmt_outstr='>'
    gmt_command=('gmt psrose %s %s %s %s %s %s %s %s %s %s %s %s %s %s') % \
              (inp,gmt_proj,gmt_s,gmt_a,gmt_g,gmt_ext,gmt_B,gmt_xoff,gmt_yoff,\
               gmt_w,gmt_iscon,\
               gmt_iscov,gmt_outstr,gmt_outps)
    print(" pGMT: %s" % gmt_command)
    flag,info,err = gmt_run(gmt_command)
    #
    return flag
              
###############################################################################
def gmt_pstext(x,y,instr,gmt_outps,\
              gmt_f='-F+a0+f7p,Helvetica,255/255/255+jBL',\
              gmt_g='-G',gmt_ext='-R', gmt_D='-D0/0',gmt_proj='-J',\
              gmt_B='-B',gmt_iscov='-O',gmt_xoff='-X0i',gmt_w='-W0.1p',\
              gmt_yoff='-Y0i',gmt_iscon='-K',gmt_n='',gmt_T='-TO'):
    #
    # gmt_T, to shape the type of corners of the rectangle of the text.
    #        -TO will be used for rounded corners.
    #
    infile = None
    if x is None:
        x,y=' ',' '
        #
    else:
        if y is None and os.path.exists(x):
           infile = x
        #
        x,y=str(x),str(y)
    #
    if gmt_iscov.upper()=="-O":
        gmt_outstr='>>'
    else:
        gmt_outstr='>'
    #
    if infile is not None:
       gmt_command = \
       ('gmt pstext %s %s %s -P %s %s %s %s %s %s %s %s %s %s %s %s %s' % \
                  (x,gmt_proj,gmt_ext,gmt_f,gmt_g,gmt_B,gmt_iscov,\
                  gmt_xoff,gmt_yoff,gmt_iscon, \
                  gmt_w,gmt_n,gmt_D,gmt_T,gmt_outstr,gmt_outps))
    else:
       if '"' not in instr:
           instr = '"%s"' % instr
       #
       gmt_command = ('echo %s %s %s | gmt pstext %s %s -P %s %s %s %s %s %s %s %s %s %s %s %s %s' % \
                  (x,y,instr,gmt_proj,gmt_ext,gmt_f,gmt_g,gmt_B,gmt_iscov,\
                  gmt_xoff,gmt_yoff,gmt_iscon,gmt_w,gmt_n,gmt_D,\
                  gmt_T,gmt_outstr,gmt_outps))
                  
    print(' pGMT: %s' % gmt_command)    
    flag,info,errs = gmt_run(gmt_command)
    return flag
###############################################################################
def gmt_grd2cpt(ingrd,outcpt,minv=0,maxv=None,cpt='gray'):
    #
    if maxv is None:
        maxv = gmt_amp2max(ingrd)
    #
    gmt_command = 'gmt grd2cpt %s -Z -D -L%f/%f -C%s > %s' % \
           (ingrd,minv,float(maxv),cpt,outcpt) 
    print(' pGMT: %s' % gmt_command)    
    flag,info,errs = gmt_run(gmt_command)
    
    return flag
def gmt_makecpt(incpt,outcpt,minv=-5,maxv=5,zint=0.1,\
                isrev=False,dflag=False,gmt_m='-M -Fr'):
    #
    if isrev:
        revstr='-I'
    else:
        revstr=''
    if dflag:
       # Flag of -D, Set back- and forground color to match the bottom/top limits
       dstr='-D'
    else:
       dstr=''
    #
    gmt_command = ('gmt makecpt -T%s/%s/%s %s -C%s %s %s > %s' % \
                   (str(minv),str(maxv),\
                    str(zint),dstr,incpt,revstr,gmt_m,outcpt))
    print(' pGMT: %s' % gmt_command)
    #
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait() 
    if os.path.exists(outcpt):
       return True
    else:
       return False
###############################################################################
def gmt_psscale(incpt,gmt_outps,zinterv=5,gmt_p='',gmt_xoff='-X0i',\
                gmt_yoff='-Y0i',gmt_iscov='-O',gmt_iscon='-K',\
                xtitle='InSAR LOS Changes',\
                unit='(cm)',loc='-Dx8c/1c+w12c/0.5c+jTC+h',\
                isbf=False,fillcolor='120/120/120',\
                shade_sx='0.0i',shade_sy='0.5i',norun=False,\
                shade_gap='0p',shade_color='white',tgap='10p'):
    #
    # note that 255/255/255, such a color definition cannot be accepted in 
    # the current version, which may be due to the system settings.
    # by Wapeng Feng, @SYSU, Guanghzou, 2019/07/24
    # So a color name, like "white" is highly recommended since this date.
    #
    if isbf:
       gmt_bf = '-E'
    else:
       gmt_bf = ' '
    #
    if len(fillcolor)==0:
        bcolor=''
        sfillcolor=''
    else:
        bcolor='+g%s' % fillcolor
        sfillcolor=('-F%s+s%s/%s/%s+r%s+c3p/3p/2p/%s' % \
                    (bcolor,shade_sx,shade_sy,shade_color,shade_gap,tgap)) 
    #
    if gmt_iscov == "-O":
       constr='>>'
    else:
       constr='>'
    # 
    if unit == "":
       BYstr=""
    else:
       BYstr=('-By+l"%s"' % unit)
    if xtitle == "":
       BXstr=("-Bx%s" % str(zinterv))
    else:
       BXstr=('-Bx%s+l"%s"' % (str(zinterv),xtitle))
    #
    gmt_command = ('gmt psscale %s %s -C%s -I %s %s %s %s %s %s %s %s %s %s' % \
                  (str(gmt_xoff),str(gmt_yoff),str(incpt),str(loc),\
                   str(BXstr),str(BYstr),str(gmt_bf),\
                   str(gmt_iscon), str(gmt_iscov),str(sfillcolor),\
                   str(gmt_p),str(constr),str(gmt_outps)))
    #
    print(' pGMT: %s' % gmt_command)
    #
    if norun:
       flag = gmt_command
    else:
       flag,info,errs = gmt_run(gmt_command)
    #
    return flag      
###############################################################################           
def gmt_ps2raster(ps,of='G',kml=False,gmt_res='360',gmt_p=''):
    #
    if kml:
       png=os.path.basename(ps).split('.')[0]+'.png'
       # inps = os.path.basename(ps)
       # outpng = os.path.dirname(ps)+'/'+png
       inps = os.path.basename(ps)
       psdir  = os.path.dirname(os.path.abspath(ps))
       topdir = os.getcwd()
       os.chdir(psdir)
       gmt_command=('gmt psconvert %s -A -T%s -E%s -TG -P -S -V -W+k+t"%s"' \
                    % (inps,of,gmt_res,png))
       print(' pGMT: %s' % gmt_command)
       subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
       flag = subinfo.wait() 
       prints, errs = subinfo.communicate()
       prints = pSAR.util.bytestoutf8(prints)
       os.chdir(topdir)
    else:
       gmt_command=('gmt psconvert %s -A -T%s -E%s %s' % (ps,of,gmt_res,gmt_p))
       print(' pGMT: %s' % gmt_command)
       subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
       flag = subinfo.wait() 
       prints, errs = subinfo.communicate()
       prints = pSAR.util.bytestoutf8(prints)
    return flag,prints,errs

###############################################################################                           
def gmt_defaults():
    #
    gmt_command=('gmt gmtdefaults -L')
    subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                   stderr=subprocess.PIPE,shell=True)
    subinfo.wait()                             
    gmtinfo, errID = subinfo.communicate() 
    gmtinfo = pSAR.util.bytestoutf8(gmtinfo)
    #
    gmt_sysinfo={}
    for cline in gmtinfo.split("\n"):
        #
        #print(type(cline),len(cline))
        if (len(cline) > 0 and cline[0] != "#"):
           keyname,value = cline.split('=')
           keyname = keyname.split("\t")[0]
           keyname = keyname.rstrip()
           gmt_sysinfo[keyname]= value
    # 
    return gmt_sysinfo
    
    
###############################################################################    
# 
def gmt_gmtset(**kwargs):
    #
    # MAP_ANNOT_OFFSET_PRIMARY is also functioning 
    # on the offsets between fault and arrows
    #
    gmt_sysinfo = gmt_defaults()
    #
    flag = None
    for name, value in kwargs.items():
        # print(' pGMT: gmt_gmtset: %s = %s' % (name.upper(),value))
        if name.upper() in gmt_sysinfo:
           print(' pGMT: gmt gmtset %s = %s' % (name.upper(),value))
           gmt_command=('gmt gmtset %s = %s' % (name.upper(),value))
           flag,info,errs = gmt_run(gmt_command)
    #
    return flag
###############################################################################
def gmt_grdview(demgrd,grd,grad=None,gmt_ext=None,\
                gmt_xoff='-X4i',gmt_yoff='-Y4i',\
                gmt_output='test.ps',gmt_proj='-JM13c',gmt_iscon='-K',\
                gmt_iscov='-O',gmt_snew='',gmt_xinv='0.5',gmt_yinv='0.5',\
                gmt_zproj='-JZ1c',gmt_p='-p150/45',gmt_n='-nb',\
                gmt_xl='',gmt_yl='',gmt_titel='',gmt_bz='',gmt_N='-N-2+ggray',\
                gmt_t='-t0',gmt_c='-C',gmt_kml='',gmt_q='-Qc',\
                gmt_s='',gmt_T=''):
    # gmt_kml="-Q --MAP_FRAME_TYPE=inside"
    # gmt_q, nan will be set transparency
    # gmt_N, -N-6+glightgray
    # gmt_n, interpolation
    gmt_g = ""
    if grd is not None:
       gmt_g = '-G%s' % grd
    #
    if gmt_ext is None:
       gmt_ext = gmt_grd2gext(demgrd)
    #
    if gmt_titel is None:
        gmt_titel = ""
    #
    if (gmt_snew is not None and len(gmt_snew.strip())>0):
        gmt_b1 = ('-B%s' % gmt_snew)
    if (len(gmt_snew.strip()) > 0 and len(gmt_titel.strip())>0):
        # print(gmt_titel)
        gmt_b1 = '%s+t"%s"' % (gmt_b1,gmt_titel)
    #
    if (gmt_xl is not None and gmt_yl is not None):
        gmt_b2 = ('-Bx%s+l"%s" -By%s+l"%s"' % (gmt_xinv,gmt_xl,gmt_yinv,gmt_yl))
    else:
        gmt_b2 = ''    
    gmt_B = ('%s %s ' % (gmt_b1,gmt_b2) )
    #
    #
    #
    if gmt_iscov.upper()=="-O":
       gmt_output = ('>> %s'%  gmt_output)
    else:
       gmt_output = ('> %s' % gmt_output)
    #
    gmt_ind = ""
    if (grad is not None and os.path.exists(grad)):
        gmt_ind = ('-I%s' % grad)
    #
    #
    if len(gmt_kml)>0:
        gmt_B=''
    #
    gmt_command = ('gmt grdview %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s -P %s %s' % \
                   (demgrd,gmt_g,gmt_proj,gmt_zproj,gmt_p,gmt_ext,gmt_B,\
                                   gmt_xoff,gmt_yoff,gmt_t,gmt_c,gmt_n,gmt_ind,\
                                   gmt_iscon,gmt_iscov,gmt_s,gmt_T,gmt_N,gmt_bz,\
                                   gmt_kml,gmt_q,gmt_output))
    print(' pGMT: %s' % gmt_command)
    # 
    flag,info,errs = gmt_run(gmt_command)
    #
    return flag
#
###############################################################################
#      
def gmt_grdimage(grd,grad=None,gmt_ext=None,gmt_xoff='4i',gmt_yoff='4i',\
                 gmt_output='test.ps',gmt_proj='-JM4i',gmt_iscon='-K',\
                 gmt_iscov='-O',gmt_snew='SnEW',gmt_xinv='10',gmt_yinv='10',\
                 gmt_xl='',gmt_yl='',\
                 gmt_title=None,gmt_dpi='-E280',\
                 gmt_transparency='0',gmt_cpt='seis',\
                 gmt_kml='',gmt_q='',gmt_p='-P',af=False):
    #
    # gmt_kml="-Q --MAP_FRAME_TYPE=inside"
    # gmt_q, nan will be set transparency
    # 
    if gmt_ext is None:
       ginfo,gerr = gmt_grdinfo(grd)
       gmt_ext = ('-R%s/%s/%s/%s' % (ginfo['X_FIRST'],ginfo['X_MAX'],\
                                     ginfo['Y_MIN'],ginfo['Y_FIRST']))
    #
    if (gmt_title is not None and len(gmt_title.strip()) == 0):
        gmt_title = None
    #
    if (gmt_snew is not None):
        gmt_b1 = ('-B%s' % gmt_snew)
    else:
        gmt_b1 = ''
    if len(gmt_b1.strip())>0 and gmt_title is not None:
        gmt_b1 = '%s+t"%s"' % (gmt_b1,gmt_title)
    #
    if gmt_xinv is not None:
       gmt_bx='-Bx%s' % gmt_xinv
    else:
       gmt_bx = ""
    if gmt_yinv is not None:
       gmt_by='-By%s' % gmt_yinv
    else:
       gmt_by = ""
    #
    if gmt_xl is not None and len(gmt_bx.strip())>0:
       gmt_bx = '%s+l"%s"' % (gmt_bx,gmt_xl)
    if gmt_yl is not None and len(gmt_by.strip())>0:
       gmt_by = '%s+l"%s"' % (gmt_by,gmt_yl)
    #
    gmt_b2 = '%s %s' % (gmt_bx,gmt_by)
    # 
    gmt_B = ('%s %s ' % (gmt_b1,gmt_b2) )
    #
    if af:
        gmt_B = ' -Baf '
    #
    gmt_t = ('-t%s' % gmt_transparency)
    gmt_c = ('-C%s' % gmt_cpt)
    gmt_x = ('-X%s' % gmt_xoff)
    gmt_y = ('-Y%s' % gmt_yoff)
    #
    #
    if gmt_iscov.upper()=="-O":
       gmt_output = ('>> %s'%  gmt_output)
    else:
       gmt_output = ('> %s' % gmt_output)
    #
    if (grad is not None and os.path.exists(grad)):
        gmt_ind = ('-I%s' % grad)
    else:
        gmt_ind = ''
    #
    if len(gmt_kml)>0:
        gmt_B=''
    #
    gmt_command = ('gmt grdimage %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s'\
                   % (grd,gmt_proj,gmt_ext,gmt_B,\
                      gmt_x,gmt_y,gmt_t,gmt_c,gmt_ind,\
                      gmt_iscon,gmt_iscov,gmt_kml,gmt_dpi,gmt_q,gmt_p,gmt_output))
                   #
    print(' pGMT: %s' % gmt_command)
    # 
    flag,info,err = gmt_run(gmt_command)
    #
    if flag != 0:  
       print(' pGMT: pGMT.gmt_grdimage has error: %s' % err)
    return flag
#
###############################################################################
#          
def gmt_grd2xyz(grdfile,xyzfile,isbin=True):
    #
    if isbin:
       gmt_biout = '-bo3'
    else:
       gmt_biout = ''
    gmt_command = ('gmt grd2xyz %s %s > %s' % (grdfile,gmt_biout, xyzfile))
    print(" pGMT: %s " % gmt_command)
    subprocess.Popen(gmt_command,shell=True).wait()
    #
    return True
###############################################################################
def gmt_surface(xyz,grd,gext=None,ginc=None,binary=True,A=1,gmt_L='-Ll0'):
    #
    if (gext is None or ginc is None):
       return False
    #
    if binary:
       bistr="-bi3"
    else:
       bistr=""
    # 
    #
    fout=open('pgmt_error.inf','a')
    #
    gmt_command = ('gmt surface %s -G%s %s %s %s -T0.05 -A%f -C0.01 %s' % \
                                             (xyz,grd,bistr,gext,ginc,A,gmt_L))
    print(" pGMT: %s" % gmt_command)
    #
    flag = subprocess.Popen(gmt_command,stderr=fout,shell=True).wait()
    fout.close()
    #
    return flag
###############################################################################
def gmt_grds2mask(grd1,grd2,outmask):
    #
    nozero1 = outmask+'_1.msk'
    nozero2 = outmask+'_2.msk'
    #
    gmt_grdmath(nozero1,gext='',grd1=grd1,grd2='0',gmath='NEQ')
    gmt_grdmath(nozero2,gext='',grd1=grd2,grd2='0',gmath='NEQ')
    #
    gmt_grdmath(outmask,gext='',grd1=nozero1,grd2=nozero2,gmath='MUL')
    if os.path.exists(nozero1):
       os.remove(nozero1)
    if os.path.exists(nozero2):
       os.remove(nozero2)
    #
    if os.path.exists(outmask):
       return True
    else:
       return False
###############################################################################
def gmt_resampbyRSC(inroi,outroi,refrsc):#
    #
    gmt_roi2grd(inroi,inroi+'.grd',minv=-5,maxv=5,scale=1,unit="m",\
                gr='',isdisp=False,factor=None,gmt_r='',\
                iswrap=False,zerov=None,ishelp=False)
    #
    gmt_dem2roibyrsc(inroi+'.grd',refrsc,inroi+'.r.grd',gmt_r='-r',interp='b')
    gmt_grd2roi(inroi+'.r.grd',outroi,fmt='f')
    #
    if os.path.exists(outroi):
        return True
    else:
        return False
       
def gmt_xyz2grd(xyz,grd,gext=None,surface=False,dtype=None,\
                gmt_r='-r',ginc=None,binary=True,A=1,di='-di0'):
    #
    #
    if (gext is None or ginc is None):
       return False
    #
    if binary:
       bistr="-bi3f"
       if dtype is not None:
           bistr = '-bi3%s' % dtype
    else:
       bistr=""
    # 
    #
    if surface:
       gmt_command = ('gmt surface %s -G%s %s %s %s -T0.1 -N800 -A%f -C0.0001' %\
                      (xyz,grd,bistr,gext,ginc,A))
    else:
       # fix pixel registration
       # by Wanpeng Feng, @Ottawa, 2016-11-29
       #
       gmt_command = ('gmt xyz2grd %s %s -G%s %s %s %s %s ' % \
                      (xyz,gmt_r,grd,bistr,gext,ginc,di))
    #
    print(" pGMT: %s" % gmt_command)
    flag,info,err = gmt_run(gmt_command)
    #
    return flag
    #
###############################################################################
def gmt_greenspline(xyz,outgrd,gext,ginc,S='-Sc',D='-D1',C='-Cn500'):
    #
    gmt_command = ('gmt greenspline %s -G%s %s %s %s %s %s' % (xyz,\
                      outgrd,S,gext,ginc,C,D))
    print(" pGMT: %s"% gmt_command)
    flag,info,err= gmt_run(gmt_command)
    return flag
def gmt_grdfilter(ingrd,outgrd,F='-Fg10/10',D='-Dp'):
    # -Fg10/10, Gaussian filter, with 10 by 10 pixels
    # -Dp, x and y as width in pixel, F should be given with odd numbers, e.g. 
    #   -Fg11/11
    #
    gmt_command = ('gmt grdfilter %s -G%s %s %s' % (ingrd,\
                      outgrd,F,D))
    print(" pGMT: %s"% gmt_command)
    flag,info,err= gmt_run(gmt_command)
    return flag
def gmt_gradient(demgrd,gradgrd,azi1=45,azi2=85,amp=1.5):
    #
    gmt_command = ('gmt grdgradient %s -G%s -Ne%s -Da -A%s/%s ' % (demgrd,\
                      gradgrd,str(amp),str(azi1),str(azi2)))
    #
    print(" pGMT: %s"% gmt_command)
    flag,info,err= gmt_run(gmt_command)
    return flag
#
###############################################################################        
def gmt_dem2grd(demfile,demgrd,refgrd=None,isgrad=False,azi1=0.,azi2=270.,\
                               amp=1.5):
    #
    #
    tmp_demgrd = demgrd.split('.')[0]+'.tmp.grd'
    gmt_roi2grd(demfile,tmp_demgrd)
    #
    if refgrd is not None:
       ginfo,gerror = gmt_grdinfo(refgrd)
       #
    else:
       demrsc = demfile + '.rsc'
       ginfo,ext = pSAR.roipac.rsc_read(demrsc)
    #
    gmt_ext=('-R%s/%s/%s/%s' % (ginfo['X_FIRST'],ginfo['X_MAX'],\
                                ginfo['Y_MIN'],ginfo['Y_FIRST']))
    gmt_inc=('-I%s/%s'%(ginfo['X_STEP'],str(np.float64(ginfo['Y_STEP'])*-1)))
    #
    # ROI file to xyz 
    dem_xyz = demfile+'.xyz'
    gmt_grd2xyz(tmp_demgrd,dem_xyz,isbin=True)
    #
    gmt_command = ('gmt surface %s -G%s -bi3 %s %s -T0.25 -C0.1 ' % \
                                              (dem_xyz,demgrd,gmt_ext,gmt_inc))
    #
    print(" pGMT: %s" % gmt_command)
    GMTinfo = subprocess.Popen(gmt_command,shell=True).wait()
    # print(" gmt_dem2grd: %s " % GMTinfo)
    # shutil.move(tmp_demgrd,demgrd)                        
    #
    if GMTinfo<=1:
       demgrd_grad = demgrd+'.grad'
       gmt_command = ('gmt grdgradient %s -G%s -Ne%s -Da -A%s/%s ' % (demgrd,\
                      demgrd_grad,str(amp),str(azi1),str(azi2)))
       #
       print(" pGMT: %s"% gmt_command)
       GMTinfo = subprocess.Popen(gmt_command,stdout=subprocess.PIPE,\
                            stderr=subprocess.PIPE,shell=True).wait()
       if GMTinfo<=1:                    
          shutil.move(demgrd_grad,demgrd)               
          print(" pGMT: *** %s has been replaced by %s" % (demgrd,demgrd_grad))
    #
    return GMTinfo
##############################################################################
def gmt_rsc2ginfo(rsc,inc=None,xinc=None,yinc=None):
    #
    # Note: xinc and yinc are both positive
    # by Wanpeng Feng, @CCRS/NRCan, 2017-07-12
    #
    ginfo,ext = pSAR.roipac.rsc_read(rsc)
    #
    if inc is not None:
        xinc,yinc = inc,inc
    #        
    if (xinc is None or yinc is None):
       gmt_ext=('-R%s/%s/%s/%s'%(ginfo['X_FIRST'],ginfo['X_MAX'],\
                                 ginfo['Y_MIN'],ginfo['Y_FIRST']))
       gmt_inc=('-I%s/%s'%(ginfo['X_STEP'],str(np.float64(ginfo['Y_STEP'])*-1)))
    else:
       #
       # in default ROI_PAC is in pixel-registered projection...
       #
       nx = (float(ginfo['X_MAX']) - float(ginfo['X_FIRST'])) / xinc + 1
       ny = (float(ginfo['Y_FIRST']) - float(ginfo['Y_MIN'])) / yinc + 1
       x_max =  float(ginfo['X_FIRST']) + (nx-1) * xinc
       y_min =  float(ginfo['Y_FIRST']) - (ny-1) * yinc
       # 
       gmt_ext = ("-R%s/%s/%s/%s" % (ginfo['X_FIRST'],str(x_max),\
                                   str(y_min),ginfo['Y_FIRST']))
       gmt_inc = ("-I%s/%s" % (str(xinc),str(yinc)))
       #
    return gmt_ext,gmt_inc
    
###############################################################################    
def gmt_grdinfo(grd,gmt_info=None):
    #
    gmt_command = ('gmt grdinfo -L %s'% grd)
    #
    if os.path.exists(grd):
      subinfo = subprocess.Popen(gmt_command, stdout=subprocess.PIPE,\
                                     stderr=subprocess.PIPE,shell=True)
      # subinfo = subprocess.Popen(gmt_command)
      subinfo.wait()                             
      gmtinfo, errID = subinfo.communicate()    
      gmtinfo = pDATA.bytestoutf8(gmtinfo)
      #
    else:
      gmtinfo = None
    #
    if gmt_info is None:
       gmt_info = {}
    for cline in gmtinfo.split("\n"):
        # print(cline)
        if cline.find('x_min') > -1:
           tmp = cline.split(' ')
           gmt_info['X_FIRST'] = tmp[2]
           gmt_info['X_MAX']   = tmp[4]
           gmt_info['X_STEP']  = tmp[6]
           #
           if "nx:" in cline:
              width = cline.split()[-1]
           if "n_columns:" in cline:
              width = cline.split()[-1]
           #
           gmt_info['WIDTH']   = width
           #
        if cline.find('y_min') > -1:
           tmp = cline.split(' ')
           gmt_info['Y_FIRST'] = tmp[4]
           gmt_info['Y_MIN']   = tmp[2]
           gmt_info['Y_STEP']  = str(np.float64(tmp[6])*-1)
           #
           if "ny:" in cline:
              file_length = cline.split('ny:')[1]
           if "n_rows:" in cline:
              file_length = cline.split()[-1]
           #
           gmt_info['FILE_LENGTH'] = file_length
           #
        if cline.find('z_max') > -1:
           tmp = cline.split(' ')
           gmt_info['Z_MIN'] = tmp[2]
           gmt_info['Z_MAX'] = tmp[4]
    #
    for ckey in gmt_info.keys():
        gmt_info[ckey] = gmt_info[ckey].replace(" ","")
        #
    #
    return gmt_info,errID
###############################################################################
def gmt_rsc2ext(rsc,ishelp=False,ll180=False):
    #
    helpstr=\
    ''' pGMT.gmt_rsc2ext(rsc,ishelp=False)
        ++++++++++++++++++++++++++++++++++++++++++++++
        To calculate the extents of the given ROI_PAC like file.
        -rsc, a header file of the ROI_PAC binary file
    '''
    if ishelp:
        print(helpstr)
        return None
    #
    info,ext=pSAR.roipac.rsc_read(rsc,ll180=ll180)
    #
    gmt_ext='-R'+str(ext[0])+'/'+\
                 str(ext[1])+'/'+\
                 str(ext[2])+'/'+\
                 str(ext[3])
    #
    px = np.float64(info['X_STEP'])
    py = np.float64(info['Y_STEP'])
    #
    if py < 0:
        py = py * -1.
    #
    gmt_inc = '-I'+str(px)+'/'+str(py)            
    return gmt_ext,gmt_inc
    
###############################################################################
def gmt_amp2max(inampgrd):
    gmt_command = "gmt grdinfo -L2 %s | grep stdev | awk '{ print 3*$5}'" % \
                   inampgrd
    print(' pGMT: %s' % gmt_command)
    GMTinfo,info,err = gmt_run(gmt_command)
    info = info.split('\n')[0]
    #
    return info
###############################################################################
def gmt_roi2grd(roifile,outgrd,minv=-5,maxv=5,scale=1,unit="m",\
                gr='',isdisp=False,factor=None,gmt_r='',\
                iswrap=False,zerov=None,ishelp=False,ll180=False):
    #
    helpstr=\
    ''' pGMT.gmt_roi2grd(roifile,outgrd,ishelp=False)
        ++++++++++++++++++++++++++++++++++++++++++++++
        To convert a ROI_PAC like binary file into GMT grid.
        -roifile, simple binary file with a rsc header
        -outgrd,  simple GMT grd file
        
    '''
    if ishelp:
        print(helpstr)
        return None
    #
    # environ    = os.environ.copy()
    losroi     = None
    losroi_rsc = None
    #
    if isdisp:
       #
       roibase = os.path.basename(roifile).split('.')[0]
       losroi  = roibase+'.iMg'
       losroi_rsc=losroi+'.rsc'
       print(" pGMT: phs TO LOS displacement: %s" % losroi)
       pSAR.roipac.roi2los(roifile,losroi,unit=unit)
       #
       print(" pGMT: %s exists %s" % (losroi,os.path.exists(losroi)))
       roifile = losroi
       fmt     = pSAR.roipac.roi_to_fmt(roifile)
       #
    #
    roifile_fullpath = os.path.abspath(roifile)
    roifile_dirname  = os.path.dirname(roifile_fullpath)
    roifile_rootname = os.path.basename(roifile_fullpath).split('.')[0]   
    roifile_wrap     = os.path.join(roifile_dirname,roifile_rootname+'.tmp') 
    tmporary_roi     = os.path.join(roifile_dirname,roifile_rootname+'.tmp')
    #
    factor_db = []
    if factor is not None:
       #
       pSAR.roipac.roi_math(roifile,roifile + '.math.img' , muls=factor) #
       roifile_fullpath = roifile + '.math.img'
       factor_db        = roifile + '.math.img'
       roifile          = roifile + '.math.img'
    #
    if iswrap:
       # 
       if zerov is None:
           szerov = 'None'
       else:
           szerov = str(zerov)
       #
       print(" pGMT: rewrapping %s with zero setting of %s" % (roifile,szerov))
       #
       flag = pSAR.roipac.roi_rewrap(roifile,roifile_wrap,scale=1,\
                                     minv=minv,maxv=maxv,zerov=zerov)
       #
       #
       if not flag:
           print(" ERROR: gmt_roi2grd failed due to a failure when rewrapping roi")
           return None
       roifile = roifile_wrap
       #
    else:
       #
       if zerov is not None:
           print(" Replace zero in %s with %s" % (roifile,zerov))
           pSAR.roipac.roireplaceZERO(roifile,zerov,roifile_wrap)
           roifile = roifile_wrap
    #      
    rsc = roifile + '.rsc'
    fmt = pSAR.roipac.roi_to_fmt(roifile)
    ginfo,ext = pSAR.roipac.rsc_read(rsc,ll180=ll180)
    # gext = '-R1/%d/1/%d' % (int(ginfo['WIDTH']),int(ginfo['FILE_LENGTH']))
    #
    #
    if fmt.upper()=='INT16':
       gmt_of='-ZTLh'
    elif fmt.upper() == "INT8":
       gmt_of='-ZTLc'
    else:
       gmt_of='-ZTLf'
    #
    gmt_ext,gmt_in = gmt_rsc2ext(rsc,ll180=ll180)
    #
    # The best choice for roi2grd is grdline registration.
    # developed by Wanpeng Feng, @NRCan, 2016-11-29
    #
    gmt_command=('gmt xyz2grd %s %s -G%s %s %s %s %s' % \
                 (roifile,gr,outgrd,gmt_ext,gmt_r,gmt_in,gmt_of))
    # below can be used to guarrenty a success in conversion.
    # gmt_command=('gmt xyz2grd %s %s -G%s %s %s %s %s' % \
    #             (roifile,gr,outgrd,gext,gmt_r,'-I1/1',gmt_of))
    # gmt_command = 'pSAR_imgformat.py %s %s -of GMT' % (roifile,outgrd) 
    #
    print(' pGMT: %s' % gmt_command)
    GMTinfo,info,err = gmt_run(gmt_command)
    #
    #
    # gmt_command='gmt grdedit %s -A %s' % (outgrd,gmt_ext)
    # print(' pGMT: %s' % gmt_command)
    # GMTinfo,info,err = gmt_run(gmt_command)
    #
    if (scale > 1 and GMTinfo <= 1):
       resgrd   = outgrd.split('.')[0]+'_SCALED.grd'
       gmt_ginc = gmt_grd2inc(outgrd,scale=scale)
       GMTinfo  = gmt_grdsample(outgrd,resgrd,ginc=gmt_ginc)
       shutil.move(resgrd,outgrd)
       #
    #
    if (len(factor_db)>0 and os.path.exists(factor_db)):
       os.remove( factor_db )
       os.remove( factor_db + '.rsc' )
    #
    if losroi is not None:
       os.remove(losroi)
       os.remove(losroi_rsc)
    if os.path.exists(tmporary_roi):
       os.remove(tmporary_roi)
       if os.path.exists(tmporary_roi+'.rsc'):
          os.remove(tmporary_roi+'.rsc')
        
    return GMTinfo
#
###############################################################################
def gmt_grd2geotiff(grd,geotiff,errlog='pgmt_error.inf'):
    #
    gmt_command = ('gmt grdconvert %s %s=rd:GTiff' % (grd,geotiff))
    print(' pGMT: %s' % gmt_command)
    # 
    fout    = open(errlog,'a')
    GMTinfo = subprocess.Popen(gmt_command,\
                               stderr=fout,shell=True).wait()
    fout.close()
    #                           
    return GMTinfo
###############################################################################
def gmt_geotiff2grd(geotiff,grd,errlog='pgmt_error.inf',fmt='float32'):
    #
    gmt_command = ('gdal_translate -of GMT -ot %s %s %s' % (fmt,geotiff,grd))
    print(' pGMT: %s' % gmt_command)
    # 
    fout    = open(errlog,'a')
    GMTinfo = subprocess.Popen(gmt_command,\
                               stderr=fout,shell=True).wait()
    fout.close()
    #                           
    return GMTinfo      
