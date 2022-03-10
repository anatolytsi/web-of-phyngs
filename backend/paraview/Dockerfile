FROM kitware/paraviewweb:pvw-v5.7.0-rc2-osmesa

COPY ./config.json /pvw/launcher/config.json

RUN ["/opt/paraviewweb/scripts/addEndpoints.sh", \
  "visualizer", "/opt/paraview/share/paraview-5.6/web/visualizer/www" \
]

ENTRYPOINT ["/opt/paraviewweb/scripts/start.sh"]
