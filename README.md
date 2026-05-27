# GMTSAR+

**GMTSAR+** is an automated and reproducible GMTSAR-based SBAS-InSAR workflow for Sentinel-1 data processing and standardized geospatial product generation.

GMTSAR+ extends the original GMTSAR workflow by integrating Sentinel-1 data retrieval, precise orbit-file acquisition, DEM preparation, SBAS time-series processing, and standardized output generation into a Docker-based command-line workflow. The software is designed for local workstations and server-based environments where reproducibility, automation, and GIS-ready outputs are required.

The workflow exports InSAR deformation products in commonly used formats, including CSV, GeoPackage, KMZ, and XML metadata files. These outputs support post-processing, GIS analysis, Google Earth visualization, product sharing, and processing traceability.

---

## Main features

- Docker-based deployment for a reproducible processing environment.
- Automated Sentinel-1 data retrieval using SAFE-based and burst-level workflows.
- Precise orbit-file acquisition using `eof`.
- DEM downloading and preparation for GMTSAR processing.
- End-to-end SBAS processing through `run_sbas.sh`.
- Integration with GMTSAR, GMT, GDAL/OGR, pSAR utilities, `burst2stack`, and `eof`.
- Standardized geospatial outputs in CSV, GeoPackage, KMZ, and XML metadata formats.
- Metadata recording for processing parameters, input data, and output products.
- Documentation and example commands for reproducible use.

---

## Repository contents

The main repository structure is:

```text
GMTSARplus/
├── README.md
├── LICENSE
├── Dockerfile
├── installation.md
├── scripts.md
├── update.md
├── docs/
└── Copphil-local/
```

The key documentation files are:

| File | Description |
|---|---|
| `README.md` | Overview, installation, usage, input/output description, and reproducibility notes. |
| `installation.md` | Detailed installation and Docker deployment instructions. |
| `scripts.md` | Description of the main scripts and their roles in the workflow. |
| `update.md` | Notes on pSAR-related updates, provenance, and modifications. |
| `Dockerfile` | Docker environment definition for GMTSAR+ processing. |
| `LICENSE` | Software license. |

---

## Relation to GMTSAR and pSAR

GMTSAR+ is built on top of the GMTSAR processing framework and uses selected utilities from the pSAR Python package during the interferometric processing stage.

The pSAR package, developed by Associate Professor Wanpeng Feng at Sun Yat-sen University, provides tools for GMTSAR-based Sentinel-1 data preparation, interferogram generation, baseline handling, metadata management, and geospatial format conversion.

In GMTSAR+, selected pSAR utilities are adapted and integrated into an end-to-end Docker-based SBAS workflow. Details on the provenance of pSAR-related scripts and modifications are provided in `update.md`.

---

## Installation

GMTSAR+ is primarily distributed through Docker. The Docker image provides a controlled processing environment that includes GMTSAR, GMT, GDAL/OGR, Python utilities, pSAR-related scripts, `burst2stack`, `eof`, and other runtime dependencies required by the workflow.

### Requirements

For a lightweight test or small demonstration:

- Linux operating system or a system with Docker support.
- Docker installed.
- 2 CPU cores or more.
- 4 GB RAM or more.

For a real Sentinel-1 SBAS processing case:

- Linux operating system, Ubuntu 18.04 or later recommended.
- Docker installed.
- Multi-core CPU recommended.
- 32 GB RAM or more recommended for large-area time-series processing.
- Hundreds of GB to several TB of storage, depending on the number of Sentinel-1 scenes and the area of interest.
- Valid credentials for Sentinel-1 data access when automated downloading is required.

### Clone the repository

```bash
git clone https://github.com/Bingquan-InSAR/GMTSARplus.git
cd GMTSARplus
```

### Build the Docker image

```bash
docker build -t gmtsarplus:latest .
```

### Run the Docker container

Create a working directory on the host machine:

```bash
mkdir -p /mnt/gmtsarplus_work
```

Run the container:

```bash
docker run -it --rm \
  -v /mnt/gmtsarplus_work:/home/process \
  -w /home/process \
  gmtsarplus:latest \
  bash
```

Here, `/mnt/gmtsarplus_work` is the working directory on the host machine, and `/home/process` is the working directory inside the container.

### Verify the processing environment

Inside the container, check the main software components:

```bash
gmt --version
gdalinfo --version
python --version
which run_sbas.sh
which pSAR_gmtsar_s1.py
which burst2stack
which eof
```

---

## Data access configuration

Before running automated Sentinel-1 downloads, valid credentials should be configured for the required data services.

A typical `.netrc` file may include credentials for NASA Earthdata and/or the Copernicus Data Space Ecosystem:

```text
machine urs.earthdata.nasa.gov
  login YOUR_EARTHDATA_USERNAME
  password YOUR_EARTHDATA_PASSWORD

machine dataspace.copernicus.eu
  login YOUR_COPERNICUS_USERNAME
  password YOUR_COPERNICUS_PASSWORD
```

For security, restrict the file permission:

```bash
chmod 600 ~/.netrc
```

The exact data-access configuration depends on the data source used by the workflow.

---

## Quick start

After entering the Docker container, GMTSAR+ can be executed using `run_sbas.sh`.

Example:

```bash
run_sbas.sh \
  --kml airport.kml \
  --st 20240101 \
  --ed 20240131 \
  --rel_orbit 11 \
  --tmpbase 12 \
  --rlook 20 \
  --azlook 4
```

This command performs SBAS processing for the area of interest defined by `airport.kml` between 1 January 2024 and 31 January 2024, using Sentinel-1 relative orbit 11, a temporal baseline threshold of 12 days, and multilooking factors of 20 and 4 in the range and azimuth directions, respectively.

