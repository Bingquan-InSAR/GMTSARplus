#!/usr/bin/env python 
###############################################################################
# Sentinel-1 Creodias Query Script
# Created by George on July 19, 2025
# Updated by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose:
#   Query and cluster Sentinel-1 SLC data from the Creodias datahub based on
#   user-defined geometry, orbit direction, and date range, for downstream InSAR
#   processing workflows.
###############################################################################
import argparse
import sys
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from datetime import datetime, date, timedelta
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta   
from cluster_S1 import cluster_s1
from shapely import wkt 
import kml2geojson
import os
import shutil

def monthly_windows(start_iso: str, end_iso: str):
    """
    Yield (window_start, window_end) ISO strings, one per month,
    honouring the exact first/last days supplied by the caller.
    """
    # 1. parse inputs (strip the trailing 'Z' if present)
    start__ = datetime.strptime(start_iso, "%Y%m%d").date()   # → datetime.date(2020, 1, 1)
    end__ = datetime.strptime(end_iso, "%Y%m%d").date()   # → datetime.date(2023, 1, 1)

    start_clean = start__.isoformat()    # "2020-01-01
    end_clean = end__.isoformat()    # "2023-01-01
    
    start = datetime.fromisoformat(start_clean.rstrip("Z"))
    end   = datetime.fromisoformat(end_clean.rstrip("Z"))

    cur_start = start
    while cur_start < end:
        # 2. jump to the first day of the next month, same time = 00:00:00
        next_month = (cur_start.replace(day=1) + relativedelta(months=1))
        #       our chunk ends *one second* before that, OR at the true end
        cur_end = min(end, next_month - timedelta(seconds=1))

        yield (cur_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
               cur_end.strftime("%Y-%m-%dT%H:%M:%SZ"))

        # 3. next loop starts right at next_month
        cur_start = next_month


def s1_query(inputGeom, orbit, firstDate, lastDate):

    """
    inputGeom: input geometry either as a list of the xmin,ymin, xmax, ymax to form a bbox or a geometry as a geojson 
    firstDate: first date of the collection 
    lastDate: last date of the collection
    """
    
    #-----------------------------------------------------------------
    ###time frame for query

    data_collection = "SENTINEL-1"
    prod_type='SLC'
    orbit = orbit

    geom_filtr = inputGeom
    print(inputGeom)
    
    
    poly = wkt.loads(geom_filtr)
    
    # 2.  Wrap it in a GeoDataFrame (assume lon/lat WGS 84 → EPSG:4326)
    geom_filtr_gdf = gpd.GeoDataFrame({"geometry": [poly]}, crs="EPSG:4326")
    ###empty df for export
    df_4export = pd.DataFrame(columns =['S3Path','GeoFootprint', 'Online'])


    print(f"Sentinel 1 data will be searched for the dates between {firstDate} and {lastDate}")
    print(f"AOI of the desired scene to be downloaded will be delimited by: West:{geom_filtr_gdf.bounds.minx[0]} East:{geom_filtr_gdf.bounds.maxx[0]} North:{geom_filtr_gdf.bounds.maxy[0]} South:{geom_filtr_gdf.bounds.miny[0]}")
    #---------------------------------------------------------------
    for window_start, window_end in monthly_windows(firstDate, lastDate):
        json_ = requests.get(f"https://datahub.creodias.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{prod_type}') and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'orbitDirection' and att/OData.CSC.StringAttribute/Value eq '{orbit}') and OData.CSC.Intersects(area=geography'SRID=4326;{geom_filtr}') and ContentDate/Start gt {window_start} and ContentDate/Start lt {window_end}&$count=True&$top=1000").json() 

        
        dataFrame_response = pd.DataFrame.from_dict(json_["value"])    
        
        if dataFrame_response.empty:
                df_4export = pd.concat([df_4export, dataFrame_response]).reset_index(drop=True)
        else:
            df_4export = pd.concat([df_4export, dataFrame_response[["S3Path", "GeoFootprint", 'Online']]]).reset_index(drop=True)
                    
    total_data_found = len(df_4export)
    print(f"A total of {total_data_found} Sentinel-1 scenes were found for the corresponding timeframe and geometry for the {orbit} orbit.")

    try:
        if df_4export.empty:
            raise ValueError("Error: Due to various reasons returned DataFrame is empty. Retry with other search Criteria.")
    
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    print("Some data samples are here: \n", df_4export["S3Path"].head())
        
    df_4export_final2, dict_4export_final2 = cluster_s1(df_4export)

    print(dict_4export_final2)
    print("clustering_ended")
    return df_4export_final2, dict_4export_final2

def input_geom(value: str):
    """
    Return ('bbox', [xmin, ymin, xmax, ymax]) or ('geojson', path)
    Raise argparse.ArgumentTypeError if format is bogus.
    """
    # Try bbox first (4 floats separated by space or commas)
    stripped = value.replace(',', ' ')
    parts = stripped.split()
    
    if len(parts) == 4:
        try:
            nums = [float(p) for p in parts]
            
            xmin, ymin, xmax, ymax = nums
        
            poly = box(xmin, ymin, xmax, ymax)
        
            geom = gpd.GeoDataFrame({"geometry": [poly]}, crs="EPSG:4326")

            ft = geom.geometry.to_wkt()[0]
            return ft
        
        except ValueError:
            pass     
    # Otherwise assume it's a GeoJSON path; optional quick check
    
    if value.endswith('.geojson'):
        geom=gpd.read_file(value)
        
        geom = geom.to_crs('epsg:4326')
        
        ft = geom.geometry.to_wkt()[0]
        
        return ft
    if value.endswith('.kml'):
        
        kml_json = kml2geojson.main.convert(value)

        gdf = gpd.GeoDataFrame.from_features(kml_json[0]["features"])
        geom = gdf.set_crs('epsg:4326')
        
        ft = geom.geometry.to_wkt()[0]
        return ft
    
    raise argparse.ArgumentTypeError(
        f"'{value}' is neither 4 numbers nor a GeoJSON or KML file")

def main():
    
    # Step 2: Create the argument parser
    parser = argparse.ArgumentParser(description="Simple script to query the creodias datahub to get S1_SLC*.SAFE data to be used in GMS processing ")
    
    # Step 3: Add arguments to the parser

    parser.add_argument('-g', '--inputGeom', type=input_geom, required = True, help='Geometry structure that will be used for spatial query of the  Copernicus database. either in bbox format: xmin, ymin, xmax, ymax or as a geojson file.')
    
    parser.add_argument('-o', '--orbit', type=str, metavar='',help='Orbit type, ASCENDING or DESCENDING.')

    parser.add_argument('-f', '--firstDate', type=str, metavar='',help='First date for the temporal query. Format of date should be YYYYMMDD, like 20200101')
    parser.add_argument('-l', '--lastDate', type=str, metavar='',help='Last date of the temporal query.Format of date should be YYYYMMDD, like 20230101')
    
    # Step 4: Parse the arguments
    args = parser.parse_args()
    
    # Step 5: Pass the arguments to your function
    none,dataset = s1_query(args.inputGeom, args.orbit, args.firstDate, args.lastDate)

    target_dir = args.orbit
    roi_txt = f"{target_dir}_roi"
    os.makedirs(target_dir, exist_ok=True)
    with open(roi_txt, 'w') as f:
        for cluster_path, roi in dataset.items():
            cluster_name = os.path.dirname(os.path.dirname(cluster_path))
            os.system(f'mv {cluster_name} {target_dir}')

            line = ','.join(str(x) for x in roi)
            f.write(line + '\n')

if __name__ == "__main__":
    main()
