# Pulled June 16, 2021
FROM --platform=linux/amd64 python:3.8@sha256:c7706b8d1b1e540b9dd42ac537498d7f3138e4b8b89fb890b2ee4d2c0bccc8ea
RUN pip install --upgrade pip && pip install gunicorn==20.1.0
WORKDIR /srv
COPY gunicorn_conf.py ./
COPY requirements-docker.txt ./
COPY requirements.txt ./
RUN pip install -r requirements-docker.txt
COPY setup.py ./
COPY open_bus_stride_api ./open_bus_stride_api
RUN pip install -e .
ARG VERSION=local-docker
RUN echo "VERSION = '${VERSION}'" > open_bus_stride_api/version.py
ENV SQLALCHEMY_APPLICATION_NAME=api
ENV SQLALCHEMY_APPLICATION_VERSION=${VERSION}
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "open_bus_stride_api.main:app"]
