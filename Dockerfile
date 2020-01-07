FROM ubuntu:18.04

ARG GIT_SHA
ARG LZAPI_VERSION

LABEL org.label-schema.name="LocusZoom API"
LABEL org.label-schema.version=$LZAPI_VERSION
LABEL org.label-schema.description="API for serving data to locuszoom.js instances"
LABEL org.label-schema.vendor="University of Michigan, Center for Statistical Genetics"
LABEL org.label-schema.url="https://github.com/statgen/locuszoom-api"
LABEL org.label-schema.usage="https://portaldev.sph.umich.edu/docs/api/v1/"
LABEL org.label-schema.vcs-url="https://github.com/statgen/locuszoom-api"
LABEL org.label-schema.vcs-ref=$GIT_SHA
LABEL org.label-schema.schema-version="1.0"

RUN apt-get update && apt-get install -y \
  build-essential \
  cmake \
  python3 \
  python3-pip \
  zlib1g-dev \
  liblzma-dev \
  git

# Install python dependencies first so docker can cache them
COPY requirements.txt /
RUN pip3 install -r requirements.txt

# Create a group and user to execute as, then drop root
RUN adduser --gecos "User for running LocusZoom API as non-root" --shell /bin/bash --disabled-password lzapi

COPY --chown=lzapi:lzapi . /home/locuszoom-api
WORKDIR /home/locuszoom-api
RUN pip3 install -e .

# Declare volume
VOLUME /home/locuszoom-api

# Switch to user
USER lzapi
