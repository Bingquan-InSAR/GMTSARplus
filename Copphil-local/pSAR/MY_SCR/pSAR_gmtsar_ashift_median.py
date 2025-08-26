#!/usr/bin/env python
#
#
#
import os
import pDATA
import sys
import numpy as np
import matplotlib.pyplot as plt
#
def median_ashift(ashift):
    #
    dim_2 = ashift.shape[1]
    off10 = int(dim_2*0.2)
    #
    for i in range(ashift.shape[0]):
        #
        ashift[i,:] = np.median(ashift[i,off10:-1*off10])
    return ashift
#
if len(sys.argv) < 2:
    helpstr = \
            '''
            %s <in_grd> <out_grd>
            ++++++++++++++++++++++++++++++++++++
            To return median azimuth shifts for each raw...
            
            By some unknown reasons, pixel shifts along azimuth could not be a constant for a raw.
            Particularly, there are some anomalies at the boundaries. In order to avoid these strange
            shifts at boundaries, a median value will be expected to fill in the whole row.
            

            by Wanpeng Feng, @SYSU, Guangzhou, 2020/11/02

            '''
    print(helpstr % sys.argv[0])
    sys.exit(-1)
    #
#
if True:
    #
    azshift_file = sys.argv[1] 
    #
    info,ext,data = pDATA.grd_read(azshift_file)
    data = np.array(data)
    # 
    # print(data.shape,type(data))
    #
    data = median_ashift(data)
    data = np.flipud(data)
    #
    newgrd = sys.argv[2] 
    #
    if newgrd != azshift_file:
       os.system('cp %s %s -f' % (azshift_file,newgrd))
    #
    pDATA.grd_update(newgrd,data)
    #
    #

