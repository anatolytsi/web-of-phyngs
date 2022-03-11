#!/bin/bash

while true; do

    /opt/paraview/bin/mpiexec -np $CORES \
    /opt/paraview/bin/pvserver --multi-clients --force-offscreen-rendering \
    && wait

done
