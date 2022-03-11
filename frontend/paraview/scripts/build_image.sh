#!/usr/bin/env bash
CURRENT_DIR=`dirname "$0"`

cd $CURRENT_DIR/..
DEPLOY_DIR=$PWD
cd frontend
ROOT_DIR=$PWD
cd $DEPLOY_DIR

docker run -it --rm         \
    -e TRAME_BUILD_ONLY=1 \
    -v "$DEPLOY_DIR:/deploy" \
    -v "$ROOT_DIR:/local-app"  \
    kitware/trame:1.2-glvnd-runtime-ubuntu20.04-py39

docker build -t pv-visualizer .
