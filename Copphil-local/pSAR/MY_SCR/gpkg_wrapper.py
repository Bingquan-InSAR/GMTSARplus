#!/usr/bin/env python
###############################################################################
# Ground Motion Product Export and Upload Script
# Created by George on July 19, 2025
# Updated by Bingquan Li and Ling Chang on August 19, 2025
#
# Purpose:
#   Generate standardized GPKG/GeoJSON products and XML metadata from Sentinel-1
#   deformation CSV results, reproject to target CRS, and upload to S3 cloud storage.
###############################################################################
import os
import boto3
import argparse
import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime

import secrets
import string


def extract_first_last_dates(s1_products):
    """
    Extract the first and last acquisition dates from a list of Sentinel-1 SLC product names.
    
    Parameters:
    s1_products (list): List of Sentinel-1 SLC product names
    
    Returns:
    tuple: (first_date, last_date) in 'dd/mm/yyyy' format
    """
    try:
        # Extract acquisition start dates from file names
        dates = []
        for product in s1_products:
            date_str = product.split('_')[5][:8]  
            date = datetime.strptime(date_str, '%Y%m%d')
            dates.append(date)
        
        # Sort dates to find first and last
        if not dates:
            return None, None
        
        dates.sort()
        firstDate = dates[0].strftime('%d/%m/%Y')
        lastDate = dates[-1].strftime('%d/%m/%Y')

        firstYear = dates[0].year
        lastYear = dates[-1].year
        
        return firstDate, firstYear, lastDate, lastYear
    
    except Exception as e:
        print(f"Error processing dates: {e}")
        return None, None


