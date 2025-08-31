



# InSAR Time Series Tool with GMTSAR and StaMPS  

This repository provides an InSAR time series processing workflow based on GMTSAR and StaMPS, specifically designed for the **local workstation**.  


---

## 🚀 Deployment Instructions  

If you would like to deploy a similar setup for your own project, please note the following:  


### 1. Configure Data Access Accounts

Make sure to configure the following services with valid credentials:

* `machine urs.earthdata.nasa.gov` (NASA Earthdata)
* `machine dataspace.copernicus.eu` (Copernicus Dataspace)

---

### 2. ⚙️ Workflow Overview

This project uses **Nomad** to manage job execution and scheduling:

➡️ User job submission → Nomad scheduling → Docker execution → Result upload

### Workflow Diagram

![Workflow](https://github.com/Bingquan-InSAR/GMTSAR-X/blob/main/docs/figures/workflow.png?raw=true)

---



## 3. Contact us

* Most development discussion happens on GitHub. Feel free to [open an issue](https://github.com/Bingquan-InSAR/GMTSAR-X/issues) or comment on any open issue or pull request.