---

## Main workflow

The main workflow is controlled by `run_sbas.sh`.

The script executes the following processing steps:

1. Read the area of interest from the input KML file.
2. Derive the geographic bounding box in EPSG:4326.
3. Download or organize Sentinel-1 data for the selected time range and relative orbit.
4. Retrieve precise orbit files.
5. Download and prepare DEM data.
6. Generate interferograms using the GMTSAR-based processing chain.
7. Perform SBAS time-series processing.
8. Export deformation products in standardized geospatial formats.
9. Generate metadata files for processing traceability.

---

## Command-line options

General usage:

```bash
run_sbas.sh \
  --kml <AOI.kml> \
  --st <YYYYMMDD> \
  --ed <YYYYMMDD> \
  --rel_orbit <int> \
  --tmpbase <int> \
  --rlook <int> \
  --azlook <int>
```

### Arguments

| Argument | Description |
|---|---|
| `--kml` | Area-of-interest file in KML format. |
| `--st` | Start date in `YYYYMMDD` format. |
| `--ed` | End date in `YYYYMMDD` format. |
| `--rel_orbit` | Sentinel-1 relative orbit number. |
| `--tmpbase` | Temporal baseline threshold in days. |
| `--rlook` | Range multilooking factor. |
| `--azlook` | Azimuth multilooking factor. |
| `-h`, `--help` | Show help information. |

---

## Input files

### Area-of-interest file

The main required input is a KML file defining the area of interest.

Example:

```text
airport.kml
```

The AOI bounding box is automatically derived in EPSG:4326 and formatted as:

```text
west,east,south,north
```

This format is required by the GMTSAR/pSAR processing interface.

### Date range

The date range is specified using:

```bash
--st <YYYYMMDD>
--ed <YYYYMMDD>
```

### Orbit and SBAS parameters

The Sentinel-1 relative orbit and SBAS processing parameters are specified using:

```bash
--rel_orbit <int>
--tmpbase <days>
--rlook <int>
--azlook <int>
```

---

## Output files

The output files are generated in the working directory.

Typical outputs include:

| Output | Description |
|---|---|
| `sbas/output.csv` | Original SBAS deformation results generated by the GMTSAR-based processing chain. |
| `output.csv` | Standardized CSV file containing coordinates, velocity, RMSE, and deformation time series. |
| `output.gpkg` | GIS-ready GeoPackage product for spatial analysis and visualization. |
| `output.kmz` | Google Earth visualization product with deformation velocity and point-wise time-series information. |
| `output.xml` | Metadata file recording processing parameters, acquisition information, and product-generation details. |

The exact output file names may vary depending on the processing configuration.

---

## Expected behaviour

A successful GMTSAR+ run should:

1. Read the AOI from the input KML file.
2. Derive the geographic bounding box.
3. Download or organize the required Sentinel-1 data.
4. Retrieve the required precise orbit files.
5. Prepare the DEM.
6. Generate interferograms.
7. Perform SBAS time-series inversion.
8. Export standardized CSV, GeoPackage, KMZ, and XML metadata products.

If input data are missing, credentials are invalid, or required files cannot be downloaded, the workflow should stop with an error message indicating the failed processing step.

---

## Reproducibility

The full Sentinel-1 SLC datasets used in large-area case studies are not redistributed in this repository because of their large data volume. These data can be obtained from public Sentinel-1 data services using valid user credentials.

To support reproducibility, this repository provides:

- The source code of the processing workflow.
- The Dockerfile used to construct the processing environment.
- Installation and usage instructions.
- Main processing commands and parameters.
- Documentation of input files, output files, and expected behaviour.
- Processing provenance and script update notes.

For large-area real-data experiments, users should download the corresponding Sentinel-1 data using the provided commands and then execute the workflow with the same processing parameters.

---

## Typical use cases

GMTSAR+ is designed for the following use cases:

- Sentinel-1 SBAS-InSAR deformation monitoring.
- Large-area land subsidence analysis.
- Earthquake-related deformation mapping when suitable data are available.
- Generation of GIS-ready InSAR products.
- Standardized deformation product sharing in GeoPackage and KMZ formats.
- Reproducible InSAR workflow deployment using Docker.

---

## Documentation

Additional documentation is available in the following files:

- `installation.md` — installation and Docker setup.
- `scripts.md` — description of major scripts and their functions.
- `update.md` — pSAR-related provenance and update notes.
- `docs/` — figures and supplementary documentation when available.

---

## Limitations

GMTSAR+ depends on external data services for Sentinel-1 data and orbit-file retrieval. Therefore, the reproducibility of full real-data workflows depends on data availability, user credentials, network conditions, and the long-term accessibility of external data archives.

Large Sentinel-1 SLC datasets are not included in this repository because of their size. Users should obtain the corresponding data from public Sentinel-1 archives before running the full workflow.

---

## Code comments

All comments in the source code should be written in English. If non-English comments are found, they should be translated before release or submission.

---

## Citation

If you use GMTSAR+ in academic work, please cite the corresponding manuscript once it is published.

A suggested citation format is:

```text
Li, B., and Chang, L. GMTSAR+: An extended GMTSAR workflow streamlining SBAS products with standardized geospatial outputs.
```

Please also cite GMTSAR, pSAR, and other third-party software packages used in your processing chain where appropriate.

---

## License

GMTSAR+ is released under the GNU General Public License v3.0 (GPL-3.0). See the `LICENSE` file for details.

---

## Contact

For questions, bug reports, or suggestions, please use the GitHub Issues page of this repository.
