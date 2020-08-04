FROM ubuntu:18.04

LABEL org.label-schema.name="LocusZoom API"
LABEL org.label-schema.description="API for serving data to locuszoom.js instances"
LABEL org.label-schema.vendor="University of Michigan, Center for Statistical Genetics"
LABEL org.label-schema.url="https://github.com/statgen/locuszoom-api"
LABEL org.label-schema.usage="https://portaldev.sph.umich.edu/docs/api/v1/"
LABEL org.label-schema.vcs-url="https://github.com/statgen/locuszoom-api"
LABEL org.label-schema.schema-version="1.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-dev \
    zlib1g-dev \
    liblzma-dev \
    git \
    locales \
  && rm -rf /var/lib/apt/lists/* \
  && locale-gen en_US.UTF-8

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

# Install python dependencies first so docker can cache them
COPY requirements.txt /
RUN pip3 install -r requirements.txt

# Create a group and user to execute as, then drop root
ARG UID
ARG GID
RUN \
  if [ -n "$GID" ]; then \
    addgroup --gid $GID lzapi; \
  else \
    addgroup lzapi; \
  fi && \
  if [ -n "$UID" ]; then \
    adduser --gecos "User for running LocusZoom API as non-root" --shell /bin/bash --disabled-password --uid $UID --ingroup lzapi lzapi; \
  else \
    adduser --gecos "User for running LocusZoom API as non-root" --shell /bin/bash --disabled-password --ingroup lzapi lzapi; \
  fi

COPY --chown=lzapi:lzapi . /home/locuszoom-api
RUN mkdir -p /home/locuszoom-api/logs && chown lzapi:lzapi /home/locuszoom-api/logs
WORKDIR /home/locuszoom-api
RUN pip3 install -e .

# Switch to user
USER lzapi

# Metadata
ARG GIT_SHA
ARG LZAPI_VERSION

LABEL org.label-schema.version=$LZAPI_VERSION
LABEL org.label-schema.vcs-ref=$GIT_SHA
