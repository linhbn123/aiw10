# FIXME use alpine to reduce the size of the image
# We hit 'standard_init_linux.go:228: exec user process caused: no such file or directory'
# when running a container built from an alpine image
FROM python:3.8

RUN apt update

# Install curl
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install docker client
# Use the same version as the one being used in docker host
# The docker container will then needs to be launched with -v /var/run/docker.sock:/var/run/docker.sock to share dockerd
# with the host
ENV DOCKER_CHANNEL stable
ENV DOCKER_VERSION 19.03.12
ENV DOCKER_API_VERSION 1.40
RUN curl -fsSL "https://download.docker.com/linux/static/${DOCKER_CHANNEL}/x86_64/docker-${DOCKER_VERSION}.tgz" \
  | tar -xzC /usr/local/bin --strip=1 docker/docker

# Install packages
RUN pip install --no-cache-dir pipenv

# Define working directory and adding source code
WORKDIR /usr/src/app
COPY Pipfile Pipfile.lock bootstrap.sh ./
COPY api ./api

# Install API dependencies
RUN pipenv install
RUN ls

# Start app
EXPOSE 5000
ENTRYPOINT ["/usr/src/app/bootstrap.sh"]
