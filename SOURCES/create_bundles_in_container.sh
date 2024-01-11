#!/bin/bash -eu
#
# create vendor and webpack bundles inside a container for reproducibility
#

cat <<EOF | podman build -t grafana-build -f - .
FROM fedora:35

RUN dnf upgrade -y && \
    dnf install -y rpmdevtools python3-packaging make golang nodejs yarnpkg

WORKDIR /tmp/grafana-build
COPY Makefile grafana.spec *.patch build_frontend.sh list_bundled_nodejs_packages.py .
RUN mkdir bundles
CMD make && mv *.tar.* bundles
EOF

podman run --name grafana-build --replace "$@" grafana-build
podman cp grafana-build:bundles/. .
