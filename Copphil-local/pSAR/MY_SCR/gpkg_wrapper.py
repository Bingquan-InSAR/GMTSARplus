#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# Ground Motion Product Export Script (simplified)
# Original: 2025-07-19 (George) | Updated: 2025-08-19 (Bingquan Li & Ling Chang)
# This version: 2025-08-31 (me) — per user request:
#   - Do NOT use COP_MASTER_GRID_ASCENDING/DESCENDING.geojson
#   - Do NOT use /tmp
#   - Outputs must be output.gpkg and output.xml in the current directory
###############################################################################

import os
import argparse
import pandas as pd
import geopandas as gpd
from pathlib import Path
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from tqdm import tqdm
import secrets
import string


def extract_first_last_dates(s1_products):
    """
    Extract first and last acquisition dates from a list of S1 product names.

    Expected name parts like: S1A_IW_SLC__1SDV_20240101T012345_...
    We take the 6th token (index 5) then first 8 chars as YYYYMMDD.

    Returns:
        (firstDate, firstYear, lastDate, lastYear) with dd/mm/YYYY strings, and years as int.
        On failure or empty list, all returned as None.
    """
    try:
        dates = []
        for product in s1_products:
            parts = product.split('_')
            if len(parts) >= 6:
                date_str = parts[5][:8]
                date = datetime.strptime(date_str, '%Y%m%d')
                dates.append(date)
        if not dates:
            return None, None, None, None
        dates.sort()
        firstDate = dates[0].strftime('%d/%m/%Y')
        lastDate = dates[-1].strftime('%d/%m/%Y')
        firstYear = dates[0].year
        lastYear = dates[-1].year
        return firstDate, firstYear, lastDate, lastYear
    except Exception:
        return None, None, None, None


def safe_get(df_meta, key, default="NA"):
    """Get meta value by VARIABLE==key from a df with columns ['VARIABLE','VALUE']."""
    try:
        val = df_meta[df_meta['VARIABLE'] == key]['VALUE'].iloc[0]
        return str(val).strip()
    except Exception:
        return default


def normalize_list_s1(list_text):
    """
    Normalize LIST_S1 string like: "['A.SAFE','B.SAFE']" -> ['A.SAFE','B.SAFE']
    """
    s = str(list_text)
    reps = str.maketrans({"[": "", "]": "", "'": ""})
    cleaned = s.translate(reps)
    # split by comma, strip whitespace, drop empties
    items = [x.strip() for x in cleaned.split(',') if x.strip()]
    return items


def relative_orbit_from_name(scene_name):
    """
    Compute Sentinel-1 relative orbit from product name.
    For S1A: ((abs_orbit - 73) % 175) + 1
    For S1B: ((abs_orbit - 27) % 175) + 1
    Returns int or None.
    """
    try:
        parts = scene_name.split('_')
        if len(parts) < 3:
            return None
        sat = parts[0]  # e.g., 'S1A' or 'S1B'
        # absolute orbit often is third from the end; original code used [-3]
        abs_orbit_str = parts[-3]
        abs_orbit = int(abs_orbit_str)
        if sat == 'S1A':
            return ((abs_orbit - 73) % 175) + 1
        elif sat == 'S1B':
            return ((abs_orbit - 27) % 175) + 1
        else:
            return None
    except Exception:
        return None


