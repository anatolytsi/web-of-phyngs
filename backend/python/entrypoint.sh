#!/bin/sh

chown -R foam:foam /wop/cases
exec runuser -u foam "$@"
