# GMTSAR+

**GMTSAR+** is a Docker-based extension of GMTSAR for automated Sentinel-1 SBAS-InSAR processing and standardized geospatial product generation.

It integrates Sentinel-1 data preparation, precise orbit-file acquisition, DEM preparation, GMTSAR-based SBAS time-series processing, and standardized output generation into an end-to-end workflow. The workflow exports deformation products in CSV, GeoPackage, KMZ, and XML metadata formats for GIS analysis, Google Earth visualization, product sharing, and processing traceability.

---

## Main features

- Docker-based and reproducible GMTSAR processing environment.
- Automated Sentinel-1 data preparation using SAFE-based and burst-level workflows.
- Precise orbit-file retrieval and DEM preparation.
- End-to-end SBAS processing through `run_sbas.sh`.
- Standardized outputs in CSV, GeoPackage, KMZ, and XML metadata formats.
- Processing-parameter and metadata recording for reproducible product generation.

---

## Repository contents

```text
GMTSARplus/
├── README.md
├── LICENSE
├── Dockerfile
├── installation.md
├── scripts.md
├── update.md
├── demo/
│   ├── demo_run.sh
│   └── example_aoi.kml
├── docs/
└── Copphil-local/
```

| File or directory | Description |
|---|---|
| `Dockerfile` | Docker environment definition for GMTSAR+ processing. |
| `installation.md` | Installation and Docker deployment instructions. |
| `scripts.md` | Description of the main scripts and workflow components. |
| `update.md` | Notes on [pSAR-related updates](https://github.com/wpfeng/utilities_of_GMTSAR_from_pSAR), provenance, and modifications. |
| `demo/` | Lightweight demonstration files, including an example AOI and a runnable command script. |
| `docs/` | Additional figures and documentation. |
| `Copphil-local/` | Local workflow scripts and processing components used by GMTSAR+. |

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Bingquan-InSAR/GMTSARplus.git
cd GMTSARplus
```

Build the Docker image:

```bash
docker build -t gmtsarplus:latest .
```

Run the container:

```bash
docker run -it --rm \
  -v /mnt/gmtsarplus_work:/home/process \
  -w /home/process \
  gmtsarplus:latest \
  bash
```

Detailed installation instructions are provided in `installation.md`.

---

## Quick start

Inside the Docker container, run:

```bash
run_sbas.sh \
  --kml demo/example_aoi.kml \
  --st 20220101 \
  --ed 20220501 \
  --rel_orbit 32 \
  --tmpbase 24 \
  --rlook 20 \
  --azlook 4
```

Main options:

| Option | Description |
|---|---|
| `--kml` | Area-of-interest file in KML format. |
| `--st` | Start date in `YYYYMMDD` format. |
| `--ed` | End date in `YYYYMMDD` format. |
| `--rel_orbit` | Sentinel-1 relative orbit number. |
| `--tmpbase` | Temporal baseline threshold in days. |
| `--rlook` | Range multilooking factor. |
| `--azlook` | Azimuth multilooking factor. |

---

## Outputs

Typical outputs include:

| Output | Description |
|---|---|
| `output.csv` | Standardized CSV containing coordinates, velocity, RMSE, and deformation time series. |
| `output.gpkg` | GIS-ready GeoPackage product. |
| `output.kmz` | Google Earth visualization product. |
| `output.xml` | Metadata file recording processing parameters and product information. |

The exact output names may vary depending on the processing configuration.

---

## Dependencies and computational requirements

GMTSAR+ is distributed through Docker and depends on GMTSAR, GMT, GDAL/OGR, Python utilities, [pSAR-related scripts](https://github.com/wpfeng/utilities_of_GMTSAR_from_pSAR), `burst2stack`, and `eof`.

For real Sentinel-1 SBAS processing, a Linux system with Docker, a multi-core CPU, sufficient memory, and large storage capacity is recommended. The required storage and runtime depend on the number of Sentinel-1 scenes, area size, and multilooking parameters.

---

## Reproducibility

The full Sentinel-1 SLC datasets used in large-area case studies are not redistributed in this repository because of their large volume. These data can be obtained from public Sentinel-1 data services using valid user credentials.

A lightweight demo is provided in the `demo/` directory. It includes an example AOI file and a runnable shell script that illustrates the command-line usage of GMTSAR+.

This repository provides the source code, Dockerfile, installation instructions, processing commands, parameter documentation, and output descriptions required to reproduce the workflow after downloading the corresponding input data.

---

## Relation to GMTSAR and pSAR

GMTSAR+ is built on GMTSAR and integrates selected utilities from the [pSAR Python package](https://github.com/wpfeng/pSAR) into a Docker-based SBAS workflow. The [pSAR package](https://github.com/wpfeng/pSAR) was developed by Associate Professor Wanpeng Feng at Sun Yat-sen University and provides important support for GMTSAR-based Sentinel-1 data preparation, interferogram generation, baseline handling, metadata management, and geospatial format conversion.

Details on pSAR-related script provenance, updates, and modifications are provided in `update.md`.

---

## Citation

If you use GMTSAR+ in academic work, please cite the corresponding manuscript once it is published:

```text
Li, B., and Chang, L. GMTSAR+: An extended GMTSAR workflow streamlining SBAS products with standardized geospatial outputs.
```

Please also cite GMTSAR, [pSAR](https://github.com/wpfeng/utilities_of_GMTSAR_from_pSAR), and other third-party software packages used in your processing chain where appropriate.

---

## License

GMTSAR+ is released under the GNU General Public License v3.0 (GPL-3.0). See the `LICENSE` file for details.

---

## Contact

For questions, bug reports, or suggestions, please use the GitHub Issues page of this repository.
