#!/bin/bash
echo "Executing '$@'"
source /opt/openfoam7/etc/bashrc
exec "$@"
