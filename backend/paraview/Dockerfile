FROM lhofmann/paraview-superbuild:5.6.0-osmesa
USER root

RUN apt-get update \
    && apt-get install -y bzip2 wget make gcc vim \
    && apt-get install -y openmpi-bin openmpi-common libopenmpi-dev \
    && apt-get install -y libblas-dev liblapack-dev \
    && apt-get install -y libatlas-dev libatlas-base-dev libatlas3-base \
    && apt-get clean autoclean \
    && apt-get autoremove -y

ARG OPENMPI_VERSION=${OPENMPI_VERSION:-3.0.0}
RUN wget --no-check-certificate https://www.open-mpi.org/software/ompi/v3.0/downloads/openmpi-${OPENMPI_VERSION}.tar.gz && \
    tar xvzf openmpi-${OPENMPI_VERSION}.tar.gz && \
    cd openmpi-${OPENMPI_VERSION} && \
    CFLAGS=-O3 CXXFLAGS=-O3 ./configure --prefix=/usr --sysconfdir=/mnt/0 --disable-pyt-support && \
    make -j8 install

COPY ./start.sh /start.sh
RUN sed -i "s/\r$//g" /start.sh
RUN chmod +x /start.sh
CMD ["/bin/bash", "/start.sh"]

# Set work directory
WORKDIR /wop/cases

USER paraview
