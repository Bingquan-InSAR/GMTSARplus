
#!/usr/bin/env python3
"""
getaoifromkml.py — Read a KML (or other vector), compute its AOI bbox, and call
`burst2stack` with that bbox as --extent.

Output order for --extent is strictly:
    xmin ymin xmax ymax   (i.e., lon_min lat_min lon_max lat_max)

Example
-------
python downloads1.py \
  --input input.kml \
  --rel-orbit 155 \
  --start-date 2025-04-01 \
  --end-date 2025-05-31

This will execute:
  burst2stack --rel-orbit 155 --start-date 2025-04-01 --end-date 2025-05-31 \
              --extent <xmin> <ymin> <xmax> <ymax>

Extras
------
- Pass any unknown args and they will be appended to the burst2stack command.
- Use --dry-run to only print the command without executing.
- Use --precision to control printed bbox/command formatting.
- Supports KML with multiple layers; merges all layers before computing bounds.
- CRS is assumed/forced to EPSG:4326 for extent. Input is reprojected if needed.
"""

import argparse
import os
import sys
import subprocess
from typing import List, Tuple

import geopandas as gpd
import fiona


def read_vector_all_layers(path: str) -> gpd.GeoDataFrame:
    """Read vector; for KML merge all layers. Keep/assign CRS as available."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".kml":
        layers = fiona.listlayers(path)
        frames: List[gpd.GeoDataFrame] = []
        for lyr in layers:
            gdf = gpd.read_file(path, driver="KML", layer=lyr)
            if not gdf.empty:
                frames.append(gdf)
        if not frames:
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        out = gpd.pd.concat(frames, ignore_index=True)
        if out.crs is None:
            out = out.set_crs("EPSG:4326")
        return out
    else:
        gdf = gpd.read_file(path)
        return gdf


def compute_bbox_wgs84(gdf: gpd.GeoDataFrame, assume_crs: str = "EPSG:4326") -> Tuple[float, float, float, float]:
    """Return (minx, miny, maxx, maxy) in EPSG:4326."""
    if gdf.empty or gdf.geometry.is_empty.all():
        raise SystemExit("ERROR: Input has no geometries to bound.")

    if gdf.crs is None:
        # Assume provided CRS if missing
        gdf = gdf.set_crs(assume_crs)
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    minx, miny, maxx, maxy = gdf.total_bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def parse_args():
    p = argparse.ArgumentParser(description="Compute bbox from KML and call burst2stack with --extent xmin ymin xmax ymax")
    p.add_argument("--input", required=True, help="Input KML/GeoJSON/GPKG/Shapefile path")
    p.add_argument("--rel-orbit", required=True, type=int, help="Relative orbit number for burst2stack")
    p.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    p.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")

    p.add_argument("--burst2stack-cmd", default="burst2stack", help="Path or name of burst2stack executable (default: burst2stack)")
    p.add_argument("--precision", type=int, default=6, help="Decimal places for extent values when printing (default: 6)")
    p.add_argument("--assume-crs", default="EPSG:4326", help="CRS to assume when input has no CRS (default: EPSG:4326)")
    p.add_argument("--dry-run", action="store_true", help="Only print the constructed command; do not execute")
    # Any extra args will be forwarded to burst2stack
    ns, unknown = p.parse_known_args()
    ns._forward = unknown
    return ns


def main():
    ns = parse_args()

    gdf = read_vector_all_layers(ns.input)
    minx, miny, maxx, maxy = compute_bbox_wgs84(gdf, assume_crs=ns.assume_crs)

    # Build command for burst2stack
    cmd = [
        ns.burst2stack_cmd,
        "--rel-orbit", str(ns.rel_orbit),
        "--start-date", ns.start_date,
        "--end-date", ns.end_date,
        "--extent", f"{minx}", f"{miny}", f"{maxx}", f"{maxy}",
    ]

    # Forward any unknown/extra args
    if getattr(ns, "_forward", None):
        cmd.extend(ns._forward)

    # Pretty print
    fmt = f"{{:.{ns.precision}f}}"
    printable = [
        ns.burst2stack_cmd,
        "--rel-orbit", str(ns.rel_orbit),
        "--start-date", ns.start_date,
        "--end-date", ns.end_date,
        "--extent", fmt.format(minx), fmt.format(miny), fmt.format(maxx), fmt.format(maxy),
    ] + (ns._forward if getattr(ns, "_forward", None) else [])

    print("Constructed command:" + " ".join(printable))

    if ns.dry_run:
        return

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.stderr.write(f"ERROR: '{ns.burst2stack_cmd}' not found. Set --burst2stack-cmd to its path or add it to PATH.")
        sys.exit(127)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"ERROR: burst2stack exited with code {e.returncode}.")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()

