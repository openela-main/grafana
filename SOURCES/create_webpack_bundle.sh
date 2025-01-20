#!/bin/bash -eux
VERSION=$(rpm --specfile ./*.spec --qf '%{VERSION}\n' | head -1)
RELEASE=$(rpm --specfile ./*.spec --qf '%{RELEASE}\n' | head -1 | cut -d. -f1)
CHANGELOGTIME=$(rpm --specfile ./*.spec --qf '%{CHANGELOGTIME}\n' | head -1)
SOURCE_DATE_EPOCH=$((CHANGELOGTIME - CHANGELOGTIME % 86400))

SOURCE_DIR=grafana-$VERSION
SOURCE_TAR=grafana-$VERSION.tar.gz
VENDOR_TAR=grafana-vendor-$VERSION-$RELEASE.tar.xz
WEBPACK_TAR=grafana-webpack-$VERSION-$RELEASE.tar.gz


## Download and extract source tarball
spectool -g grafana.spec
rm -rf "${SOURCE_DIR}"
tar xf "${SOURCE_TAR}"

## Create vendor bundle
pushd "${SOURCE_DIR}"

# Vendor Node.js dependencies
patch -p1 --fuzz=0 < ../0005-remove-unused-frontend-crypto.patch
patch -p1 --fuzz=0 < ../0014-resolve-dompurify-CVE.patch
export HUSKY=0
yarn install --frozen-lockfile

# Remove files with licensing issues
find .yarn -name 'node-notifier' -prune -exec rm -r {} \;
find .yarn -name 'nodemon' -prune -exec rm -r {} \;

popd


## Create webpack
pushd "${SOURCE_DIR}"
../build_frontend.sh
popd

# Create tarball
tar \
    --sort=name \
    --mtime="@${SOURCE_DATE_EPOCH}" --clamp-mtime \
    --owner=0 --group=0 --numeric-owner \
    -czf "${WEBPACK_TAR}" \
    "${SOURCE_DIR}/plugins-bundled" \
    "${SOURCE_DIR}/public/build" \
    "${SOURCE_DIR}/public/img" \
    "${SOURCE_DIR}/public/lib" \
    "${SOURCE_DIR}/public/locales" \
    "${SOURCE_DIR}/public/views"
