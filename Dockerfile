FROM ubuntu:20.04

MAINTAINER Nicolai Spohrer <nicolai@xeve.de>

RUN adduser --quiet --disabled-password qtuser && \
    apt update && \
    DEBIAN_FRONTEND="noninteractive" apt install -y --no-install-recommends \
        python3-pyqt5 \
        wkhtmltopdf \
        xvfb && \
    rm -rf /var/lib/apt/lists/*

COPY . /app/
