FROM ubuntu:20.04

# Install any extra things that might be need
RUN apt-get update \
	&& apt-get install -y \
		vim \
		ssh \
		sudo \
		wget \
		software-properties-common ;\
		rm -rf /var/lib/apt/lists/*

# Install ParaView-OSMesa
ARG PV_URL=https://www.paraview.org/files/v5.10/ParaView-5.10.0-osmesa-MPI-Linux-Python3.9-x86_64.tar.gz
RUN mkdir -p /opt/paraview && cd /opt/paraview && wget -qO- $PV_URL | tar --strip-components=1 -xzv

COPY ./start.sh ./opt/paraview/start.sh

ENTRYPOINT ["/opt/paraview/start.sh"]
