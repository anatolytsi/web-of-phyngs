#!/bin/bash

while true; do

    /home/paraview/package/bin/pvserver --multi-clients --force-offscreen-rendering && wait
    /home/paraview/package/bin/mpiexec -np $CORES \
    /home/paraview/package/bin/pvserver --multi-clients --force-offscreen-rendering \
    && wait

done
