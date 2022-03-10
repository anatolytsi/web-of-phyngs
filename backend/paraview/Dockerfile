FROM kitware/paraviewweb:pvw-v5.7.0-rc2-osmesa

RUN mkdir -p /var/run/apache2 && \
    chown -R 999:999 /var/run/apache2* && \
    chown -R 999:999 /var/run/apache2* && \
    chmod -R g+w /var/run/apache2*     && \
    chown -R 999:99 /var/log/apache2
RUN groupadd -g 999 paraview && useradd -o -u 999 -g 999 paraview
COPY ./config-template.json /opt/launcher/config-template.json
COPY ./001-pvw.conf /etc/apache2/sites-available/001-pvw.conf
COPY ./envvars /etc/apache2/
COPY ./ports.conf /etc/apache2
COPY ./start.sh /opt/paraviewweb/scripts/

RUN ["/opt/paraviewweb/scripts/addEndpoints.sh", \
    "visualizer", "/opt/paraview/share/paraview-5.7/web/visualizer/www" \
]

ENTRYPOINT ["/opt/paraviewweb/scripts/start.sh"]
