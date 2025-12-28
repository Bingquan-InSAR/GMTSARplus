#!/usr/bin/env python

import os
import argparse
import sys

# --- Parse command line arguments ---
parser = argparse.ArgumentParser(description="Generate metadata txt file from .SAFE files.")
parser.add_argument('-method', type=str, choices=['PS', 'SBAS'], required=True,
                    help="InSAR method: PS or SBAS. Affects APSCorrection value.")
args = parser.parse_args()

# --- Determine APSCorrection based on method ---
aps_correction = "Spatio-Temporal Filtering" if args.method == 'SBAS' else "Linear Model"

# --- Define constants and paths ---
root_dir = os.getcwd()  # Use current working directory
parent_name = os.path.basename(os.path.normpath(root_dir))
track = os.path.basename(os.path.dirname(root_dir))  # This is the "grandparent" as in your comment

dem = "SRTM"
data_dir = os.path.join(root_dir, "DATA", "S1_UNZIP")

print(f"Scanning data directory: {data_dir}")
file_list = []

# --- Check and read .SAFE files ---
if os.path.exists(data_dir) and os.path.isdir(data_dir):
    for filename in os.listdir(data_dir):
        if filename.endswith(".SAFE"):
            file_list.append(filename)
            print(f"Found .SAFE file: {filename}")
else:
    print(f"Error: 'DATA/S1_UNZIP' directory not found under {root_dir}")
    sys.exit(1)

file_list.sort()  # Fix: sort() was incorrectly used with assignment
list_s1 = ",".join(file_list)

# --- Compose output content ---
output_content = f"""VARIABLE:VALUE
APSCorrection:{aps_correction}
DEM:{dem}
LIST_S1:[{list_s1}]
"""

# --- Write to metadata text file ---
output_file = 'output.txt'
with open(output_file, "w") as f:
    f.write(output_content)

print(f"Metadata file written to: {output_file}")


