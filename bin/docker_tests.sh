#!/bin/bash
docker-compose run --rm api /bin/bash -c \
    "cd tests/data && \
    python3 pytest_waitdb.py && \
    python3 pytest_initdb.py && \
    cd /home/locuszoom-api && \
    pytest tests"

docker-compose down
