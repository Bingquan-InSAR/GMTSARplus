#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import xarray as xr


def read_lines(fname: str) -> list[str]:
    lines = []
    with open(fname, "r", encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if s:
                lines.append(s)
    return lines


def parse_dates_yyyymmdd(date_lines: list[str]) -> np.ndarray:
    # returns np.ndarray of datetime64[ns]
    dts = []
    for s in date_lines:
        # expect YYYYMMDD
        dts.append(np.datetime64(datetime.strptime(s, "%Y%m%d")))
    return np.array(dts, dtype="datetime64[ns]")


def time_years_since_first(dts: np.ndarray) -> np.ndarray:
    # MATLAB: days(dt - t0) / 365.25
    t0 = dts[0]
    days = (dts - t0) / np.timedelta64(1, "D")
    return days.astype(np.float64) / 365.25


def open_gmt_grid(path: str) -> xr.DataArray:
    """
    Open GMT netCDF grid (.grd) with xarray.

    Returns a DataArray with dims (lat, lon) or (y, x) depending on file,
    with coords present.
    """
    ds = xr.open_dataset(path, engine="netcdf4")

    # pick first data_var (usually 'z' for GMT grids)
    if len(ds.data_vars) == 0:
        raise RuntimeError(f"No data variables found in {path}")
    var = list(ds.data_vars)[0]
    da = ds[var]

    # Ensure float64 for stable math
    da = da.astype(np.float64)

    return da


def get_lon_lat_coords(da: xr.DataArray) -> tuple[np.ndarray, np.ndarray, str, str]:
    """
    Try to infer lon/lat coordinate arrays and their dim names.
    """
    dims = list(da.dims)

    # Common GMT CF names: lon/lat OR x/y
    lon_name = None
    lat_name = None

    for name in da.coords:
        low = name.lower()
        if low in ("lon", "longitude", "x"):
            lon_name = name
        if low in ("lat", "latitude", "y"):
            lat_name = name

    # Fallback: infer from dims if coords missing
    if lon_name is None:
        for d in dims:
            if d.lower() in ("lon", "longitude", "x"):
                lon_name = d
                break
    if lat_name is None:
        for d in dims:
            if d.lower() in ("lat", "latitude", "y"):
                lat_name = d
                break

    if lon_name is None or lat_name is None:
        raise RuntimeError(f"Cannot infer lon/lat coordinate names from dims={dims} coords={list(da.coords)}")

    lon = da[lon_name].values
    lat = da[lat_name].values
    return lon, lat, lon_name, lat_name


def main(date_file: str = "date", disp_list_file: str = "disp_list") -> int:
    dates_txt = read_lines(date_file)
    disps_txt = read_lines(disp_list_file)

    if len(dates_txt) != len(disps_txt):
        print(f"ERROR: length mismatch: {date_file}={len(dates_txt)} lines, {disp_list_file}={len(disps_txt)} lines", file=sys.stderr)
        return 2
    if len(dates_txt) < 2:
        print("ERROR: need at least 2 epochs", file=sys.stderr)
        return 2

    dts = parse_dates_yyyymmdd(dates_txt)
    t = time_years_since_first(dts)  # shape (K,)

    # Build list of *_ll.grd paths
    ll_paths: list[str] = []
    for g in disps_txt:
        # disp_XXXX.grd -> disp_XXXX_ll.grd
        base = g[:-4] if g.lower().endswith(".grd") else g
        ll = f"{base}_ll.grd"
        if not Path(ll).is_file():
            print(f"ERROR: missing grid: {ll}", file=sys.stderr)
            return 2
        ll_paths.append(ll)

    # Open template to get shape/coords
    tmpl = open_gmt_grid(ll_paths[0])
    lon, lat, lon_name, lat_name = get_lon_lat_coords(tmpl)
    # Ensure 2D order is (lat, lon) but keep dims as in file
    dims = tmpl.dims
    shape = tmpl.shape

    # Accumulators (NaN-aware): N, sum(t), sum(t^2), sum(y), sum(t*y)
    N = np.zeros(shape, dtype=np.float64)
    SUMT = np.zeros(shape, dtype=np.float64)
    SUMT2 = np.zeros(shape, dtype=np.float64)
    SUMY = np.zeros(shape, dtype=np.float64)
    SUMTY = np.zeros(shape, dtype=np.float64)

    print(f"Pass 1/2: accumulating OLS sums over {len(ll_paths)} epochs ...")
    for k, p in enumerate(ll_paths):
        da = open_gmt_grid(p)
        y = da.values  # float64 with NaN
        m = np.isfinite(y)  # valid mask

        tk = float(t[k])

        # update only where valid
        N[m] += 1.0
        SUMT[m] += tk
        SUMT2[m] += tk * tk
        SUMY[m] += y[m]
        SUMTY[m] += tk * y[m]

        if (k + 1) % 10 == 0 or k == 0 or k == len(ll_paths) - 1:
            print(f"  epoch {k+1}/{len(ll_paths)}: {p}")

    # Solve per-pixel linear regression y ≈ a*t + b
    den = N * SUMT2 - SUMT * SUMT
    # invalid where N<2 or den==0
    valid_reg = (N >= 2) & np.isfinite(den) & (np.abs(den) > 0)

    A = np.full(shape, np.nan, dtype=np.float64)
    B = np.full(shape, np.nan, dtype=np.float64)

    A[valid_reg] = (N[valid_reg] * SUMTY[valid_reg] - SUMT[valid_reg] * SUMY[valid_reg]) / den[valid_reg]
    B[valid_reg] = (SUMY[valid_reg] - A[valid_reg] * SUMT[valid_reg]) / N[valid_reg]

    # Pass 2: SSE = Σ (y - (A*t + B))^2 over valid epochs
    SSE = np.zeros(shape, dtype=np.float64)

    print("Pass 2/2: accumulating residual SSE ...")
    for k, p in enumerate(ll_paths):
        da = open_gmt_grid(p)
        y = da.values
        m = np.isfinite(y) & valid_reg

        tk = float(t[k])
        model = A * tk + B
        res = y - model

        SSE[m] += res[m] * res[m]

        if (k + 1) % 10 == 0 or k == 0 or k == len(ll_paths) - 1:
            print(f"  epoch {k+1}/{len(ll_paths)}: {p}")

    RMSE = np.full(shape, np.nan, dtype=np.float64)
    RMSE[valid_reg] = np.sqrt(SSE[valid_reg] / N[valid_reg])

    # Write netCDF (rmse_ll.nc)
    out_nc = "rmse_ll.nc"
    rmse_da = xr.DataArray(
        RMSE,
        dims=dims,
        coords={lon_name: tmpl[lon_name], lat_name: tmpl[lat_name]},
        name="rmse",
        attrs={"long_name": "RMSE to linear trend (y ≈ a*t + b)", "units": "same_as_input"},
    )
    rmse_da.to_netcdf(out_nc)
    print(f"Wrote {out_nc}")


    return 0


if __name__ == "__main__":
    sys.exit(main())
