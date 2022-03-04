FROM lhofmann/paraview-superbuild:5.6.0-osmesa
USER root

COPY ./start.sh /server_files/start.sh
RUN sed -i 's/\r$//g' /server_files/start.sh
RUN chmod +x /server_files/start.sh

# Set work directory
WORKDIR /wop/cases

CMD ['/server_files/start.sh']

USER paraview
