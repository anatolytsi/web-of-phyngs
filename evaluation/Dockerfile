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

COPY . ./

# Build NodeJS
RUN echo -e "\n\n\n********** Building NodeJS project **********\n\n\n" && \
    npm run build

ENV BASE_URL $BASE_URL
ENV MESH_STEP $MESH_STEP
ENV MAX_CORES $MAX_CORES
ENV HEATERS $HEATERS
ENV ACS $ACS
ENV WINDOWS $WINDOWS
ENV DOORS $DOORS

