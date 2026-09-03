# GMTSAR+ Provenance and Contribution Boundary

## Purpose

GMTSAR+ is an integration and workflow-extension project built on the
open-source GMTSAR InSAR processor. This document distinguishes upstream
software and data from scripts adapted or newly developed for GMTSAR+.
The classification is based on the source code included in this repository;
the core GMTSAR and SNAPHU algorithms were not reimplemented.

## Contribution categories

- **External dependency:** used without changing its source code.
- **Adapted script:** derived from an upstream script and modified for a
  GMTSAR+ workflow or data structure.
- **New script:** added specifically for GMTSAR+.
- **External data:** input data or auxiliary products obtained from an
  upstream provider.

## Module-level contribution inventory

| Module or tool | Source and status | Function in GMTSAR+ | Authors' contribution | License or terms | Main input -> output | Testing status |
|---|---|---|---|---|---|---|
| GMTSAR | Official GMTSAR project; external dependency | Sentinel-1 TOPS preprocessing, interferogram generation, geocoding, and SBAS inversion | Integrated and configured; core algorithms unchanged | GPL-3.0 (upstream) | SAFE, PRM, DEM, pair tables -> interferograms, velocity, and displacement time series | Executed in both case studies |
| SNAPHU | Upstream phase-unwrapping software; external dependency | Phase unwrapping | Called by the GMTSAR workflow; no algorithmic modification | Stanford license (upstream) | Wrapped interferograms -> unwrapped phase | Executed in both case studies |
| pSAR | pSAR package by W. Feng; upstream scripts | Sentinel-1 data preparation, baseline handling, SLC preparation, merging, and GMTSAR input generation | Selected scripts are used unchanged; 18 scripts are adapted as listed below | Upstream pSAR terms | SAFE/SLC, orbit, DEM, ROI -> GMTSAR inputs and intermediate products | Integrated in the case-study workflows |
| burst2safe / burst2stack | ASF upstream tools; external dependency | Burst-level Sentinel-1 data acquisition and SAFE preparation | Used as the burst input component; burst reconstruction remains upstream functionality | Upstream repository terms | AOI, dates, orbit selection -> burst-derived SAFE products | Tested with the reported burst acquisitions |
| EOF orbit products | ESA/Copernicus auxiliary data; external data | Precise orbit information | Retrieved and associated with acquisitions; retrieval algorithm unchanged | Provider data terms | SAFE names and dates -> EOF orbit files | Used in both case studies |
| GDAL | Open-source geospatial library; external dependency | Raster conversion, coordinate handling, and GIS packaging | Called by GMTSAR+ export and utility scripts | MIT (upstream) | GRD/GeoTIFF and vector data -> GeoTIFF, GeoPackage, and related products | Used during product generation |
| GMT | Generic Mapping Tools; external dependency | Gridding, filtering, coordinate conversion, plotting, and trend removal | Called by GMTSAR+ scripts; no changes to GMT | LGPL-3.0 (upstream) | GRD, XYZ, and tabular data -> filtered grids and figures | Used during processing and inspection |
| Docker | Container platform; integration component | Reproducible runtime and dependency packaging | Dockerfile and runtime organization added for GMTSAR+ deployment | Upstream Docker terms; project files are GPL-3.0 | Configuration and input data -> reproducible processing environment | End-to-end container execution tested |
| Original pSAR/GMTSAR scripts (29) | Upstream scripts included without source changes | Supporting preparation, baseline, SLC, merging, and geocoding operations | No source-code contribution; retained as upstream components | Respective upstream terms | SAFE/SLC, orbit, DEM -> intermediate GMTSAR products | Used through integrated workflows |
| Adapted scripts (18) | pSAR- or GMTSAR-derived scripts with identifiable changes | SAFE-directory processing, ROI handling, interferogram preparation, unwrapping, geocoding, and SLC refinement | Modified interfaces, directory handling, burst compatibility, masking, detrending, orbit-date handling, cleanup, and execution logic | Respective upstream terms plus GPL-3.0 for project modifications | SAFE/SLC, orbit, DEM, ROI -> co-registered SLCs and geocoded products | Case-study integration tested |
| New GMTSAR+ scripts (14) | Added in this repository | Acquisition, burst/SBAS automation, conversion, export, visualization, and error assessment | New workflow, conversion, RMSE, packaging, and visualization code | GPL-3.0 for project code | AOI and InSAR products -> SBAS products and standardized exports | Tested in the reported workflows; no independent CI suite |

