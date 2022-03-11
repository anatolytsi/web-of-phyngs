FROM kitware/trame:1.2-glvnd-runtime-ubuntu20.04-py39

RUN mkdir -p /opt/paraview

RUN chmod +x /opt/paraview
# Needed for PV 5.10.0 but not in 5.10.1
COPY ./setup/trame.py /opt/paraview/lib/python3.9/site-packages/paraview/apps/

# Create the /deploy directory with trame-user as the owner
RUN install -d -o trame-user -g trame-user /deploy

# Copy the server directory
COPY --chown=trame-user:trame-user ./server /deploy/server
