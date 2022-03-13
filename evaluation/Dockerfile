ARG BASE_URL
ARG MESH_STEP
ARG MAX_CORES
ARG HEATERS
ARG ACS
ARG WINDOWS
ARG DOORS

FROM node:17

# Install any extra things that might be need
RUN echo -e "\n\n\n********** Installing NodeJS dependencies **********\n\n\n" && \
    apt-get update

# Copy data
WORKDIR /app
RUN chmod 777 /app
COPY package.json package-lock.json tsconfig.json ./

# Install project dependencies
RUN echo -e "\n\n\n********** Installing NodeJS project dependencies **********\n\n\n" && \
    npm install

RUN echo "HOST $HOST\n" \
         "MESH_STEP $MESH_STEP\n" \
         "MAX_CORES $MAX_CORES\n" \
         "HEATERS $HEATERS\n" \
         "ACS $ACS\n" \
         "WINDOWS $WINDOWS\n" \
         "DOORS $DOORS\n" > .env

COPY . ./

# Build NodeJS
RUN echo -e "\n\n\n********** Building NodeJS project **********\n\n\n" && \
    npm run build
