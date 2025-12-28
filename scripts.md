# Script Descriptions and Usage (Processing Order)

This document provides brief descriptions and example usage for the core scripts used in the GMTSAR+ SBAS workflow, organized by **processing order**. The explanations are intentionally concise and focus on how each script is typically used within this repository.

---

## 1. Data Download and Preparation

### `download_s1.py`
**Purpose**  
Download Sentinel-1 data for a given area of interest (AOI) and time range, and prepare inputs for TOPS burst processing.

**Key features**
- Reads AOI from a vector file (e.g. KML)
- Computes bounding box in EPSG:4326
- Calls `burst2stack` with the computed extent

**Example**
```bash
python download_s1.py \
  --input aoi.kml \
  --rel-orbit 155 \
  --start-date 2025-04-01 \
  --end-date 2025-05-31
```

---

### `burst2stack`
**Purpose**  
Generate Sentinel-1 TOPS burst stacks for a given relative orbit, time range, and spatial extent.

**Documentation**  
Full documentation and usage are provided by ASF:
- https://github.com/ASFHyP3/burst2safe

**Typical usage (called internally)**
```bash
burst2stack --rel-orbit 155 \
            --start-date 2025-04-01 \
            --end-date 2025-05-31 \
            --extent lon_min lat_min lon_max lat_max
```

---

### `eof`
**Purpose**  
Download Sentinel-1 precise or restituted orbit files (EOFs), required for accurate InSAR processing.

**Documentation**  
Orbit download functionality is provided via SentinelSat:
- https://github.com/sentinelsat/sentinelsat

**Notes**  
This step is usually handled automatically when required orbit files are missing.

---

### `pSAR_srtmdownload.py`
**Purpose**  
Download and prepare DEM data (SRTM-based) for the processing area. The script mainly relies on the `elevation` Python package.

**Key dependency**  
- https://pypi.org/project/elevation/

**Example**
```bash
python pSAR_srtmdownload.py 119.5,120.5,14.5,15.5
```

---

## 2. GMTSAR Processing

### `pSAR_gmtsar_s1.py`
**Purpose**  
Main GMTSAR processing driver for Sentinel-1 TOPS data. It controls the full InSAR workflow, including:
- SAFE unpacking and preprocessing
- DEM handling
- Baseline calculation
- Interferogram generation
- Unwrapping and multilooking

**Typical usage**
```bash
pSAR_gmtsar_s1.py \
  -roi west,east,south,north \
  -tmpbase 36 \
  -rlook 20 -azlook 4
```

---

## 3. SBAS Time-Series Processing

### `sbas_gmtsar.sh`
**Purpose**  
Run the SBAS time-series inversion using GMTSAR outputs and export the results to CSV format.

**Main steps**
- Prepare `intf.tab` and `scene.tab`
- Run `sbas` inversion
- Geocode velocity results
- Export SBAS results

**Example**
```bash
bash sbas_gmtsar.sh
```

---

### `meta_creator.py`
**Purpose**  
Generate a simple metadata text file (`output.txt`) from Sentinel-1 SAFE files, used later for product export.

**Key outputs**
- APS correction method
- DEM type
- List of Sentinel-1 input products

**Example**
```bash
python meta_creator.py -method SBAS
```

---

## 4. Product Export

### `gpkg_wrapper.py`
**Purpose**  
Convert SBAS results in CSV format into standard geospatial products:
- GeoPackage (`.gpkg`)
- XML metadata file

**Typical usage**
```bash
python gpkg_wrapper.py \
  --csv output.csv \
  --meta output.txt
```

---

## 5. Visualization

### `vis_kmz.py`
**Purpose**  
Generate KMZ/KML visualization products from SBAS CSV results, including:
- Colored velocity points
- Interactive time-series plots
- Embedded colorbars

**Example**
```bash
python vis_kmz.py output.csv
```

---

## Notes
- Most users do not need to run these scripts individually; they are orchestrated by `run_sbas.sh`.
- Advanced users may customize or re-run individual steps for debugging or experimentation.


