#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# Ground Motion Product Export Script (single-CSV + meta-txt)
# Updated: 2025-12-28 (Bingquan Li)
#
# What it does:
#   - Read ONE CSV (default: ./output.csv) containing at least LON, LAT columns
#   - Write output.gpkg in current directory
#   - Read ONE meta file (default: ./output.txt) in VARIABLE:VALUE format
#   - Write output.xml in current directory
#
# Meta keys used:
#   - APSCorrection
#   - DEM
#   - LIST_S1
#
# Note:
#   - PASS is NOT used (and will not be written to XML)
###############################################################################

import argparse
import secrets
import string
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd
import geopandas as gpd


def extract_first_last_dates(s1_products):
    """
    Extract first and last acquisition dates from a list of S1 product names.

    Expected name parts like: S1A_IW_SLC__1SSV_20240111T103424_20240111T103427_...
    We take the 6th token (index 5) then first 8 chars as YYYYMMDD.

    Returns:
        (firstDate, firstYear, lastDate, lastYear) with dd/mm/YYYY strings, and years as int.
        On failure or empty list, all returned as None.
    """
    try:
        dates = []
        for product in s1_products:
            parts = product.split("_")
            if len(parts) >= 6:
                date_str = parts[5][:8]
                date = datetime.strptime(date_str, "%Y%m%d")
                dates.append(date)
        if not dates:
            return None, None, None, None
        dates.sort()
        firstDate = dates[0].strftime("%d/%m/%Y")
        lastDate = dates[-1].strftime("%d/%m/%Y")
        firstYear = dates[0].year
        lastYear = dates[-1].year
        return firstDate, firstYear, lastDate, lastYear
    except Exception:
        return None, None, None, None


def read_meta_file(meta_path: Path):
    """
    Read VARIABLE:VALUE meta file into a dict.
    Skips empty lines and the header line 'VARIABLE:VALUE' if present.
    Uses split(':', 1) so values can contain additional ':' safely.
    """
    meta = {}
    with meta_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.lower() == "variable:value":
                continue
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def normalize_list_s1(list_text):
    """
    Normalize LIST_S1 string like:
      "[A.SAFE,B.SAFE]" or "['A.SAFE','B.SAFE']"
    into:
      ['A.SAFE','B.SAFE']
    """
    s = str(list_text).strip()
    reps = str.maketrans({"[": "", "]": "", "'": "", '"': ""})
    cleaned = s.translate(reps)
    items = [x.strip() for x in cleaned.split(",") if x.strip()]
    return items


def relative_orbit_from_name(scene_name):
    """
    Compute Sentinel-1 relative orbit from product name.
    For S1A: ((abs_orbit - 73) % 175) + 1
    For S1B: ((abs_orbit - 27) % 175) + 1
    Returns int or None.

    Assumes absolute orbit is the third token from the end ([-3]), e.g.:
    ..._052058_064A9C_CD97.SAFE -> abs_orbit = 052058
    """
    try:
        parts = scene_name.split("_")
        if len(parts) < 3:
            return None
        sat = parts[0]  # 'S1A' or 'S1B'
        abs_orbit_str = parts[-3]
        abs_orbit = int(abs_orbit_str)

        if sat == "S1A":
            return ((abs_orbit - 73) % 175) + 1
        if sat == "S1B":
            return ((abs_orbit - 27) % 175) + 1
        return None
    except Exception:
        return None


