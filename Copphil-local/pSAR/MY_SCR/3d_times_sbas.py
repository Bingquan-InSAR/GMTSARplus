#!/usr/bin/env python 
###############################################################################
# Sentinel-1 CSV 2D Decomposition Script
# Created by Bingquan Li and Ling Chang on August 19, 2025
# Purpose:
#   1. Load ascending and descending Sentinel-1 time-series CSV files
#   2. Generate .grd rasters for height, incidence, heading, displacement, etc.
#   3. Perform 2D decomposition to extract vertical and horizontal deformation
#   4. Estimate velocity and standard deviation (STD) maps
#   5. Export time-series results to CSV for further visualization and analysis
###############################################################################
import pandas as pd
from datetime import datetime
import re
import os
import argparse
import rasterio
import numpy as np
import string
import random
from glob import glob

# Argument parsing
parser = argparse.ArgumentParser(description="Process Sentinel-1 CSV, generate .grd and perform 2D decomposition.")
parser.add_argument("csv_as", help="Ascending orbit CSV file")
parser.add_argument("csv_ds", help="Descending orbit CSV file")
args = parser.parse_args()

# Load data and define overlap bounds
df1 = pd.read_csv(args.csv_as)
df2 = pd.read_csv(args.csv_ds)
as_coords = pd.read_csv(args.csv_as, usecols=['LON', 'LAT'])
ds_coords = pd.read_csv(args.csv_ds, usecols=['LON', 'LAT'])

min_lon = max(as_coords['LON'].min(), ds_coords['LON'].min())
max_lon = min(as_coords['LON'].max(), ds_coords['LON'].max())
min_lat = max(as_coords['LAT'].min(), ds_coords['LAT'].min())
max_lat = min(as_coords['LAT'].max(), ds_coords['LAT'].max())

# Extract time columns
time_cols1 = sorted([col for col in df1.columns if col.startswith('D')])
time_cols2 = sorted([col for col in df2.columns if col.startswith('D')])

# Helper functions
def parse_dates_dict(cols):
    return {col: datetime.strptime(re.sub(r'^\D+', '', col), "%Y%m%d") for col in cols}

def make_xyz2grd_cmd(csv, colname, output):
    return f"""awk -F',' -v col={colname} '
NR==1 {{
    for (i=1; i<=NF; i++) {{
        if ($i == "LAT") LAT=i;
        if ($i == "LON") LON=i;
        if ($i == col) VAL=i;
    }}
}}
NR>1 {{ print $LON, $LAT, $VAL }}
' {csv} | gmt xyz2grd -G{output} -R{min_lon}/{max_lon}/{min_lat}/{max_lat} -I3.5s/3s"""

def read_grd(file_path):
    with rasterio.open(file_path) as src:
        return src.read(1), src.profile

def save_grd(data, ref_profile, filename):
    profile = ref_profile.copy()
    profile.update(driver="NETCDF", dtype=rasterio.float32)
    with rasterio.open(filename, "w", **profile) as dst:
        dst.write(data.astype(np.float32), 1)

def generate_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Match nearest dates
dates1 = parse_dates_dict(time_cols1)
dates2 = parse_dates_dict(time_cols2)

if len(dates1) <= len(dates2):
    base_dates, search_dates = dates1, dates2
    base_csv, search_csv = args.csv_as, args.csv_ds
else:
    base_dates, search_dates = dates2, dates1
    base_csv, search_csv = args.csv_ds, args.csv_as

for var in ['HEIGHT', 'LON', 'LAT']:
    os.system(make_xyz2grd_cmd(base_csv, var, f"{var.lower()}.grd"))

nearest_mapping = {
    base_col: min(search_dates.items(), key=lambda item: abs(item[1] - base_date))[0]
    for base_col, base_date in base_dates.items()
}

# Prepare ancillary data
os.system(make_xyz2grd_cmd(args.csv_as, "Incidence", "inc_as.grd"))
os.system(make_xyz2grd_cmd(args.csv_as, "Heading", "head_as.grd"))
os.system(make_xyz2grd_cmd(args.csv_ds, "Incidence ", "inc_ds.grd"))
os.system(make_xyz2grd_cmd(args.csv_ds, "Heading", "head_ds.grd"))

thetaa, profile = read_grd("inc_as.grd")
aha, _ = read_grd("head_as.grd")
thetad, _ = read_grd("inc_ds.grd")
ahd, _ = read_grd("head_ds.grd")

