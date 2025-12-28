## Step 0. Software installation

Two installation options are provided:

- **Option 1 (recommended)**: Automatic installation using a pre-configured Docker environment  
- **Option 2**: Manual installation by following the provided `Dockerfile` step by step  

---

### Option 1 (recommended): Automatic installation (Docker image)

The recommended approach is to build and run the Docker image defined by the provided `Dockerfile`.  
This image encapsulates **GMTSARPlus** and all required dependencies (e.g., GMT, GDAL, NetCDF), ensuring a fully reproducible environment.

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

Once inside the container, the processing environment is fully configured and ready for use.

---

### Option 2: Manual installation by following the Dockerfile (step-by-step)

If you cannot (or prefer not to) run the Docker container directly, you may **manually install the software stack on your host system** by using the provided `Dockerfile` as a **build recipe**.

The `Dockerfile` explicitly defines the complete software stack and the exact installation order, which helps ensure:

- A consistent and reproducible environment  
- Reduced dependency and version conflicts across operating systems  
- Comparable behavior across different machines and platforms  

**How to use this option**

- Open the `Dockerfile` and follow it **from top to bottom**.
- Execute each installation command on your host system **in the same order** as specified.
- Use the same software versions and environment settings (e.g., system packages, conda/pip dependencies, environment variables).

> **Note**: In this option, the Dockerfile serves as documentation for the installation procedure; the container itself is not built or executed.
