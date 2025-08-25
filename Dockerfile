###GMTSSAR and ANACO

FROM ubuntu:22.04

#FROM continuumio/anaconda3

RUN mkdir /home/software/


#COPY /data /home/data/
COPY /GMTSAR_ITC/ /home/software/GMTSAR_ITC/


WORKDIR /home
# Grant permissions to both GMTSAR_ITC and STAMPS_ITC
RUN chmod -R 755 /home/software/GMTSAR_ITC

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
    && pip install netCDF4 shapely lxml pyproj scipy geojson PyQt5==5.15.9 pandas geopandas tqdm networkx concave_hull elevation scikit-learn kml2geojson awscli boto3




ENV PATH=/home/miniforge/envs/gmtsar_python/bin:"$PATH"

RUN conda init bash \
    && . ~/.bashrc \
    && conda activate gmtsar_python


#####
WORKDIR /home/software/
RUN git clone --branch 6.5 https://github.com/gmtsar/gmtsar GMTSAR
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


ENV gInSAR="/home/software/GMTSAR_ITC/pSAR/gInSAR"
ENV S1A_InSAR="/home/software/GMTSAR_ITC/pSAR/S1A_InSAR"


ENV SRTM_HOME="/home/software/GMTSAR_ITC/DEM/SRTM"
ENV COPDEM_HOME="/home/software/GMTSAR_ITC/DEM/COPDEM"

ENV S1_ORB="/home/software/GMTSAR_ITC/S1_ORB"

ENV MY_SCR="/home/software/GMTSAR_ITC/pSAR/MY_SCR"
ENV MY_BIN="/home/software/GMTSAR_ITC/pSAR/MY_BIN"
ENV gmtsar2stamps="/home/software/GMTSAR_ITC/pSAR/gmtsar2stamps"


ENV PATH=${PATH}:$gInSAR:$S1A_InSAR:$MY_SCR:$MY_BIN:$gmtsar2stamps:$COPDEM_HOME:$SRTM_HOME:$S1_ORB

ENV PYTHONPATH=${PYTHONPATH}:/home/software/GMTSAR_ITC/pSAR/PYTHONPATH

# RUN pip install awscli

ENV AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxx
ENV AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxx
ENV AWS_DEFAULT_REGION=us-east-1

RUN mkdir -p /root/.aws && \
    echo "[default]" > /root/.aws/credentials && \
    echo "aws_access_key_id=${AWS_ACCESS_KEY_ID}" >> /root/.aws/credentials && \
    echo "aws_secret_access_key=${AWS_SECRET_ACCESS_KEY}" >> /root/.aws/credentials && \
    echo "[default]" > /root/.aws/config && \
    echo "region=us-east-1" >> /root/.aws/config


RUN mkdir /home/process/

ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*




RUN echo "machine dataspace.copernicus.eu\n\
  login xxxxxxxxxxxxxxxxxxx\n\
  password xxxxxxxxxxxxxxxxxxx\n\
 machine urs.earthdata.nasa.gov\n\
  login xxxxxxxxxxxxxxxxxxx\n\
  password xxxxxxxxxxxxxxxxxxx" > ~/.netrc

RUN chmod -R +x /home/software/GMTSAR_ITC/
RUN chmod 600 ~/.netrc

WORKDIR /home/

#sudo docker build --rm -t insar_itc:v1 .
#sudo docker run -it -v /mnt/ESA:/home/process insar_itc:v1 /bin/bash
#sudo docker run -it -v /mnt/ESA:/home/process dockerhub.copphil.geoville.com/ut/insar_itc:v1 /bin/bash

#aws s3 ls s3://results/Forest/590b9e61-dfa9-4e51-b796-df11c0fa2ce1/ --endpoint-url https://s3.waw3-1.cloudferro.com
#sudo docker build --rm -t dockerhub.copphil.geoville.com/ut/insar_itc:v1 .
#sudo docker login dockerhub.copphil.geoville.com
#sudo docker push dockerhub.copphil.geoville.com/ut/insar_itc:v1
