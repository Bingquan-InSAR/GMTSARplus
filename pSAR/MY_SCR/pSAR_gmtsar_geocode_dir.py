#!/usr/bin/env python
#
#
import os
import sys
import glob
#
#
if True:
    #
    # geoscript = glob.glob('../*.sh')
    workdir = os.getcwd()
    workroot = os.path.dirname(workdir)
    #
    flag1 = os.path.basename(workroot)
    #
    if not os.path.exists('trans.dat'):
        #
        indat = '../topo/trans.dat'
        if not os.path.exists(indat):
            print(" Err: no trans.dat is found in the folder...")
            sys.exit(-1)
        else:
            os.system('ln -s %s .' % indat)
        #
    print(" Progress: starting geocoding in %s" % os.getcwd())
    #
    #
    #
    if flag1.upper() == 'MERGE':
        geoscript = glob.glob('../proj_ra2ll.info.sh')
    else:
        flag2 = os.path.basename(workroot.split('/%s' % flag1)[0])
        iwNo  = flag2.split('F')[1]
        geoscript = glob.glob('../../../proj_ra2ll_iw%s.info.sh' % iwNo)
        #
    #
    if len(geoscript)>0:
        geoscript = geoscript[0]
    else:
        geoscript = ""
    #
    if not os.path.exists('phasefilt_ll.grd'):
        #
        # check if phasefilt.grd exists in the local folder...
        #
        if not os.path.exists('phasefilt.grd'):
            print(" ERR: cannot find phasefilt.grd !!!!")
            sys.exit(-1)
        #
        goStr = 'GMTSAR_proj_ra2ll.csh trans.dat phasefilt.grd phasefilt_ll.grd %s' % geoscript
        print(" Progress: %s" % goStr)
        os.system(goStr)
    if not os.path.exists('unwrap_ll.grd') and os.path.exists('unwrap.grd'):
        #
        os.system('gmt grdtrend unwrap.grd -N3r -Dunwrap_detrended.grd')
        goStr = 'GMTSAR_proj_ra2ll.csh trans.dat unwrap.grd unwrap_ll.grd %s' % geoscript
        print(" Progress: %s" % goStr)
        os.system(goStr)
    #
    if not os.path.exists('corr_ll.grd'):
        #
        goStr = 'GMTSAR_proj_ra2ll.csh trans.dat corr.grd corr_ll.grd %s' % geoscript
        print(" Progress: %s" % goStr)
        os.system(goStr)
    #
    if os.path.exists('unwrap.bin'):
        os.system('rm unwrap.bin phase.in -f')
    #
