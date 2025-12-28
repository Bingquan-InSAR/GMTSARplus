## Step 0. Software installation

Two installation options are provided:

- **Option 1**: Automatic installation using a pre-configured Docker environment
- **Option 2 (recommended)**: Install the software by **following the Dockerfile provided in this repository**

---

### Option 1 (recommended): Automatic installation (Docker image)

A Docker image can be built directly from the provided `Dockerfile`, which encapsulates GMTSARPlus and all required dependencies (e.g., GMT, GDAL, NetCDF).

Build the Docker image:

```bash
git clone git@github.com:Bingquan-InSAR/GMTSARplus.git
cd GMTSARplus/
sudo docker build --rm -t insar_itc:v1 .
```

Run the container with a mounted working directory:

```bash
sudo docker run -it -v /mnt/ESA:/home/process insar_itc:v1 /bin/bash
```

Once inside the container, the processing environment is ready for use.

---

### Option 2: Manual installation by following the Dockerfile (step-by-step)

If you cannot (or prefer not to) run the container directly, you can **manually install the toolchain on your host** by using the provided `Dockerfile` as a **build recipe**.

The `Dockerfile` documents the full software stack and the exact installation order, which helps ensure:

- A consistent and reproducible environment  
- Fewer dependency/version conflicts across operating systems  
- Comparable behavior across machines and platforms  

**How to use this option**

- Open the `Dockerfile` and follow it **from top to bottom**.
- Execute the installation commands on your host system **in the same order** as they appear in the Dockerfile.
- Use the same versions and environment settings (e.g., system packages, conda/pip dependencies, environment variables).

