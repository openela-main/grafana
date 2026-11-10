#!/bin/bash -eu

# Webpack needs more than the default 4GB RAM
export NODE_OPTIONS="${NODE_OPTIONS:-} --max_old_space_size=6144"

# Build the frontend
yarn run build

# Fix permissions (webpack sometimes outputs files with mode = 666 due to reasons unknown (race condition/umask issue afaics))
chmod -R g-w,o-w public/build