The 14 new scripts include 12 scripts used in the main workflows and two
optional StaMPS helpers (`run_stamps.sh` and `mergeforstamps.csh`). The optional
helpers were not used to support the scientific claims in the manuscript.

## Burst-level GMTSAR compatibility adjustment

`burst2safe` generates valid burst-level SAFE products and source annotation
XML files. In the tested environment, the conventional GMTSAR frame-assembly
workflow (`create_frame_tops.csh`) and the corresponding pSAR workflow
(`GMTSAR_s1_createTOPSframes.csh`) produced an incomplete empty `sliceList`
node during assembly. The subsequent `make_s1a_tops` stage terminated with a
segmentation fault.

GMTSAR+ therefore includes the burst-oriented script
`GMTSAR_s1_createTOPSframes_burst.csh`. This script adapts the frame-assembly
workflow for burst-level products and normalizes the empty XML node before the
downstream GMTSAR stage. The adjustment does not alter timing, orbit,
geolocation, calibration, phase, amplitude, or measurement values. It is a
GMTSAR-side compatibility adaptation, not a correction to the burst2safe
scientific processing algorithm.

The detailed XML comparison, reproducible command, and before/after processing
records are documented in
[`gmtsar_burst_compatibility.md`](gmtsar_burst_compatibility.md).

## Script statistics

The current repository contains 61 `.py`, `.sh`, and `.csh` scripts (excluding
`.js` and `.png` files):

| Category | Number |
|---|---:|
| Original upstream scripts | 29 |
| Adapted scripts | 18 |
| New GMTSAR+ scripts | 14 |
| **Total** | **61** |

## Updated scripts (18)

1. `pSAR_gmtsar_s1.py` - SAFE-directory workflow support, SAFE-compatible parsing, AWS-oriented selection, and robustness improvements.
2. `merge_batch_ps.csh` - PSI-oriented batch merging support.
3. `pSAR_S1select_aws.py` - SAFE-directory Sentinel-1 selection for cloud or mounted archives.
4. `merge_unwrap_geocode_tops_ps.csh` - PSI-oriented merge, unwrap, and geocode support.
5. `GMTSAR_s1_createTOPSframes.csh` - cleanup robustness improvement.
6. `create_merge_input_ps.csh` - PSI-oriented merge-input preparation.
7. `pSAR_gmtsar_s1insar2roi_aws.py` - SAFE-directory ROI workflow support.
8. `gmtsar_unwrap.py` - SNAPHU configuration and landmask automation improvements.
9. `GMTSAR_s1_createTOPSframes_burst.csh` - burst-level GMTSAR frame-assembly compatibility.
10. `pSAR_gmtsar_dir2roi_aws.py` - SAFE-directory ROI workflow support.
11. `pSAR_gmtsar_s1_aws.py` - SAFE-directory Sentinel-1 processing entry point.
12. `gmtsar_geocode.csh` - trend removal for unwrapped products.
13. `pSAR_gmtsar_baseline2intfin.py` - StaMPS-oriented baseline selection logic.
14. `pSAR_gmtsar_dir2datalist.py` - updated orbit-association and date handling.
15. `pSAR_gmtsar_geocode_dir.py` - trend removal for unwrapped products.
16. `pSAR_srtmdownload.py` - safer temporary-file cleanup.
17. `pSAR_gmtsar_tiff2slcs_paral.py` - executes SLC refinement calls rather than only printing them.
18. `intf_tops_ps.csh` - PSI-oriented interferogram preparation.

## New scripts (14)

- `3d_times_sbas.py`
- `download_s1.py`
- `export_csv.py`
- `gpkg_wrapper.py`
- `rmse.py`
- `run_sbas.sh`
- `run_stamps.sh`
- `sbas2xyz_aws.sh`
- `sbas2xyz_burst.sh`
- `sbas_gmtsar_aws.sh`
- `sbas_gmtsar_burst.sh`
- `vis_kmz.py`
- `meta_creator.py`
- `mergeforstamps.csh`

## Unmodified scripts (29)

The 29 unmodified scripts are retained as upstream components. Their complete
names are listed in the repository file [`update.md`](update.md), together
with the corresponding script-level update history.

## Reproducibility and licensing note

Project-specific additions and modifications are released under the project
license. Third-party software, scripts, data, and auxiliary products retain
their respective upstream licenses or provider terms. Users should consult
the cited upstream repositories for the authoritative license text and
version-specific conditions.
