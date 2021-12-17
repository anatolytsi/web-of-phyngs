FROM node:17

# Install any extra things that might be need
RUN echo -e "\n\n\n********** Installing NodeJS dependencies **********\n\n\n" && \
    apt-get update

# Copy data
WORKDIR /app
RUN chmod 777 /app
COPY . ./

# Install project dependencies
RUN echo -e "\n\n\n********** Installing NodeJS project dependencies **********\n\n\n" && \
    npm install

# Build NodeJS
RUN echo -e "\n\n\n********** Building NodeJS project **********\n\n\n" && \
    npm run build

# Run workaround
RUN node workaround.js