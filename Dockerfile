###GMTSSAR and ANACO

FROM ubuntu:22.04

#FROM continuumio/anaconda3

RUN mkdir /home/software/


#COPY /data /home/data/
COPY /Copphil-local/ /home/software/Copphil-local/


WORKDIR /home
# Grant permissions to both Copphil-local and STAMPS_ITC
RUN chmod -R 755 /home/software/Copphil-local

WORKDIR /software

RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone

RUN apt-get update && apt-get install -y \
    apt-utils\
    ghostscript\
    nano\
    rsync\
    git\
    vim\
    wget\
    sudo\
    pip\
    build-essential\
    csh\
    subversion\
    autoconf\
    libtiff5-dev\
    libhdf5-dev\
    liblapack-dev\
    libgmt-dev\
    gfortran\
    g++\
    triangle-bin\
    libxt6\
    gmt-dcw\
    gmt-gshhg\
    gmt\
    curl\
    bc

ENV HOME="/home"

####
RUN wget https://github.com/conda-forge/miniforge/releases/download/24.7.1-0/Miniforge-pypy3-Linux-x86_64.sh

RUN bash Miniforge-pypy3-Linux-x86_64.sh -b -p /home/miniforge/


ENV PATH=/home/miniforge/bin:"$PATH"

RUN conda config --add channels conda-forge


RUN conda init bash \
    && . ~/.bashrc \
    && conda create --name gmtsar_python python==3.12.3 \
    && conda activate gmtsar_python \
    && conda install gdal==3.8.5\
    && conda install numpy==1.26.4\
    && conda install matplotlib==3.8.4\ 
    && pip install netCDF4 shapely lxml pyproj scipy geojson PyQt5==5.15.9 pandas geopandas tqdm networkx concave_hull elevation scikit-learn kml2geojson awscli boto3 burst2safe fiona rasterio xarray




ENV PATH=/home/miniforge/envs/gmtsar_python/bin:"$PATH"

RUN conda init bash \
    && . ~/.bashrc \
    && conda activate gmtsar_python


#####
WORKDIR /home/software/
RUN git clone --branch 6.6 https://github.com/gmtsar/gmtsar GMTSAR
WORKDIR GMTSAR
RUN autoconf
RUN autoupdate
RUN ./configure CFLAGS='-z muldefs' LDFLAGS='-z muldefs'
RUN make
RUN make install


#####    
WORKDIR /software
RUN git clone https://github.com/scottstanie/sentineleof 
RUN pip install sentineleof

ENV GMTSAR_HOME=/home/software/GMTSAR
ENV PATH=$GMTSAR_HOME:$GMTSAR_HOME/bin:"$PATH"


ENV gInSAR="/home/software/Copphil-local/pSAR/gInSAR"
ENV S1A_InSAR="/home/software/Copphil-local/pSAR/S1A_InSAR"


ENV SRTM_HOME="/home/software/Copphil-local/DEM/SRTM"
ENV COPDEM_HOME="/home/software/Copphil-local/DEM/COPDEM"

ENV S1_ORB="/home/software/Copphil-local/S1_ORB"

ENV MY_SCR="/home/software/Copphil-local/pSAR/MY_SCR"
ENV MY_BIN="/home/software/Copphil-local/pSAR/MY_BIN"
ENV gmtsar2stamps="/home/software/Copphil-local/pSAR/gmtsar2stamps"


ENV PATH=${PATH}:$gInSAR:$S1A_InSAR:$MY_SCR:$MY_BIN:$gmtsar2stamps:$COPDEM_HOME:$SRTM_HOME:$S1_ORB

ENV PYTHONPATH=${PYTHONPATH}:/home/software/Copphil-local/pSAR/PYTHONPATH


RUN mkdir /home/process/

ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*




RUN echo "machine dataspace.copernicus.eu\n\
  login libingquan13@163.com\n\
  password LBQlbq8454710000?\n\
 machine urs.earthdata.nasa.gov\n\
  login libingquan13\n\
  password LBQlbq84547100" > ~/.netrc

RUN chmod -R +x /home/software/Copphil-local/
RUN chmod 600 ~/.netrc

WORKDIR /home/process

#sudo docker build --rm -t insar_local:v1 .
#sudo docker run -it -v /mnt/Test:/home/process insar_local:v1 /bin/bash


