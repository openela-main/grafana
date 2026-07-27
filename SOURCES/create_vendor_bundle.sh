#!/bin/bash -eux
VERSION=$(rpm --specfile ./*.spec --qf '%{VERSION}\n' | head -1)
RELEASE=$(rpm --specfile ./*.spec --qf '%{RELEASE}\n' | head -1 | cut -d. -f1)
CHANGELOGTIME=$(rpm --specfile ./*.spec --qf '%{CHANGELOGTIME}\n' | head -1)
SOURCE_DATE_EPOCH=$((CHANGELOGTIME - CHANGELOGTIME % 86400))

SOURCE_DIR=grafana-$VERSION
SOURCE_TAR=grafana-$VERSION.tar.gz
VENDOR_TAR=grafana-vendor-$VERSION-$RELEASE.tar.xz


## Download and extract source tarball
spectool -g grafana.spec
rm -rf "${SOURCE_DIR}"
tar xf "${SOURCE_TAR}"


## Create vendor bundle
pushd "${SOURCE_DIR}"

# Vendor Go dependencies
patch -p1 --fuzz=0 < ../0004-remove-unused-backend-dependencies.patch
patch -p1 --fuzz=0 < ../0015-update-go-git-version.patch
patch -p1 --fuzz=0 < ../0018-fix-x-net-CVE.patch
patch -p1 --fuzz=0 < ../0019-update-go-billy-version.patch
go mod vendor

# Generate Go files
make gen-go

# Remove unused crypto
rm -r vendor/golang.org/x/crypto/bcrypt
rm -r vendor/golang.org/x/crypto/blowfish
rm -r vendor/golang.org/x/crypto/cast5
rm -r vendor/golang.org/x/crypto/openpgp/elgamal
rm    vendor/golang.org/x/crypto/openpgp/packet/ocfb.go
rm -r vendor/golang.org/x/crypto/pkcs12/internal/rc2

# List bundled dependencies
awk '$2 ~ /^v/ && $4 != "indirect" {print "Provides: bundled(golang(" $1 ")) = " substr($2, 2)}' go.mod | \
    sed -E 's/=(.*)-(.*)-(.*)/=\1-\2.\3/g' > "../${VENDOR_TAR}.manifest"

# Vendor Node.js dependencies
patch -p1 --fuzz=0 < ../0005-remove-unused-frontend-crypto.patch
patch -p1 --fuzz=0 < ../0014-resolve-dompurify-CVE.patch
export HUSKY=0
yarn install --frozen-lockfile

# Remove files with licensing issues
find .yarn -name 'node-notifier' -prune -exec rm -r {} \;
find .yarn -name 'nodemon' -prune -exec rm -r {} \;

# List bundled dependencies
../list_bundled_nodejs_packages.py . >> "../${VENDOR_TAR}.manifest"

popd

# Create tarball
# shellcheck disable=SC2046
XZ_OPT=-9 tar \
    --sort=name \
    --mtime="@${SOURCE_DATE_EPOCH}" --clamp-mtime \
    --owner=0 --group=0 --numeric-owner \
    -cJf "${VENDOR_TAR}" \
    "${SOURCE_DIR}/vendor" \
    $(find "${SOURCE_DIR}" -type f -name wire_gen.go | LC_ALL=C sort) \
    "${SOURCE_DIR}/.pnp.cjs" \
    "${SOURCE_DIR}/.yarn/cache" \
    "${SOURCE_DIR}/.yarn/unplugged"
