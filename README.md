# InSAR Time Series Tool with GMTSAR and StaMPS

This repository provides an **InSAR time series processing workflow** based on **GMTSAR**, optimized for use on a **local workstation**.

---


## 1. [Installation](./installation.md)
## 2. Running GMTSAR+

#### 2.1 Routine workflow `smallbaselineApp.py` ####

MintPy reads a stack of interferograms (unwrapped interferograms, coherence and connected components from SNAPHU if available) and the geometry files (DEM, lookup table, incidence angle, etc.). You need to give the [path to where the files are]and MintPy takes care of the rest!

```bash
smallbaselineApp.py                         # run with default template 'smallbaselineApp.cfg'
smallbaselineApp.py <custom_template>       # run with default and custom templates
smallbaselineApp.py -h / --help             # help
smallbaselineApp.py -H                      # print    default template options
smallbaselineApp.py -g                      # generate default template if it does not exist
smallbaselineApp.py -g <custom_template>    # generate/update default template based on custom template

# Run with --start/stop/dostep options
smallbaselineApp.py GalapagosSenDT128.txt --dostep velocity  # run step 'velocity' only
smallbaselineApp.py GalapagosSenDT128.txt --end load_data    # end run after step 'load_data'
```


## 🚀 1. Configure Data Access Accounts

Before running the workflow, ensure the following accounts are configured with valid credentials in your `.netrc` file:

- `machine urs.earthdata.nasa.gov` – NASA Earthdata
- `machine dataspace.copernicus.eu` – Copernicus Dataspace

---

## ⚙️ 2. Workflow Overview

### Workflow Diagram
![Workflow](https://github.com/Bingquan-InSAR/GMTSAR-X/blob/main/docs/figures/workflow.jpg?raw=true)

---
## 🛰️ 3. Example


  <img src="https://github.com/Bingquan-InSAR/GMTSAR-X/blob/main/docs/figures/Fig1.jpg?raw=true" width="800" />
  <img src="https://github.com/Bingquan-InSAR/GMTSAR-X/blob/main/docs/figures/Fig4.jpg?raw=true" width="800" />



## 📬 4. Contact

Most development discussions take place on GitHub.  
Feel free to [open an issue](https://github.com/Bingquan-InSAR/GMTSAR-X/issues) or comment on any open issue or pull request.

---

## 📚 5. References

- [GMTSAR GitHub Repository](https://github.com/gmtsar/gmtsar)  
- [INSAR_G2S GitHub Repository](https://github.com/dedetmix/INSAR_G2S)

## Acknowledgment
We gratefully acknowledge ESA, PhilSA, and all project members for their contributions.
