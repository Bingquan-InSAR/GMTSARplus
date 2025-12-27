## Step 0. Software installation

Two installation options are provided:

- **Option 1**: Automatic installation using a pre-configured Docker environment
- **Option 2 (recommended)**: Install the software by **following the Dockerfile provided in this repository**

---

### Option 1: Automatic installation (Docker image)

A Docker image can be built directly from the provided `Dockerfile`, which encapsulates GMTSARPlus and all required dependencies (e.g., GMT, GDAL, NetCDF).

Build the Docker image:

```bash
sudo docker build --rm -t insar_itc:v1 .
```

Run the container with a mounted working directory:

```bash
sudo docker run -it -v /mnt/ESA:/home/process insar_itc:v1 /bin/bash
```

Once inside the container, the processing environment is ready for use.

---

### Option 2 (recommended): Installation via Dockerfile

Users are **strongly encouraged** to install the software by following the `Dockerfile` provided in this repository.

The `Dockerfile` defines the complete software stack and installation order, and ensures:

- Consistent and reproducible environments  
- No dependency conflicts across operating systems  
- Identical behavior across different machines and platforms  

When using this option, please follow the Dockerfile **step by step (top to bottom)** and install the required dependencies on the host system in the same order.
