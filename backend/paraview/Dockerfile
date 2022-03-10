FROM kitware/paraviewweb:pvw-v5.7.0-rc2-osmesa

COPY ./config-template.json /opt/launcher/config-template.json

RUN ["/opt/paraviewweb/scripts/addEndpoints.sh", \
  "visualizer", "/opt/paraview/share/paraview-5.6/web/visualizer/www" \
]

COPY ./start.sh /opt/paraviewweb/scripts/

ENTRYPOINT ["/opt/paraviewweb/scripts/start.sh"]
