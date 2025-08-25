#!/usr/bin/env python 
###############################################################################
# Sentinel-1 Clustering and ROI Extraction Script
# Created by George on July 19, 2025
# Updated by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose:
#   Perform spatial clustering of Sentinel-1 SLC scenes using DBSCAN,
#   extract representative ROIs, and generate symbolic links for
#   grouped scenes, supporting downstream InSAR processing workflows.
###############################################################################
import ast
import os
import pandas as pd
import numpy as np
import sys

from pathlib import Path
import geopandas as gpd
from pyproj import CRS
import json

from sklearn.cluster import DBSCAN  
import matplotlib.pyplot as plt
from shapely.geometry import shape 

def S1_linker (dataframe):

    paths = []
    rois = []
    
    
    files_by_cluster = dataframe.explode("S3Path", ignore_index=True)
    
    for cluster, sub in files_by_cluster.groupby('cluster_id'):
        dst = f'./dataCluster_{cluster}/safe/'
        
        isExist = os.path.exists(dst)
        if not isExist:
            os.makedirs(dst)
        
        print(f'Data for cluster {cluster} is being symlinked to {dst}')
        
        for file in sub["S3Path"]:
            os.symlink(file, os.path.join(dst+os.path.basename(file)))
        
        paths.append(dst)
        
    end_dict = dict(zip(paths, list(dataframe["Roi"])))
    
    return end_dict

def as_geometry(v):
    """Accept either dict or str and return a shapely geometry."""
    if isinstance(v, dict):
        return shape(v)
    else:                 
        return shape(json.loads(v))

def LM_scenes_intersection(inputScenes_dataframe):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(script_dir, 'Philippines_LM.geojson')
    inputMask=gpd.read_file(geojson_path )
    ea_crs = CRS.from_epsg(6933)                  
    gdf_results = inputScenes_dataframe.to_crs(ea_crs)
    gdf_mask    = inputMask.to_crs(ea_crs)

    mask_geom = gdf_mask.geometry.unary_union 
    
    # total area of every result feature
    gdf_results["areaTotal_Km2"] = gdf_results.geometry.area/1000000

    # area that lies inside the mask
    gdf_results["areaInLand_Km2"] = (gdf_results.geometry.intersection(mask_geom)).area/1000000

    # percentage; multiply by 100 for human-friendly numbers
    gdf_results["%Land"] = (gdf_results["areaInLand_Km2"] / gdf_results["areaTotal_Km2"]).fillna(0).round(4) * 100

    return gdf_results

    
def cluster_s1(dataframe):

    dataframe["geometry"] = dataframe["GeoFootprint"].apply(as_geometry)
    
    gdf_init = gpd.GeoDataFrame(dataframe, geometry="geometry", crs="EPSG:4326")

    ##reproject to metric epsg
    gdf_init_reproj = gdf_init.to_crs(3857)
    
    # 2.  Build an (N, 2) array of centroid coords
    gdf_init_reproj["centroid"] = gdf_init_reproj.geometry.centroid
    coords = np.vstack([gdf_init_reproj.centroid.x, gdf_init_reproj.centroid.y]).T     # shape (N, 2)

    
    """
    Cluster the centroids --------------------------------------------------
        • eps  : max distance (metres) two centroids can be apart to belong
                 to the same cluster.
        • min_samples=1 makes every polygon belong to *some* cluster
    
     Tune `eps` → try the average spacing you expect between polygons
    """
    
    db = DBSCAN(eps=4000, min_samples=1, metric="euclidean").fit(coords)
    gdf_init_reproj["cluster_id"] = db.labels_

    #### data filtering 
    gdf_filter=gdf_init_reproj[['geometry','cluster_id', 'centroid','S3Path']]

    ### copy and set scenes names
    gdf_filter_copy = gdf_filter.copy()
    gdf_filter_copy.loc[:, "sceneName"] = gdf_filter_copy["S3Path"].apply(lambda p: Path(p).stem)

    ### extract the time series and set aquistion date
    time_series = gdf_filter_copy["sceneName"].str.extract(r"_(\d{8}T\d{6})_")[0]
    gdf_filter_copy["acq_time"] = pd.to_datetime(time_series, format="%Y%m%dT%H%M%S")
    gdf_filter_copy_2 = gdf_filter_copy.sort_values("acq_time").reset_index(drop=True)


    ### compute area, get the idx for each max area and get max extent of each geometry
    gdf_filter_copy_2["area_m2"] = gdf_filter_copy_2.geometry.area
    idx_max = gdf_filter_copy_2.groupby("cluster_id")["area_m2"].idxmax()


    ### get scenes list and group them by cluster ids, after that dissolve all the geometry by the cluster id 
    cluster_extent = gdf_filter_copy_2.dissolve(by="cluster_id", aggfunc=({"sceneName": list, "S3Path":list}), as_index=False)


    ### get the final clustered files for export
    clustered_files = cluster_extent.sort_values(by="sceneName",key=lambda col: col.apply(len),ascending=True,).reset_index().drop(columns="index")
    clustered_files["scene_count"] = clustered_files["sceneName"].apply(len)

    print(clustered_files)
    
    LM_intersections = LM_scenes_intersection(clustered_files)
    
    ### final filter
    #filtered_scenes = LM_intersections[(LM_intersections['%Land'] > 5) & (LM_intersections['scene_count'] > 10)].reset_index()
    filtered_scenes = LM_intersections[(LM_intersections['scene_count'] > 4)].reset_index()
    try:
        if filtered_scenes.empty:
            raise ValueError("Error: Due to low number of scenes, certain clusters couldnt be established by the algorithm. Retry with other search criteria, usually a wider timeframe!!!")
    
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    filtered_scenes = filtered_scenes.to_crs(4326)

    print(filtered_scenes)
    filtered_scenes = filtered_scenes.assign(Roi=filtered_scenes.geometry.bounds.to_numpy()[:, [0,2,1,3]].tolist())    
    end_dict = S1_linker (filtered_scenes)
    
    return filtered_scenes, end_dict
