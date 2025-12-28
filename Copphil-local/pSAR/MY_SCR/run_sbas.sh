#!/bin/bash
set -euo pipefail

# -----------------------------------------------------------------------------
# run_sbas.sh
#
# SBAS-only end-to-end runner (single relative orbit; no asc/desc switch; no StaMPS)
#
# What it does:
#   1) Activate conda environment
#   2) Ensure output directory ./safe exists (always under the current working directory)
#   3) Use download_s1.py to:
#        - read the AOI from a vector file (KML/GeoJSON/GPKG/...)
#        - compute bbox in EPSG:4326
#        - call burst2stack with --extent xmin ymin xmax ymax
#        - write results to --output-dir ./safe
#   4) (Optional) download precise orbit files via `eof` if $S1_ORB is set
#   5) Run the SBAS processing chain:
#        meta_creator.py -> pSAR_gmtsar_s1_aws.py -> sbas_gmtsar.sh
#
# Requirements:
#   - conda env: gmtsar_python
#   - download_s1.py wrapper script available
#   - burst2stack available in PATH
#   - meta_creator.py / pSAR_gmtsar_s1.py / sbas_gmtsar.sh in PATH
#
# Usage:
#   run_sbas.sh --kml <aoi.kml> --st <YYYYMMDD> --ed <YYYYMMDD> \
#               --rel_orbit <int> --tmpbase <days> --rlook <int> --azlook <int>
#
# Example:
#   run_sbas.sh --kml airport.kml --st 20240101 --ed 20240131 \
#               --rel_orbit 11 --tmpbase 12 --rlook 20 --azlook 4
# -----------------------------------------------------------------------------

source ~/.bashrc
conda activate gmtsar_python

# Change this if you want to run elsewhere:
#cd /home/process

# -----------------------------
# Parse CLI arguments
# -----------------------------
KML=""
ST=""
ED=""
REL_ORBIT=""
TMPBASE=""
RLOOK=""
AZLOOK=""

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --kml)        KML="$2"; shift 2 ;;
    --st)         ST="$2"; shift 2 ;;
    --ed)         ED="$2"; shift 2 ;;
    --rel_orbit)  REL_ORBIT="$2"; shift 2 ;;
    --tmpbase)    TMPBASE="$2"; shift 2 ;;
    --rlook)      RLOOK="$2"; shift 2 ;;
    --azlook)     AZLOOK="$2"; shift 2 ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

[[ -z "$KML" ]]       && { echo "Error: --kml is required"; exit 1; }
[[ -z "$ST" ]]        && { echo "Error: --st is required"; exit 1; }
[[ -z "$ED" ]]        && { echo "Error: --ed is required"; exit 1; }
[[ -z "$REL_ORBIT" ]] && { echo "Error: --rel_orbit is required"; exit 1; }
[[ -z "$TMPBASE" ]]   && { echo "Error: --tmpbase is required"; exit 1; }
[[ -z "$RLOOK" ]]     && { echo "Error: --rlook is required"; exit 1; }
[[ -z "$AZLOOK" ]]    && { echo "Error: --azlook is required"; exit 1; }

# Convert YYYYMMDD -> YYYY-MM-DD
ST_ISO="${ST:0:4}-${ST:4:2}-${ST:6:2}"
ED_ISO="${ED:0:4}-${ED:4:2}-${ED:6:2}"

# Output directory is ALWAYS ./safe under the current working directory
OUTDIR="safe"
mkdir -p "$OUTDIR"

# Path to your KML->bbox->burst2stack wrapper (adjust if needed)
DOWNLOAD_S1_PY="/home/software/Copphil-local/pSAR/MY_SCR/download_s1.py"
[[ -f "$DOWNLOAD_S1_PY" ]] || { echo "ERROR: download_s1.py not found: $DOWNLOAD_S1_PY"; exit 1; }

# -----------------------------
# Compute AOI bbox (ROI string) from the input vector
#
# pSAR_gmtsar_s1_aws.py expects:
#   -roi "west,east,south,north"
# Here we compute bbox in EPSG:4326 and format as:
#   minx,maxx,miny,maxy  -> west,east,south,north
# -----------------------------
export KML_PATH="$KML"
ROI=$(python3 - <<'PY'
import os
import geopandas as gpd
import fiona

path = os.environ["KML_PATH"]
ext = os.path.splitext(path)[1].lower()

frames = []
if ext == ".kml":
    for lyr in fiona.listlayers(path):
        gdf = gpd.read_file(path, driver="KML", layer=lyr)
        if not gdf.empty:
            frames.append(gdf)
    if not frames:
        raise SystemExit("ERROR: Input KML has no geometries.")
    gdf = gpd.pd.concat(frames, ignore_index=True)
else:
    gdf = gpd.read_file(path)

if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326")
if gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")

minx, miny, maxx, maxy = gdf.total_bounds
print(f"{minx:.6f},{maxx:.6f},{miny:.6f},{maxy:.6f}")
PY
)

[[ -n "$ROI" ]] || { echo "ERROR: Failed to compute ROI from $KML"; exit 1; }
echo "[INFO] AOI ROI (west,east,south,north) = $ROI"

# -----------------------------
# Download bursts / SAFE via burst2stack (called inside download_s1.py)
#
# Important:
# - burst2stack uses --output-dir (NOT --outdir)
# - Do NOT pass '--' as a separator
# -----------------------------
echo "[INFO] Downloading bursts via download_s1.py -> burst2stack"
echo "[INFO] rel_orbit=${REL_ORBIT}, ${ST_ISO} to ${ED_ISO}, output-dir=./${OUTDIR}"

python3 "$DOWNLOAD_S1_PY" \
  --input "$KML" \
  --rel-orbit "$REL_ORBIT" \
  --start-date "$ST_ISO" \
  --end-date "$ED_ISO" \
  --output-dir "$OUTDIR"

# -----------------------------
# Download precise orbit files (optional)
# If S1_ORB is set, store orbit files under $S1_ORB/aux_poeorb
# -----------------------------
if [[ -n "${S1_ORB:-}" ]]; then
  echo "[INFO] Downloading orbit files into ${S1_ORB}/aux_poeorb"
  eof --search-path "./${OUTDIR}" --save-dir "${S1_ORB}/aux_poeorb"
else
  echo "[WARN] S1_ORB is not set; skipping orbit download."
fi

# -----------------------------
# Run SBAS processing (single run, using ./safe as S1 directory)
# -----------------------------
echo "[INFO] Running SBAS workflow..."
#

pSAR_gmtsar_s1.py \
  -tmpbase "$TMPBASE" \
  -roi "$ROI" \
  -s1dir "$OUTDIR" \
  -rlook "$RLOOK" \
  -azlook "$AZLOOK"

# Clean up large intermediate TIFFs if they exist
rm -rf raw/*/*/*tiff 2>/dev/null || true


# Wrap to GPKG output (if this is part of your standard deliverable)
meta_creator.py -method SBAS
cp sbas/output.csv .
gpkg_wrapper.py --csv output.csv --meta output.txt -p EPSG:4326
echo "[INFO] DONE."
echo "[INFO] Working directory: $(pwd)"
echo "[INFO] SAFE directory: $(pwd)/${OUTDIR}"

