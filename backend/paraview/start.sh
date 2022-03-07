#!/bin/bash

while true; do

    /home/paraview/package/bin/pvserver --multi-clients --use-offscreen-rendering && wait

done
