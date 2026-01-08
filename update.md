# pSAR in GMTSAR+

GMTSAR+ is developed on top of the open-source GMTSAR package and builds upon existing efforts to automate GMTSAR-based Sentinel-1 TOPS InSAR processing. In particular, the **pSAR package** developed by **Wanpeng Feng** provides well-tested scripts and utilities for Sentinel-1 data preparation and interferogram generation within the GMTSAR framework, and forms an important technical basis for the development of GMTSAR+.

pSAR code repository:
https://github.com/wpfeng/utilities_of_GMTSAR_from_pSAR

In GMTSAR+, **selected pSAR scripts are employed for Sentinel-1A/B/C data preparation and interferogram generation**, while orbit-data retrieval, subsequent SBAS time-series inversion, and standardized product generation are performed within the GMTSAR framework as integrated in GMTSAR+. The pSAR scripts used here have been **further adapted and extended** to improve automation, robustness, and suitability for large-scale processing.

---

## Script Statistics (excluding `.js` and `.png`)

The current script set includes:

| Category  | Number of Scripts |
|----------|-------------------|
| Original | 29 |
| Updated  | 18 |
| Added    | 14 |
| **Total** | **61** |

> Counted file types: `.py`, `.sh`, `.csh`  
> Excluded from the statistics: `.js`, `.png`

---

## Updated Scripts (18)

1. `pSAR_gmtsar_s1.py` — SAFE-directory workflow support (replacing ZIP-based handling), SAFE-compatible parsing utilities, AWS-oriented selection, and improved robustness (e.g., library-path handling).
2. `merge_batch_ps.csh` — PSI-oriented batch merging support.
3. `pSAR_S1select_aws.py` — SAFE-directory Sentinel-1 selection for cloud/mounted archives.
4. `merge_unwrap_geocode_tops_ps.csh` — PSI-oriented merge–unwrap–geocode workflow support.
5. `GMTSAR_s1_createTOPSframes.csh` — robustness improvement for cleanup (`rm -r` → `rm -rf`).
6. `create_merge_input_ps.csh` — PSI-oriented merge-input preparation support.
7. `pSAR_gmtsar_s1insar2roi_aws.py` — SAFE-directory ROI workflow support.
8. `gmtsar_unwrap.py` — updated SNAPHU configuration handling; improved automation (e.g., landmask generation when missing).
9. `GMTSAR_s1_createTOPSframes_burst.csh` — compatibility with burst2safe-style SAFE products.
10. `pSAR_gmtsar_dir2roi_aws.py` — SAFE-directory ROI workflow support.
11. `pSAR_gmtsar_s1_aws.py` — SAFE-directory Sentinel-1 processing entry for cloud/mounted archives.
12. `gmtsar_geocode.csh` — adds trend removal for unwrapped products (`gmt grdtrend ... -Dunwrap_detrended.grd`).
13. `pSAR_gmtsar_baseline2intfin.py` — supports stamps-oriented baseline selection logic.
14. `pSAR_gmtsar_dir2datalist.py` — updated orbit-association interface (including date handling for orbit retrieval).
15. `pSAR_gmtsar_geocode_dir.py` — adds trend removal for unwrapped products (`gmt grdtrend ... -Dunwrap_detrended.grd`).
16. `pSAR_srtmdownload.py` — safer cleanup command (`rm %s -f` → `rm -- %s`).
17. `pSAR_gmtsar_tiff2slcs_paral.py` — ensures intended execution of SLC refinement calls (previously only printed commands).
18. `intf_tops_ps.csh` — PSI-oriented interferogram preparation support.

---

## Original Scripts (29)

- `FWP_preproc_batch_tops_NOesd.csh`
- `FWP_preproc_batch_tops_esd.csh`
- `GMTSAR_proj_ra2ll.csh`
- `gmtsar_filter.csh`
- `gmtsar_intf_tops_notopo.csh`
- `merge2trans.csh`
- `merge_wrap_geocode_tops.csh`
- `pSAR_gmtsar_ashift_median.py`
- `pSAR_gmtsar_dir2baseline.py`
- `pSAR_gmtsar_dir2losvecs.py`
- `pSAR_gmtsar_dir2refineSLCs.py`
- `pSAR_gmtsar_los2projvec.py`
- `pSAR_gmtsar_merge.py`
- `pSAR_gmtsar_merge2unwrap.py`
- `pSAR_gmtsar_raw2baseline.py`
- `pSAR_gmtsar_rawdir2prms.py`
- `pSAR_gmtsar_refineESD.py`
- `pSAR_gmtsar_s1insar2roi.py`
- `pSAR_grabS1orb.py`
- `pSAR_imgformat.py`
- `pSAR_rasterio_fillnodata.py`
- `pSAR_s1zips2orb.py`
- `slc2amp_MUL.csh`
- `gmtsar_intf_tops.csh`
- `gmtsar_merge_redo.py`
- `gmtsar_preproc_batch_tops_esd.csh`
- `merge_batch_only.csh`
- `pSAR_gmtsar_dir2roi.py`
- `pSAR_gmtsar_refineSLC.py`

---

## Added Scripts (14)

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

---

## Acknowledgement (for citation context)

This work acknowledges the development of the **pSAR** package by **Wanpeng Feng**, which provides useful scripts and utilities for GMTSAR-based InSAR processing and has inspired parts of the GMTSAR+ workflow. Users are encouraged to cite the original pSAR repository when appropriate.
