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

# Apply dependency patches before vendoring
patch -p1 --fuzz=0 < ../0010-update-golang-x-net-to-v0.56.0.patch

# Vendor Go dependencies
go work vendor

# Generate Go files
make gen-go

# Remove unused crypto
rm -r vendor/golang.org/x/crypto/bcrypt
rm -r vendor/golang.org/x/crypto/blowfish
rm -r vendor/golang.org/x/crypto/cast5
rm -r vendor/golang.org/x/crypto/argon2
rm -r vendor/golang.org/x/crypto/blake2b
rm -r vendor/golang.org/x/crypto/chacha20
rm -r vendor/golang.org/x/crypto/chacha20poly1305
rm -r vendor/golang.org/x/crypto/cryptobyte
rm -r vendor/golang.org/x/crypto/curve25519
rm -r vendor/golang.org/x/crypto/hkdf
rm -r vendor/golang.org/x/crypto/internal
rm -r vendor/golang.org/x/crypto/md4
rm -r vendor/golang.org/x/crypto/nacl
rm -r vendor/golang.org/x/crypto/pkcs12
rm -r vendor/golang.org/x/crypto/salsa20
rm -r vendor/golang.org/x/crypto/scrypt
rm -r vendor/golang.org/x/crypto/ripemd160
rm -r vendor/golang.org/x/crypto/sha3
rm -r vendor/golang.org/x/crypto/ssh

# Remove unused code under apsl licenses
rm -r vendor/modernc.org/libc
rm -r vendor/modernc.org/sqlite

# List bundled dependencies
awk '$1 !~ /^\/\// && $2 ~ /^v/ && $4 != "indirect" {print "Provides: bundled(golang(" $1 ")) = " substr($2, 2)}' go.mod | \
    sed -E 's/=(.*)-(.*)-(.*)/=\1-\2.\3/g' > "../${VENDOR_TAR}.manifest"

# Vendor Node.js dependencies
patch -p1 --fuzz=0 < ../0004-remove-unused-frontend-crypto.patch
export HUSKY=0
yarn install --frozen-lockfile

# Remove files with licensing issues
find .yarn -name 'node-notifier' -prune -exec rm -r {} \;
find .yarn -name 'nodemon' -prune -exec rm -r {} \;
rm -rf node_modules/node-notifier node_modules/nodemon

# Remove forbidden Unicode code point
sed -i "s/$(printf '\xe2\x80\xac')//g" node_modules/http2-client/LICENSE

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
    "${SOURCE_DIR}/.yarn/cache" \
    "${SOURCE_DIR}/node_modules"


## Create webpack
pushd "${SOURCE_DIR}"
# Apply frontend source patches before compiling
patch -p1 --fuzz=0 < ../0008-fix-plugin-details-for-versions-not-in-GCOM-registry.patch
patch -p1 --fuzz=0 < ../0009-suppress-signature-warning-for-pcp-plugin.patch
../build_frontend.sh
popd

# Create tarball
# shellcheck disable=SC2046
tar \
    --sort=name \
    --mtime="@${SOURCE_DATE_EPOCH}" --clamp-mtime \
    --owner=0 --group=0 --numeric-owner \
    -czf "${WEBPACK_TAR}" \
    "${SOURCE_DIR}/public/build" \
    "${SOURCE_DIR}/public/img" \
    "${SOURCE_DIR}/public/lib" \
    "${SOURCE_DIR}/public/locales" \
    "${SOURCE_DIR}/public/views" \
    $(find "${SOURCE_DIR}/public/app/plugins" -type d -name "dist" | LC_ALL=C sort)
