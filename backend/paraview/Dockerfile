FROM lhofmann/paraview-superbuild:5.10.0-osmesa
USER root

COPY ./start.sh /start.sh
RUN sed -i "s/\r$//g" /start.sh
RUN chmod +x /start.sh
CMD ["/bin/bash", "/start.sh"]

# Set work directory
WORKDIR /wop/cases

USER paraview
