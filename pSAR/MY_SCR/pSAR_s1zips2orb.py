#!/usr/bin/env python
#
#
#
import numpy as np
import os
import sys
import glob 
import datetime
# import pGAMMA
import pSAR
import pS1

##################################################
def s1zip2info(inzip):
    #
    zipfile = os.path.basename(inzip)
    zipfile = zipfile.split('.zip')[0]
    info = zipfile.split('_')
    return  info
#
if len(sys.argv) < 2 or '*' in sys.argv[1]:
    helpstr = \
            '''

            %s [*.zip or <specific>.zip] -orbdir [] -link -c -source ['asf' or 'esa']
            ++++++++++++++++++++++++++++++++++++++
            To grap precise orbit files for zip(s)
            #
            -orbdir in default the system S1_ORB will be applied.
                    If S1_ORB does not exist, the syste will save orb 
                    in the curernt folder.
            -model "resorb" in default. poeorb can be another option.
            -link   flag, if given, the EOF orbit file will be linked into the current folder.
            -c      flag, if given, the EOF orbit file will be copied into the current folder
            -update False, in default
            -tshift shift days, 1 day in default.
            #
            
            
            
            by Wanpeng Feng, @SYSU(Guangzhou), 2018-11-2
            #
            by Wanpeng Feng, @SYSU(Guangzhou), 2021/11/27
            since 2021/11/xx, ASF has strong constraints for users outside US. So I add a new 
            keyword, source.
            -source 'esa' will be set as default.


            '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
#
#############################################################
#
pSAR.util.log(sys.argv)
#
#
tshift = 1 
model = 'resorb'
link = False
update = False
iscopy = False
source = 'esa'
#
orbdir = None
for ci,ckey in enumerate(sys.argv):
    if ckey == '-tshift':
        tshift = int(sys.argv[ci+1])
    if ckey == '-c':
        iscopy = True
    if ckey == '-update':
        update = True
    if ckey == '-orbdir':
        orbdir = sys.argv[ci+1]
    #
    if ckey == '-model':
        model = sys.argv[ci+1]
    if ckey == '-link':
        link = True
    if ckey == '-source':
        source = sys.argv[ci+1]
#
##########################################################################
#
if orbdir is None:
   #
   orbdir = os.environ.get('S1_ORB') 
   #
   if orbdir is None:
      orbdir = os.getcwd()
   #
   #
   # sys.exit(-1)
   #
   #

if model.upper() == "RESORB":
   searchdir = orbdir +'/'+'/aux_resorb/'
else:
   searchdir = orbdir +'/'+'/aux_poeorb/'
#
#
if True:
    #
    orbs_S1A = None
    times_S1A = None
    orbs_S1B = None
    times_S1B = None
    #
    #  orbs,times = s1_resorb(in_resorb_dir=orbdir,mission=mission)
    #
    platform = 'S1A'
    orb_poeorb,time_poeorb = pS1.s1_poeorb(in_poeorb_dir=orbdir+'/aux_poeorb/', mission=platform)
    orb_resorb,time_resorb = pS1.s1_resorb(in_resorb_dir=orbdir+'/aux_resorb/', mission=platform)
    #
    #
    orbs_S1A = np.hstack([orb_poeorb,orb_resorb])
    times_S1A = np.vstack([time_poeorb,time_resorb])
    #
    #
    platform = 'S1B'
    orb_poeorb,time_poeorb = pS1.s1_poeorb(in_poeorb_dir=orbdir+'/aux_poeorb/', mission=platform)
    orb_resorb,time_resorb = pS1.s1_resorb(in_resorb_dir=orbdir+'/aux_resorb/', mission=platform)
    #
    #
    orbs_S1B = np.hstack([orb_poeorb,orb_resorb])
    times_S1B = np.vstack([time_poeorb,time_resorb])
    #
    #
    #
    for ind,czip in enumerate(sys.argv):
        #
        if '.zip' in czip and "S1" == czip[0:2]:
            # 
            info = s1zip2info(czip)
            #
            # print(info)
            #
            platform     = info[0]
            #
            print(" Process: now working at %s in %s mode" % (czip,info[2]))
            if info[2].upper() == 'GRDH':
              #
              startTimeOri = info[4]
              stopTimeOri  = info[5]
            else:
              startTimeOri = info[5]
              stopTimeOri  = info[6]
            #
            #
            startTime = datetime.datetime.strptime(startTimeOri,"%Y%m%dT%H%M%S").strftime('%Y-%m-%dT%H:%M:%S.0')
            stopTime  = datetime.datetime.strptime(stopTimeOri,"%Y%m%dT%H%M%S").strftime('%Y-%m-%dT%H:%M:%S.0')
            #
            # print(startTime,stopTime)
            #
            searchdirTMP = searchdir
            # searchdirTMP = searchdir+'/%s/' % platform
            #
            if platform=='S1A':
              orbfile,orbs_S1A,times_S1A = pS1.s1times2orb(startTime+'Z',stopTime+'Z',orbdir=searchdirTMP,model=model.upper(),\
                       mission=platform,orbs=orbs_S1A,times=times_S1A)
              #
              # print(orbfile)
            elif platform=='S1B':
              orbfile,orbs_S1B,times_S1B = pS1.s1times2orb(startTime+'Z',stopTime+'Z',orbdir=searchdirTMP,model=model.upper(),\
                       mission=platform,orbs=orbs_S1B,times=times_S1B)
            else:
              print(" ERR: we have to update here once S1C, S1D are available...")
              sys.exit(-1)
            #
            if update:
                str_update = '-update'
            else:
                str_update = ''
            if source.upper()=='ASF':
               gograb = 'pSAR_grabS1orb.py %s %s -s1_orb %s -model %s -mission %s %s' % \
                    (startTimeOri,stopTimeOri,orbdir,model,platform,str_update)
            else:
               model = model[0:3]
               t1 = pSAR.ts.timeshift(startTimeOri,-1*tshift,fmt="%Y%m%dT%H%M%S",outfmt='%Y-%m-%dT%H:%M:%S')
               t2 = pSAR.ts.timeshift(stopTimeOri,tshift,fmt="%Y%m%dT%H%M%S",outfmt='%Y-%m-%dT%H:%M:%S')
               gograb = 'ESA_s1_get_aux_orb_gnss %s %s %s %s' % (model,t1,t2,platform)
               #
               #
            #
            print(orbfile)
            if 'NULL' in orbfile.upper():
               print(gograb)
               os.system(gograb)
               #
               # orbfile = pGAMMA.gamma_s1times2statevector(startTime+'Z',stopTime+'Z',model=model.upper(),\
               #       mission=platform)
               if platform=='S1A':
                  orbfile,orbs_S1A,times_S1A = pS1.s1times2orb(startTime+'Z',stopTime+'Z',orbdir=searchdirTMP,model=model.upper(),\
                       mission=platform,orbs=orbs_S1A,times=times_S1A,update=True)
                  #
               elif platform=='S1B' :
                  orbfile,orbs_S1B,times_S1B = pS1.s1times2orb(startTime+'Z',stopTime+'Z',orbdir=searchdirTMP,model=model.upper(),\
                       mission=platform,orbs=orbs_S1B,times=times_S1B,update=True)
            else:
               eoffile = os.path.basename(orbfile)
               #
            goflag = True
            #
            if 'NULL' in orbfile:
                goflag = False 
            #
            if iscopy and goflag:
               zipfulldir = os.path.dirname(os.path.abspath(czip))
               orbfilename = os.path.basename(orbfile)
               #
               objorb = os.path.join(zipfulldir,orbfilename)
               if not os.path.exists(objorb):
                  print(objorb)
                  os.system('cp %s %s -f' % (orbfile,objorb))
               #
            if link and goflag:
               zipfulldir = os.path.dirname(os.path.abspath(czip))
               orbfilename = os.path.basename(orbfile)
               #
               objorb = os.path.join(zipfulldir,orbfilename)
               if not os.path.exists(objorb):
                  print(objorb)
                  os.symlink(orbfile,objorb)