def create_metadata_xml(sbas_result, meta, projection):

    # Read meta
    df_meta = pd.read_csv(meta, delimiter=":")

    # Get S1 scenes from dataframe and create list
    s1_scenes = df_meta[df_meta['VARIABLE']=='LIST_S1']['VALUE'].iloc[0]
    replacements = str.maketrans({"[": "", "]" : "", "'":""})
    s1_scenes_good = s1_scenes.translate(replacements).split(',')
    
    # Get first-last date
    firstDate, firstYear, lastDate, lastYear = extract_first_last_dates (s1_scenes_good)
    
    # Get number of inputs
    NI = len(s1_scenes_good)
    
    
    # Get Relative orbit information
    orbit =[]
    for scene in s1_scenes_good: 
        satellite = scene.split('_')[0]
        orbit_str = scene.split('_')[-3]
        
        
        if satellite == 'S1A':
            orbitA = ((int(orbit_str) - 73) %175)+1
            orbit.append(orbitA)
        
        if satellite == 'S1B':
            orbitB = ((int(orbit_str) - 27) %175)+1
            orbit.append(orbitB)
    
    s1_orbit = set(orbit)

    s1_orbitXML = None if len(s1_orbit) == 0 else s1_orbit.pop()
    
    # Get Orbit and Incidence Angle
    Orbit_Angle = sbas_result["Heading"].iloc[0]
    Incidence_Angle = sbas_result["Incidence"].iloc[0]


    #Generate uniqueID with 8 alphanumeirc data
    length = 8
    DeliverableID = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

    # Info from meta txt file
    Pass = str(df_meta[df_meta['VARIABLE']=='PASS']['VALUE'].iloc[0])
    APS = str(df_meta[df_meta['VARIABLE']=='APSCorrection']['VALUE'].iloc[0])
    DEM = str(df_meta[df_meta['VARIABLE']=='DEM']['VALUE'].iloc[0])
    
    # Create the root
    root = ET.Element("ProductMetadata")
    # Add elements
    ET.SubElement(root, "ProductLevel").text = "P1.1 LOS"
    # Parse elements from the dataframe or statict to the XML
    ET.SubElement(root, "Pass").text = Pass
    ET.SubElement(root, "DeliverableID").text = str(DeliverableID)
    ET.SubElement(root, "ProcessorVersion").text = "1.0.0v"
    ET.SubElement(root, "ProcessingDate").text = str(datetime.now())
    ET.SubElement(root, "APSCorrection").text = APS
    #ET.SubElement(root, "ReferencePoint").text = str(df_meta[df_meta['VARIABLE']=='REFERENCE_POINT']['VALUE'].iloc[0])
    ET.SubElement(root, "EPSG").text = str (projection)
    ET.SubElement(root, "DEM").text = DEM
    ET.SubElement(root, "Constellation").text = "Sentinel-1"
    ET.SubElement(root, "RelativeOrbitSentinel-1").text = str(s1_orbitXML)
    
    # Incidence Angle and Orbit Angle
    los_vector = ET.SubElement(root, "LOSVector")
    product = ET.SubElement(los_vector, "IncidenceAngle")
    product.text = str(Incidence_Angle)
    product = ET.SubElement(los_vector, "OrbitAngle")
    product.text = str(Orbit_Angle)

    # First and last acquisition dates
    ET.SubElement(root, "NI").text = str(NI)
    ET.SubElement(root, "FirstAcquisition").text = str(firstDate)
    ET.SubElement(root, "LastAcquisition").text = str(lastDate)
    
    # Parse S1 list
    products = ET.SubElement(root, "Sentinel1InputProducts")
    
    # Add products to XML
    if s1_scenes_good:
        for product in s1_scenes_good:
            if product.endswith('.SAFE'):
                product_split = product.split('.SAFE')[0]
                prod_elem = ET.SubElement(products, "Product")
                prod_elem.text = product_split
            
            else:
                prod_elem = ET.SubElement(products, "Product")
                prod_elem.text = product
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if Pass == 'DESCENDING':
        master_grid_path = os.path.join(script_dir, 'COP_MASTER_GRID_DESCENDING.geojson')
        master_grid = gpd.read_file(master_grid_path)
        joined_grid = sbas_result.sjoin(master_grid)

    
    elif Pass == 'ASCENDING': 
        master_grid_path = os.path.join(script_dir, 'COP_MASTER_GRID_ASCENDING.geojson')
        master_grid = gpd.read_file(master_grid_path)
        joined_grid = sbas_result.sjoin(master_grid)
    
    else:
        raise ValueError("Not a valid orbit pass. Meta file may be not incorrect!")
    
    Path = joined_grid["Path"].value_counts().idxmax()
    Frame = joined_grid["Frame"].value_counts().idxmax()

    export_name = f'CPH_GMS_P1.1_{s1_orbitXML}_P{Path}_F{Frame}_{Pass}_{firstYear}_{lastYear}_{DeliverableID}'
    
    # Convert to pretty-printed XML string
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Save to file
    with open(f"/tmp/{export_name}.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    return export_name

def read_export(input_path, extension, projection):
    """
    Reads CSV files, converts to GeoDataFrames, reprojects, and uploads to S3.
    Upload path: s3://results/results/GroundMotion/<user_id>/<order_id>/<filename>
    """
    user_id = os.getenv('USER_ID')
    order_id = os.getenv('ORDER_ID')
    bucket_name = "results"
    s3_endpoint = "https://s3.waw3-1.cloudferro.com"

    if not user_id or not order_id:
        raise EnvironmentError("Environment variables USER_ID and ORDER_ID must be defined.")
    
    #boto3 connection
    s3 = boto3.client('s3', endpoint_url=s3_endpoint)

    csv_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.csv')]
    meta_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.txt')]

    csv_files.sort()
    meta_files.sort()

    
    if not csv_files:
        print("No CSV files found.")
        return

    for file_path, meta_file_path in tqdm(zip(csv_files, meta_files), desc="Processing and uploading"):
        
        try:
            df = pd.read_csv(file_path)

            if 'LAT' not in df.columns or 'LON' not in df.columns:
                print(f"Skipping {file_path}: Missing 'LAT' or 'LON' columns.")
                continue
            
            # read points as GDF
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LON, df.LAT), crs='EPSG:4326')
            gdf = gdf.to_crs(projection)

            # get the export name from the create_meta_xml function
            gpkg_export_name = create_metadata_xml(sbas_result = gdf, meta=meta_file_path,  projection=projection)
            
            #base_name = Path(file_path).stem
            #filename = f"{base_name}{extension}"
            local_tmp = f"/tmp/{gpkg_export_name}{extension}"
            s3_key = f"GroundMotion/{user_id}/{order_id}/{gpkg_export_name}{extension}"

            s3_key_xml = f"GroundMotion/{user_id}/{order_id}/{gpkg_export_name}.xml"
            if extension == ".gpkg":
                gdf.to_file(local_tmp, driver="GPKG", index=False)
            
            elif extension == ".geojson":
                gdf.to_file(local_tmp, driver="GeoJSON", index=False)
            
            else:
                raise ValueError("Unsupported extension. Use .gpkg or .geojson")

            s3.upload_file(local_tmp, bucket_name, s3_key)
            s3.upload_file(f"/tmp/{gpkg_export_name}.xml", bucket_name, s3_key_xml)

            print(f"Uploaded: s3://{bucket_name}/{s3_key}")
            print(f"Uploaded XML: s3://{bucket_name}/{s3_key_xml}")

            # delete all files from /tmp, for multiple extension files
            local_tmp = "/tmp"
            for filename in os.listdir(local_tmp):
                final_export = os.path.join(local_tmp, filename)
                
                # check if file is dir
                if os.path.isfile(final_export):
                    if final_export.endswith((".gpkg", ".geojson", ".xml")):
                        os.remove(final_export) 
                        print(f"Deleted file: {filename}")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert CSV to GPKG/GeoJSON and upload to S3 GroundMotion folder.")

    parser.add_argument('--input_path', '-i', type=str, required=True, help='Path to directory containing .csv files')
    parser.add_argument('--extension', '-e', type=str, default='.gpkg', choices=['.gpkg', '.geojson'], help='Export format')
    parser.add_argument('--projection', '-p', type=str, default='EPSG:4326', help='Output projection (default EPSG:4326)')

    args = parser.parse_args()

    read_export(args.input_path, args.extension, args.projection)

if __name__ == "__main__":
    main()
