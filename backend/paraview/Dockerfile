FROM kitware/trame:1.2-glvnd-runtime-ubuntu20.04-py39

# Install ParaView-OSMesa
ARG PV_URL=https://www.paraview.org/files/v5.10/ParaView-5.10.0-osmesa-MPI-Linux-Python3.9-x86_64.tar.gz
RUN mkdir -p /opt/paraview && cd /opt/paraview && wget -qO- $PV_URL | tar --strip-components=1 -xzv

COPY ./start.sh ./start.sh

ENTRYPOINT ["/start.sh"]
