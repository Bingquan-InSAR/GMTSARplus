#!/usr/bin/env python
import csv
import random
import string
import os
import pandas as pd

# Function to generate random alphanumeric code
def generate_code(length=5):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

# Check if required files exist
required_files = ['height.xyz', 'vel_ll.xyz', 'rmse.xyz', 'corr.xyz', 'vel_ra.xyz', 'heading', 'incidence']
for file in required_files:
    if not os.path.isfile(file):
        print(f"Error: {file} is missing.")
        exit(1)

# Open the files and write to output.csv
with open('height.xyz', 'r') as height_file, open('vel_ll.xyz', 'r') as vel_file, open('rmse.xyz', 'r') as rmse_file, \
     open('corr.xyz', 'r') as corr_file, open('vel_ra.xyz', 'r') as vel_ra_file, open('heading', 'r') as heading_file, \
     open('incidence', 'r') as incidence_file, open('output.csv', 'w', newline='') as outfile:

    writer = csv.writer(outfile)
    writer.writerow(['CODE', 'LAT', 'LON', 'HEIGHT', 'VEL', 'RMSE', 'COHER', 'Range', 'Azimuth', 'Heading', 'Incidence'])  # Column headers
    
    # Read the lines from other files
    vel_lines = vel_file.readlines()
    vel_ra_lines = vel_ra_file.readlines()
    rmse_lines = rmse_file.readlines()
    corr_lines = corr_file.readlines()

    # Read heading and incidence
    heading_value = heading_file.read().strip()
    incidence_value = incidence_file.read().strip()

    for i, line in enumerate(height_file):
        # Process each line in height.xyz
        height_parts = line.strip().split()
        if len(height_parts) == 3:
            try:
                lon = float(height_parts[0])
                lat = float(height_parts[1])
                height = float(height_parts[2])
                lon_str = f"{lon:.6f}"
                lat_str = f"{lat:.6f}"
                height_str = f"{height:.1f}"

                # Process vel_ll.xyz (velocity)
                if i < len(vel_lines):
                    vel_parts = vel_lines[i].strip().split()
                    vel_str = f"{float(vel_parts[2]):.2f}" if len(vel_parts) > 2 else ''
                else:
                    vel_str = ''

                # Process rmse.xyz
                if i < len(rmse_lines):
                    rmse_parts = rmse_lines[i].strip().split()
                    rmse_str = f"{float(rmse_parts[2]):.2f}" if len(rmse_parts) > 2 else ''
                else:
                    rmse_str = ''

                # Process corr.xyz (correlation)
                if i < len(corr_lines):
                    corr_parts = corr_lines[i].strip().split()
                    coher_str = f"{float(corr_parts[2]):.2f}" if len(corr_parts) > 2 else ''
                else:
                    coher_str = ''

                # Process vel_ra.xyz (range and azimuth)
                if i < len(vel_ra_lines):
                    vel_ra_parts = vel_ra_lines[i].strip().split()
                    range_str = f"{round(float(vel_ra_parts[0]))}" if len(vel_ra_parts) > 0 else ''
                    azimuth_str = f"{round(float(vel_ra_parts[1]))}" if len(vel_ra_parts) > 1 else ''
                else:
                    range_str, azimuth_str = '', ''

                # Generate random code for the row
                code = generate_code()

                # Write the row to output.csv
                writer.writerow([code, lat_str, lon_str, height_str, vel_str, rmse_str, coher_str, range_str, azimuth_str, heading_value, incidence_value])
            except (ValueError, IndexError):
                continue  # Skip invalid lines


# List of D20****.xyz files in the current directory
files = sorted([f for f in os.listdir() if f.startswith('D20') and f.endswith('.xyz')])

# Create an empty DataFrame to store the data from D20 files
df = pd.DataFrame()

# Loop through each D20 file and extract the third column
for file in files:
    # Read the data from the D20 file
    data = pd.read_csv(file, delim_whitespace=True, header=None)
    
    # Extract the third column and round it to 2 decimal places
    third_column = data[2].round(2)
    
    # Name the new column based on the file name (without the .xyz extension)
    column_name = file.replace('.xyz', '')
    
    # Add the third column to the DataFrame
    df[column_name] = third_column

# Load the existing output.csv into a DataFrame
existing_df = pd.read_csv("output.csv")

# Concatenate the new data (df) with the existing data (existing_df)
combined_df = pd.concat([existing_df, df], axis=1)

# Save the combined DataFrame to output.csv
combined_df.to_csv("output.csv", index=False)

print("New columns from D20 files have been added to output.csv.")

