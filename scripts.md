# Script Descriptions and Usage (Processing Order)

This document describes the core scripts used in the GMTSAR+ SBAS workflow, **following the exact processing logic illustrated in the workflow diagram** (data download → GMTSAR processing → SBAS inversion → visualization and export). Descriptions are intentionally concise and example-driven.

---

## Step 1. Data Downloading

This step prepares all input datasets required for InSAR processing, including Sentinel-1 SAR images, DEM, and precise orbit files.

### `download_s1.py`
**Role in workflow**  
Entry point for data acquisition. It reads a KML-defined AOI, determines the bounding box, and orchestrates Sentinel-1 data preparation.

**Main functions**
- Read AOI from KML (or other vector formats)
- Compute AOI bounding box in EPSG:4326
- Call `burst2stack` to download and organize Sentinel-1 TOPS bursts

**Example**
```bash
python download_s1.py \
  --input p32_f544.kml \
  --rel-orbit 32 \
  --start-date 2022-01-01 \
  --end-date 2024-12-31
```

---

### `burst2stack`
**Role in workflow**  
Download and stack Sentinel-1 TOPS bursts covering the AOI and time range.

**Documentation**  
Full usage is provided by ASF:
- https://github.com/ASFHyP3/burst2safe

**Typical call (internal)**
```bash
burst2stack --rel-orbit 32 \
            --start-date 2022-01-01 \
            --end-date 2024-12-31 \
            --extent lon_min lat_min lon_max lat_max
```

---

### `pSAR_srtmdownload.py`
**Role in workflow**  
Download and prepare DEM data covering the processing area.

**Notes**
- Primarily based on the Python package `elevation`
- DEM is used later for topographic phase removal and geocoding

**Reference**  
- https://pypi.org/project/elevation/

**Example**
```bash
python pSAR_srtmdownload.py 119.63,122.10,14.70,15.76
```

---

### `eof`
**Role in workflow**  
Download Sentinel-1 precise or restituted orbit files required for accurate co-registration and interferogram generation.

**Reference**  
- https://github.com/sentinelsat/sentinelsat

**Notes**  
Orbit files are usually downloaded automatically when missing.

---

## Step 2. SBAS Time-Series Deformation Generation

This step performs the core GMTSAR and SBAS processing to generate deformation time series.

### `pSAR_gmtsar_s1.py`
**Role in workflow**  
Main GMTSAR processing driver responsible for generating interferograms and preparing inputs for SBAS inversion.

**Processing stages**
- Primary image selection
- SLC co-registration
- Perpendicular baseline configuration
- Interferogram generation
- Topographic phase removal
- Filtering, unwrapping, and geocoding

**Example**
```bash
pSAR_gmtsar_s1.py \
  -roi 119.63,122.10,14.70,15.76 \
  -tmpbase 36 \
  -s1dir safe \
  -rlook 20 -azlook 4
```

---

### `sbas_gmtsar.sh`
**Role in workflow**  
Perform SBAS inversion using GMTSAR-generated interferograms to produce deformation time series.

**Main functions**
- Build `intf.tab` and `scene.tab`
- Apply small-baseline inversion
- Generate SBAS velocity and displacement products

**Example**
```bash
bash sbas_gmtsar.sh
```

---

### `meta_creator.py`
**Role in workflow**  
Generate metadata describing the SBAS processing configuration and Sentinel-1 inputs.

**Key outputs**
- APS correction method
- DEM source
- List of Sentinel-1 SAFE products

**Example**
```bash
python meta_creator.py -method SBAS
```

---

## Step 3. Results Visualization and Export

This step converts SBAS results into user-friendly geospatial products.

### `vis_kmz.py`
**Role in workflow**  
Convert SBAS CSV results into KMZ files for visualization in Google Earth.

**Features**
- Velocity-colored points
- Interactive displacement time series
- Embedded colorbar

**Example**
```bash
python vis_kmz.py output.csv -vmin -100 -vmax 100
```

---

### `gpkg_wrapper.py`
**Role in workflow**  
Export SBAS results to standard GIS formats for desktop analysis.

**Outputs**
- GeoPackage (`.gpkg`)
- XML metadata file

**Example**
```bash
python gpkg_wrapper.py \
  --csv output.csv \
  --meta output.txt
```

---

## Notes
- In practice, the entire workflow is executed via a single command using `run_sbas.sh`.
- Individual scripts are documented here for clarity, debugging, and advanced customization.