# Decomposition
for v, k in nearest_mapping.items():
    os.system(make_xyz2grd_cmd(args.csv_as, k, "vel_as.grd"))
    os.system(make_xyz2grd_cmd(args.csv_ds, v, "vel_ds.grd"))
    Da, _ = read_grd("vel_as.grd")
    Dd, _ = read_grd("vel_ds.grd")

    gamma = 90
    A = np.stack([
        np.stack([np.cos(np.radians(thetaa)), np.sin(np.radians(thetaa)) * np.sin(np.radians(aha - gamma))], axis=-1),
        np.stack([np.cos(np.radians(thetad)), np.sin(np.radians(thetad)) * np.sin(np.radians(ahd - gamma))], axis=-1)
    ], axis=-1)

    ATA_inv = np.linalg.inv(np.einsum("...ji,...jk->...ik", A, A))
    AT_D = np.einsum("...ij,...j->...i", A, np.stack([Da, Dd], axis=-1))
    ue = np.einsum("...ij,...j->...i", ATA_inv, AT_D)

    save_grd(ue[..., 0], profile, f"Vertical_{k}_{v}.grd")
    save_grd(ue[..., 1], profile, f"Horizontal_{k}_{v}.grd")

# Velocity and STD computation
def compute_velocity_and_std(grd_list, output_vel, output_std, ref_profile):
    stack = []
    times = []

    for f in sorted(grd_list):
        match = re.search(r'D(\d{8})_D(\d{8})', f)
        if not match:
            continue
        t = datetime.strptime(match.group(1), "%Y%m%d")
        times.append(t)
        data, _ = read_grd(f)
        stack.append(data)

    times = np.array([(t - times[0]).days / 365.25 for t in times])
    stack = np.stack(stack, axis=-1)

    rows, cols, T = stack.shape
    vel_map, std_map = np.full((rows, cols), np.nan), np.full((rows, cols), np.nan)
    X = np.vstack([times, np.ones_like(times)]).T

    for i in range(rows):
        for j in range(cols):
            y = stack[i, j, :]
            if np.any(np.isnan(y)):
                continue
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            vel_map[i, j] = coeffs[0]
            if T > 2:
                residuals = y - X @ coeffs
                std_map[i, j] = np.sqrt(np.sum(residuals**2) / (T - 2))

    save_grd(vel_map, ref_profile, output_vel)
    save_grd(std_map, ref_profile, output_std)

# Export to CSV
def export_deformation_csv(grd_files, velocity_grd, std_grd, lat_grd, lon_grd, hgt_grd, output_csv):
    vel_data, _ = read_grd(velocity_grd)
    std_data, _ = read_grd(std_grd)
    lat_data, _ = read_grd(lat_grd)
    lon_data, _ = read_grd(lon_grd)
    hgt_data, _ = read_grd(hgt_grd)

    ts_data = []
    date_labels = []
    for f in sorted(grd_files):
        match = re.search(r'D(\d{8})', f)
        if match:
            date_str = "D" + match.group(1)
            date_labels.append(date_str)
            data, _ = read_grd(f)
            ts_data.append(data)

    ts_stack = np.stack(ts_data, axis=-1)
    rows, cols = vel_data.shape
    records, used_codes = [], set()

    for i in range(rows):
        for j in range(cols):
            if (
                np.isnan(lat_data[i, j]) or
                np.isnan(lon_data[i, j]) or
                np.isnan(hgt_data[i, j]) or
                np.isnan(vel_data[i, j]) or
                np.isnan(std_data[i, j]) or
                np.all(np.isnan(ts_stack[i, j, :]))
            ):
                continue
            code = generate_code()
            while code in used_codes:
                code = generate_code()
            used_codes.add(code)
            row = {
                "CODE": code,
                "LAT": lat_data[i, j],
                "LON": lon_data[i, j],
                "HEIGHT": hgt_data[i, j],
                "VEL": vel_data[i, j],
                "VSDEV": std_data[i, j],
            }
            for k, label in enumerate(date_labels):
                row[label] = ts_stack[i, j, k]
            records.append(row)

    pd.DataFrame.from_records(records).to_csv(output_csv, index=False)

# Run final steps
compute_velocity_and_std(sorted(glob("Vertical_D*.grd")), "Vertical_velocity.grd", "Vertical_std.grd", profile)
compute_velocity_and_std(sorted(glob("Horizontal_D*.grd")), "Horizontal_velocity.grd", "Horizontal_std.grd", profile)

export_deformation_csv(
    grd_files=sorted(glob("Horizontal_D*.grd")),
    velocity_grd="Horizontal_velocity.grd",
    std_grd="Horizontal_std.grd",
    lat_grd="lat.grd",
    lon_grd="lon.grd",
    hgt_grd="height.grd",
    output_csv="Horizontal_timeseries.csv"
)

export_deformation_csv(
    grd_files=sorted(glob("Vertical_D*.grd")),
    velocity_grd="Vertical_velocity.grd",
    std_grd="Vertical_std.grd",
    lat_grd="lat.grd",
    lon_grd="lon.grd",
    hgt_grd="height.grd",
    output_csv="Vertical_timeseries.csv"
)