def create_metadata_xml(gdf, meta_path, projection, xml_filename="output.xml"):
    """
    Create output.xml in current directory using:
      - LIST_S1 / APSCorrection / DEM from meta
      - NI, First/Last acquisition from LIST_S1
      - RelativeOrbit from LIST_S1
      - Incidence/Heading from gdf columns if present
    """
    # Defaults
    s1_list = []
    APS = "NA"
    DEM = "NA"

    # Read meta if provided
    if meta_path is not None and Path(meta_path).is_file():
        meta = read_meta_file(Path(meta_path))
        APS = meta.get("APSCorrection", "NA")
        DEM = meta.get("DEM", "NA")

        list_s1_text = meta.get("LIST_S1", "")
        if list_s1_text:
            s1_list = normalize_list_s1(list_s1_text)

    # dates & NI
    firstDate, _, lastDate, _ = extract_first_last_dates(s1_list)
    NI = len(s1_list)

    # relative orbit: take first valid
    rel_orbit = None
    for scene in s1_list:
        ro = relative_orbit_from_name(scene)
        if ro is not None:
            rel_orbit = ro
            break

    # Incidence/Heading from gdf
    def col_or_na(col):
        try:
            v = gdf[col].iloc[0]
            return "NA" if pd.isna(v) else str(v)
        except Exception:
            return "NA"

    incidence_angle = col_or_na("Incidence")
    orbit_angle = col_or_na("Heading")

    # unique deliverable id
    deliverable_id = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(8)
    )

    # Build XML
    root = ET.Element("ProductMetadata")
    ET.SubElement(root, "ProductLevel").text = "P1.1 LOS"
    ET.SubElement(root, "DeliverableID").text = str(deliverable_id)
    ET.SubElement(root, "ProcessorVersion").text = "1.0.0"
    ET.SubElement(root, "ProcessingDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ET.SubElement(root, "APSCorrection").text = str(APS)
    ET.SubElement(root, "EPSG").text = str(projection)
    ET.SubElement(root, "DEM").text = str(DEM)
    ET.SubElement(root, "Constellation").text = "Sentinel-1"
    ET.SubElement(root, "RelativeOrbitSentinel-1").text = "" if rel_orbit is None else str(rel_orbit)

    los_vector = ET.SubElement(root, "LOSVector")
    ET.SubElement(los_vector, "IncidenceAngle").text = str(incidence_angle)
    ET.SubElement(los_vector, "OrbitAngle").text = str(orbit_angle)

    ET.SubElement(root, "NI").text = str(NI if NI else 0)
    ET.SubElement(root, "FirstAcquisition").text = "" if firstDate is None else str(firstDate)
    ET.SubElement(root, "LastAcquisition").text = "" if lastDate is None else str(lastDate)

    products = ET.SubElement(root, "Sentinel1InputProducts")
    for product in s1_list:
        elem = ET.SubElement(products, "Product")
        elem.text = product.split(".SAFE")[0] if product.endswith(".SAFE") else product

    # Pretty print XML
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    with open(xml_filename, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))


def read_export(csv_path, projection, meta_path=None):
    """
    Read ONE CSV (default: ./output.csv), reproject to `projection`,
    write output.gpkg + output.xml in current directory.
    """
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV not found: {csv_path.resolve()}")

    meta_path = Path(meta_path) if meta_path else None
    if meta_path and (not meta_path.is_file()):
        print(f"[WARN] meta file not found: {meta_path.resolve()} (will use NA/empty defaults)")
        meta_path = None

    # Read CSV
    df = pd.read_csv(csv_path)

    # Require LAT/LON
    if "LAT" not in df.columns or "LON" not in df.columns:
        raise ValueError(
            f"{csv_path.name} missing LAT/LON columns.\n"
            f"Found columns: {list(df.columns)}"
        )

    # Build GeoDataFrame in EPSG:4326
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["LON"], df["LAT"]),
        crs="EPSG:4326",
    )

    # Reproject
    try:
        gdf = gdf.to_crs(projection)
    except Exception as e:
        print(f"[WARN] Failed to reproject to {projection}: {e}")
        print("[WARN] Falling back to EPSG:4326.")
        projection = "EPSG:4326"
        gdf = gdf.to_crs("EPSG:4326")

    # Write GPKG
    out_gpkg = "output.gpkg"
    gdf.to_file(out_gpkg, driver="GPKG", index=False)
    print(f"Wrote {out_gpkg} in {Path.cwd()}")

    # Write XML
    create_metadata_xml(gdf, meta_path, projection, xml_filename="output.xml")
    print(f"Wrote output.xml in {Path.cwd()}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert one CSV to GPKG and write XML metadata (output.gpkg / output.xml in current dir)."
    )
    parser.add_argument(
        "--csv", type=str, default="output.csv",
        help="Input CSV file (default: ./output.csv). Must contain LAT/LON columns.",
    )
    parser.add_argument(
        "--meta", type=str, default="output.txt",
        help="Meta txt file (default: ./output.txt) in VARIABLE:VALUE format.",
    )
    parser.add_argument(
        "--projection", "-p", type=str, default="EPSG:4326",
        help="Output projection (default: EPSG:4326).",
    )
    args = parser.parse_args()

    read_export(args.csv, args.projection, meta_path=args.meta)


if __name__ == "__main__":
    main()