def create_metadata_xml(gdf, meta_path, projection, xml_filename="output.xml"):
    """
    Create output.xml in current directory using:
      - LIST_S1 / PASS / APSCorrection / DEM from meta (if exists)
      - NI, First/Last acquisition from LIST_S1
      - RelativeOrbit from LIST_S1
      - Incidence/Heading from gdf columns if present
    """
    # meta
    has_meta = meta_path is not None and Path(meta_path).is_file()
    if has_meta:
        # Expect "VARIABLE:VALUE" per line
        df_meta = pd.read_csv(meta_path, delimiter=":", names=["VARIABLE", "VALUE"], engine="python")
        # Strip whitespace from columns
        df_meta["VARIABLE"] = df_meta["VARIABLE"].astype(str).str.strip()
        df_meta["VALUE"] = df_meta["VALUE"].astype(str).str.strip()
        list_s1_text = safe_get(df_meta, "LIST_S1", default="")
        s1_list = normalize_list_s1(list_s1_text)
        Pass = safe_get(df_meta, "PASS", default="NA")
        APS = safe_get(df_meta, "APSCorrection", default="NA")
        DEM = safe_get(df_meta, "DEM", default="NA")
    else:
        s1_list = []
        Pass = "NA"
        APS = "NA"
        DEM = "NA"

    # dates & NI
    firstDate, firstYear, lastDate, lastYear = extract_first_last_dates(s1_list)
    NI = len(s1_list)

    # relative orbit: take first valid
    rel_orbits = []
    for scene in s1_list:
        ro = relative_orbit_from_name(scene)
        if ro is not None:
            rel_orbits.append(ro)
    rel_orbit = rel_orbits[0] if rel_orbits else None

    # Incidence/Heading from gdf
    def col_or_na(col):
        try:
            return str(gdf[col].iloc[0])
        except Exception:
            return "NA"

    Incidence_Angle = col_or_na("Incidence")
    Orbit_Angle = col_or_na("Heading")

    # unique deliverable id
    DeliverableID = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

    # Build XML
    root = ET.Element("ProductMetadata")
    ET.SubElement(root, "ProductLevel").text = "P1.1 LOS"
    ET.SubElement(root, "Pass").text = str(Pass)
    ET.SubElement(root, "DeliverableID").text = str(DeliverableID)
    ET.SubElement(root, "ProcessorVersion").text = "1.0.0"
    ET.SubElement(root, "ProcessingDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ET.SubElement(root, "APSCorrection").text = str(APS)
    ET.SubElement(root, "EPSG").text = str(projection)
    ET.SubElement(root, "DEM").text = str(DEM)
    ET.SubElement(root, "Constellation").text = "Sentinel-1"
    ET.SubElement(root, "RelativeOrbitSentinel-1").text = "" if rel_orbit is None else str(rel_orbit)

    los_vector = ET.SubElement(root, "LOSVector")
    ET.SubElement(los_vector, "IncidenceAngle").text = str(Incidence_Angle)
    ET.SubElement(los_vector, "OrbitAngle").text = str(Orbit_Angle)

    ET.SubElement(root, "NI").text = str(NI if NI else 0)
    ET.SubElement(root, "FirstAcquisition").text = "" if firstDate is None else str(firstDate)
    ET.SubElement(root, "LastAcquisition").text = "" if lastDate is None else str(lastDate)

    products = ET.SubElement(root, "Sentinel1InputProducts")
    for product in s1_list:
        elem = ET.SubElement(products, "Product")
        elem.text = product.split('.SAFE')[0] if product.endswith('.SAFE') else product

    # Pretty print XML
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    with open(xml_filename, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))


def read_export(input_path, projection):
    """
    Read all CSV under input_path, concatenate to one GeoDataFrame,
    reproject to `projection`, and write to output.gpkg in current dir.
    Also write output.xml using first found .txt meta (if any).
    """
    input_path = Path(input_path)
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_path}")

    csv_files = sorted([p for p in input_path.iterdir() if p.suffix.lower() == ".csv"])
    meta_files = sorted([p for p in input_path.iterdir() if p.suffix.lower() == ".txt"])

    if not csv_files:
        print("No CSV files found under input_path.")
        return

    frames = []
    for fp in tqdm(csv_files, desc="Reading CSV"):
        try:
            df = pd.read_csv(fp)
            if 'LAT' not in df.columns or 'LON' not in df.columns:
                print(f"Skipping {fp.name}: missing LAT/LON.")
                continue
            frames.append(df)
        except Exception as e:
            print(f"Error reading {fp.name}: {e}")

    if not frames:
        print("No valid CSVs with LAT/LON found.")
        return

    df_all = pd.concat(frames, ignore_index=True)
    gdf = gpd.GeoDataFrame(df_all, geometry=gpd.points_from_xy(df_all['LON'], df_all['LAT']), crs="EPSG:4326")
    try:
        gdf = gdf.to_crs(projection)
    except Exception as e:
        print(f"Failed to reproject to {projection}: {e}")
        print("Falling back to EPSG:4326.")
        gdf = gdf.to_crs("EPSG:4326")

    # Write GPKG
    out_gpkg = "output.gpkg"
    gdf.to_file(out_gpkg, driver="GPKG", index=False)
    print(f"Wrote {out_gpkg} in {Path.cwd()}")

    # XML (use first meta if exists)
    meta_path = meta_files[0] if meta_files else None
    create_metadata_xml(gdf, meta_path, projection, xml_filename="output.xml")
    print(f"Wrote output.xml in {Path.cwd()}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge CSVs to GPKG and write XML metadata (output.gpkg / output.xml in current dir)."
    )
    parser.add_argument(
        "--input_path", "-i", type=str, required=True,
        help="Directory containing .csv (and optional .txt meta)."
    )
    parser.add_argument(
        "--projection", "-p", type=str, default="EPSG:4326",
        help="Output projection (default: EPSG:4326)."
    )
    args = parser.parse_args()
    read_export(args.input_path, args.projection)


if __name__ == "__main__":
    main()
