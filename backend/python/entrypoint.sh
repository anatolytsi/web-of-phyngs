#!/bin/sh

chown -R foam:appgroup /wop/cases
exec runuser -u foam "$@"
