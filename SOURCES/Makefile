VERSION := $(shell rpm --specfile *.spec --qf '%{VERSION}\n' | head -1)
RELEASE := $(shell rpm --specfile *.spec --qf '%{RELEASE}\n' | head -1 | cut -d. -f1)
CHANGELOGTIME := $(shell rpm --specfile *.spec --qf '%{CHANGELOGTIME}\n' | head -1)
SOURCE_DATE_EPOCH := $(shell echo $$(( $(CHANGELOGTIME) - $(CHANGELOGTIME) % 86400 )))

NAME       := grafana
RPM_NAME   := $(NAME)
SOURCE_DIR := $(NAME)-$(VERSION)
SOURCE_TAR := $(NAME)-$(VERSION).tar.gz
VENDOR_TAR := $(RPM_NAME)-vendor-$(VERSION)-$(RELEASE).tar.xz
WEBPACK_TAR := $(RPM_NAME)-webpack-$(VERSION)-$(RELEASE).tar.gz

# patches which must be applied before creating the vendor tarball, for example:
# - changes in dependency versions
# - changes in Go module imports (which affect the vendored Go modules)
PATCHES_PRE_VENDOR := \
	005-remove-unused-dependencies.patch \
	008-remove-unused-frontend-crypto.patch \
	012-support-go1.18.patch \
	013-CVE-2021-23648.patch \
	014-CVE-2022-21698.patch

# patches which must be applied before creating the webpack, for example:
# - changes in Node.js sources or vendored dependencies
PATCHES_PRE_WEBPACK := \
	008-remove-unused-frontend-crypto.patch


all: $(SOURCE_TAR) $(VENDOR_TAR) $(WEBPACK_TAR)

$(SOURCE_TAR):
	spectool -g $(RPM_NAME).spec

$(VENDOR_TAR): $(SOURCE_TAR)
	# Start with a clean state
	rm -rf $(SOURCE_DIR)
	tar pxf $(SOURCE_TAR)

	# Patches to apply before vendoring
	for patch in $(PATCHES_PRE_VENDOR); do echo applying $$patch ...; patch -d $(SOURCE_DIR) -p1 --fuzz=0 < $$patch; done

	# Go
	cd $(SOURCE_DIR) && go mod vendor -v
	# Remove unused crypto
	rm $(SOURCE_DIR)/vendor/golang.org/x/crypto/cast5/cast5.go
	rm $(SOURCE_DIR)/vendor/golang.org/x/crypto/ed25519/ed25519.go
	rm $(SOURCE_DIR)/vendor/golang.org/x/crypto/ed25519/internal/edwards25519/const.go
	rm $(SOURCE_DIR)/vendor/golang.org/x/crypto/ed25519/internal/edwards25519/edwards25519.go
	rm $(SOURCE_DIR)/vendor/golang.org/x/crypto/openpgp/elgamal/elgamal.go
	rm $(SOURCE_DIR)/vendor/golang.org/x/crypto/openpgp/packet/ocfb.go
	awk '$$2~/^v/ && $$4 != "indirect" {print "Provides: bundled(golang(" $$1 ")) = " substr($$2, 2)}' $(SOURCE_DIR)/go.mod | \
		sed -E 's/=(.*)-(.*)-(.*)/=\1-\2.\3/g' > $@.manifest

	# Node.js
	cd $(SOURCE_DIR) && yarn install --frozen-lockfile
	# Remove files with licensing issues
	find $(SOURCE_DIR) -type d -name 'node-notifier' -prune -exec rm -r {} \;
	find $(SOURCE_DIR) -type d -name 'property-information' -prune -exec rm -r {} \;
	find $(SOURCE_DIR) -type f -name '*.exe' -delete
	rm -r $(SOURCE_DIR)/node_modules/visjs-network/examples
	./list_bundled_nodejs_packages.py $(SOURCE_DIR) >> $@.manifest

	# Create tarball
	XZ_OPT=-9 tar \
		--sort=name \
		--mtime="@$(SOURCE_DATE_EPOCH)" --clamp-mtime \
		--owner=0 --group=0 --numeric-owner \
		-cJf $@ \
		$(SOURCE_DIR)/vendor \
		$$(find $(SOURCE_DIR) -type d -name "node_modules" -prune | LC_ALL=C sort)

$(WEBPACK_TAR): $(VENDOR_TAR)
	# Start with a clean state
	rm -rf $(SOURCE_DIR)
	tar pxf $(SOURCE_TAR)
	tar pxf $(VENDOR_TAR)

	# Patches to apply before creating the webpack
	for patch in $(PATCHES_PRE_WEBPACK); do echo applying $$patch ...; patch -d $(SOURCE_DIR) -p1 --fuzz=0 < $$patch; done

	# Build frontend
	cd $(SOURCE_DIR) && \
		../build_frontend.sh

	# Create tarball
	tar \
		--sort=name \
		--mtime="@$(SOURCE_DATE_EPOCH)" --clamp-mtime \
		--owner=0 --group=0 --numeric-owner \
		-czf $@ \
		$(SOURCE_DIR)/public/build \
		$(SOURCE_DIR)/public/views \
		$(SOURCE_DIR)/plugins-bundled

clean:
	rm -rf *.tar.gz *.tar.xz *.manifest *.rpm $(NAME)-*/
