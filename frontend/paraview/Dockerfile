FROM kitware/trame:1.2-glvnd-runtime-ubuntu20.04-py39

# Create the /deploy directory with trame-user as the owner
RUN install -d -o trame-user -g trame-user /deploy

# Copy the server directory
COPY --chown=trame-user:trame-user ./server /deploy/server
