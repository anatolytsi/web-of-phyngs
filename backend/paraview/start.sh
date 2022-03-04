#!/bin/bash

while true; do

    /home/paraview/package/bin/pvserver --multi-clients --force-offscreen-rendering && wait

done
