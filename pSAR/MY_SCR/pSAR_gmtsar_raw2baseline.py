#!/usr/bin/env python
#
#
import shutil
import os
import sys
import glob
import subprocess
import pSAR
#
#
master = None
if len(sys.argv)>1:
    master = sys.argv[1]
#
sr = '2*.PRM'
for i,key in enumerate(sys.argv):
    if key == '-sr':
        sr = sys.argv[i+1]
#
outbase = 'baseline_table.dat'
#
if True:
    fid = open(outbase,'w')
    #
    PRMs = glob.glob(sr)
    outk = 0
    if master is not None:
        for i,cprm in enumerate(PRMs):
            if master in cprm:
                outk = i
            #
        #
        if outk != 0:
            tmpPRM = PRMs[0]
            PRMs[0] = PRMs[outk]
            PRMs[outk] = tmpPRM
    for i in range(len(PRMs)):
        #
        m_prm = PRMs[0]
        s_prm = PRMs[i]
        m_date = int(m_prm.split('.PRM')[0])
        s_date = int(s_prm.split('.PRM')[0])
        #
        goStr = 'baseline_table.csh %s %s' % (m_prm, s_prm)
        #
        print(' Progress: %s' % goStr)
        output = subprocess.Popen(goStr,stdout=subprocess.PIPE,\
                                     stderr=subprocess.PIPE,shell=True)
        flag = output.wait()
        prints,errors = output.communicate()
        #
        prints = pSAR.util.bytestoutf8(prints)
        print(prints)
        #
        fid.write('%s' % prints)
        
    #
    fid.close()
    #
    # copy the baseline file to above folder...
    # shutil.copy(outbase,'../%s' % outbase)
    # shutil is not stable in practic, and now I turn to "cp"
    # by FWP, @SYSU, 2020/04/25
    os.system('cp %s ../%s -f ' % (outbase,outbase))
    #

        
