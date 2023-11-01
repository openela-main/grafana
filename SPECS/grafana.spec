# gobuild and gotest macros are not available on CentOS Stream
# remove once BZ 1965292 is resolved
# definitions lifted from Fedora 34 podman.spec
%if ! 0%{?gobuild:1}
%define gobuild(o:) GO111MODULE=off go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '-Wl,-z,relro -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld '" -a -v -x %{?**};
%endif
%if ! 0%{?gotest:1}
%define gotest() GO111MODULE=off go test -buildmode pie -compiler gc -ldflags "${LDFLAGS:-} -extldflags '-Wl,-z,relro -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld '" %{?**};
%endif

%global grafana_arches %{lua: go_arches = {}
  for arch in rpm.expand("%{go_arches}"):gmatch("%S+") do
    go_arches[arch] = 1
  end
  for arch in rpm.expand("%{nodejs_arches}"):gmatch("%S+") do
    if go_arches[arch] then
      print(arch .. " ")
  end
end}

# Specify if the frontend will be compiled as part of the build or
# is attached as a webpack tarball (in case of an unsuitable nodejs version on the build system)
%define compile_frontend 0

%if 0%{?rhel}
%define enable_fips_mode 1
%else
%define enable_fips_mode 0
%endif

Name:             grafana
Version:          7.5.15
Release:          5%{?dist}
Summary:          Metrics dashboard and graph editor
License:          ASL 2.0
URL:              https://grafana.org

# Source0 contains the tagged upstream sources
Source0:          https://github.com/grafana/grafana/archive/v%{version}/%{name}-%{version}.tar.gz

# Source1 contains the bundled Go and Node.js dependencies
# Note: In case there were no changes to this tarball, the NVR of this tarball
# lags behind the NVR of this package.
Source1:          grafana-vendor-%{version}-1.tar.xz

%if %{compile_frontend} == 0
# Source2 contains the precompiled frontend
# Note: In case there were no changes to this tarball, the NVR of this tarball
# lags behind the NVR of this package.
Source2:          grafana-webpack-%{version}-1.tar.gz
%endif

# Source3 contains Grafana configuration defaults for distributions
Source3:          distro-defaults.ini

# Source4 contains the Makefile to create the vendor and webpack bundles
Source4:          Makefile

# Source5 contains the script to build the frontend
Source5:          build_frontend.sh

# Source6 contains the script to generate the list of bundled nodejs packages
Source6:          list_bundled_nodejs_packages.py

# Source7 contains the script to create the vendor and webpack bundles in a container
Source7:          create_bundles_in_container.sh

# Patches
Patch1:           001-wrappers-grafana-cli.patch
Patch2:           002-manpages.patch

# resolve symlinks before comparing paths
# BUILD/src/github.com/grafana/grafana -> BUILD/grafana-X.Y.Z
Patch3:           003-fix-dashboard-abspath-test.patch

# Required for s390x
# the golden files include memory dumps from a x86 machine
# integers are stored as little endian on x86, but as big endian on s390x
# therefore loading this memory dump fails on s390x
Patch4:           004-skip-x86-goldenfiles-tests.patch

Patch5:           005-remove-unused-dependencies.patch

Patch6:           006-fix-gtime-test-32bit.patch

Patch8:           008-remove-unused-frontend-crypto.patch

# The Makefile removes a few files with crypto implementations
# from the vendor tarball, which are not used in Grafana.
# This patch removes all references to the deleted files.
Patch9:           009-patch-unused-backend-crypto.patch

# This patch modifies the x/crypto/pbkdf2 function to use OpenSSL
# if FIPS mode is enabled.
Patch10:          010-fips.patch

Patch11:          011-use-hmac-sha-256-for-password-reset-tokens.patch

Patch12:          012-support-go1.18.patch

Patch13:          013-CVE-2021-23648.patch

Patch14:          014-CVE-2022-21698.patch
Patch15:          015-CVE-2022-21698.vendor.patch
Patch16:          016-fix-CVE-2022-31107.patch
Patch17:          017-fix-CVE-2022-39229.patch

# Intersection of go_arches and nodejs_arches
ExclusiveArch:    %{grafana_arches}

BuildRequires:    systemd, golang, go-srpm-macros
%if 0%{?fedora} >= 31
BuildRequires:    go-rpm-macros
%endif

%if %{compile_frontend}
BuildRequires:    nodejs >= 1:14, yarnpkg
%endif

%if %{enable_fips_mode}
BuildRequires:    openssl-devel
%endif

# omit golang debugsource, see BZ995136 and related
%global           dwz_low_mem_die_limit 0
%global           _debugsource_template %{nil}

%global           GRAFANA_USER %{name}
%global           GRAFANA_GROUP %{name}
%global           GRAFANA_HOME %{_datadir}/%{name}

# grafana-server service daemon uses systemd
%{?systemd_requires}
Requires(pre):    shadow-utils

%if 0%{?fedora} || 0%{?rhel} > 7
Recommends: grafana-pcp
%endif

Obsoletes:        grafana-cloudwatch < 7.3.6-1
Obsoletes:        grafana-elasticsearch < 7.3.6-1
Obsoletes:        grafana-azure-monitor < 7.3.6-1
Obsoletes:        grafana-graphite < 7.3.6-1
Obsoletes:        grafana-influxdb < 7.3.6-1
Obsoletes:        grafana-loki < 7.3.6-1
Obsoletes:        grafana-mssql < 7.3.6-1
Obsoletes:        grafana-mysql < 7.3.6-1
Obsoletes:        grafana-opentsdb < 7.3.6-1
Obsoletes:        grafana-postgres < 7.3.6-1
Obsoletes:        grafana-prometheus < 7.3.6-1
Obsoletes:        grafana-stackdriver < 7.3.6-1
Provides:         grafana-cloudwatch = 7.3.6-1
Provides:         grafana-elasticsearch = 7.3.6-1
Provides:         grafana-azure-monitor = 7.3.6-1
Provides:         grafana-graphite = 7.3.6-1
Provides:         grafana-influxdb = 7.3.6-1
Provides:         grafana-loki = 7.3.6-1
Provides:         grafana-mssql = 7.3.6-1
Provides:         grafana-mysql = 7.3.6-1
Provides:         grafana-opentsdb = 7.3.6-1
Provides:         grafana-postgres = 7.3.6-1
Provides:         grafana-prometheus = 7.3.6-1
Provides:         grafana-stackdriver = 7.3.6-1

# vendored golang and node.js build dependencies
# this is for security purposes, if nodejs-foo ever needs an update,
# affected packages can be easily identified.
# Note: generated by the Makefile (see README.md)
Provides: bundled(golang(cloud.google.com/go/storage)) = 1.13.0
Provides: bundled(golang(github.com/BurntSushi/toml)) = 0.3.1
Provides: bundled(golang(github.com/VividCortex/mysqlerr)) = 0.0.0-20170204212430.6c6b55f8796f
Provides: bundled(golang(github.com/aws/aws-sdk-go)) = 1.37.20
Provides: bundled(golang(github.com/beevik/etree)) = 1.1.0
Provides: bundled(golang(github.com/benbjohnson/clock)) = 0.0.0-20161215174838.7dc76406b6d3
Provides: bundled(golang(github.com/bradfitz/gomemcache)) = 0.0.0-20190913173617.a41fca850d0b
Provides: bundled(golang(github.com/centrifugal/centrifuge)) = 0.13.0
Provides: bundled(golang(github.com/cortexproject/cortex)) = 1.4.1-0.20201022071705.85942c5703cf
Provides: bundled(golang(github.com/davecgh/go-spew)) = 1.1.1
Provides: bundled(golang(github.com/denisenkom/go-mssqldb)) = 0.0.0-20200910202707.1e08a3fab204
Provides: bundled(golang(github.com/facebookgo/inject)) = 0.0.0-20180706035515.f23751cae28b
Provides: bundled(golang(github.com/fatih/color)) = 1.10.0
Provides: bundled(golang(github.com/gchaincl/sqlhooks)) = 1.3.0
Provides: bundled(golang(github.com/getsentry/sentry-go)) = 0.10.0
Provides: bundled(golang(github.com/go-macaron/binding)) = 0.0.0-20190806013118.0b4f37bab25b
Provides: bundled(golang(github.com/go-macaron/gzip)) = 0.0.0-20160222043647.cad1c6580a07
Provides: bundled(golang(github.com/go-sourcemap/sourcemap)) = 2.1.3+incompatible
Provides: bundled(golang(github.com/go-sql-driver/mysql)) = 1.5.0
Provides: bundled(golang(github.com/go-stack/stack)) = 1.8.0
Provides: bundled(golang(github.com/gobwas/glob)) = 0.2.3
Provides: bundled(golang(github.com/golang/mock)) = 1.5.0
Provides: bundled(golang(github.com/golang/protobuf)) = 1.4.3
Provides: bundled(golang(github.com/google/go-cmp)) = 0.5.7
Provides: bundled(golang(github.com/google/uuid)) = 1.2.0
Provides: bundled(golang(github.com/gosimple/slug)) = 1.9.0
Provides: bundled(golang(github.com/grafana/grafana-aws-sdk)) = 0.4.0
Provides: bundled(golang(github.com/grafana/grafana-plugin-model)) = 0.0.0-20190930120109.1fc953a61fb4
Provides: bundled(golang(github.com/grafana/grafana-plugin-sdk-go)) = 0.88.0
Provides: bundled(golang(github.com/grafana/loki)) = 1.6.2-0.20201026154740.6978ee5d7387
Provides: bundled(golang(github.com/grpc-ecosystem/go-grpc-middleware)) = 1.2.2
Provides: bundled(golang(github.com/hashicorp/go-hclog)) = 0.15.0
Provides: bundled(golang(github.com/hashicorp/go-plugin)) = 1.4.0
Provides: bundled(golang(github.com/hashicorp/go-version)) = 1.2.1
Provides: bundled(golang(github.com/inconshreveable/log15)) = 0.0.0-20180818164646.67afb5ed74ec
Provides: bundled(golang(github.com/influxdata/influxdb-client-go/v2)) = 2.2.0
Provides: bundled(golang(github.com/jaegertracing/jaeger)) = 1.22.1-0.20210304164023.2fff3ca58910
Provides: bundled(golang(github.com/jmespath/go-jmespath)) = 0.4.0
Provides: bundled(golang(github.com/json-iterator/go)) = 1.1.12
Provides: bundled(golang(github.com/lib/pq)) = 1.9.0
Provides: bundled(golang(github.com/linkedin/goavro/v2)) = 2.10.0
Provides: bundled(golang(github.com/magefile/mage)) = 1.11.0
Provides: bundled(golang(github.com/mattn/go-isatty)) = 0.0.12
Provides: bundled(golang(github.com/mattn/go-sqlite3)) = 1.14.6
Provides: bundled(golang(github.com/mwitkow/go-conntrack)) = 0.0.0-20190716064945.2f068394615f
Provides: bundled(golang(github.com/opentracing/opentracing-go)) = 1.2.0
Provides: bundled(golang(github.com/patrickmn/go-cache)) = 2.1.0+incompatible
Provides: bundled(golang(github.com/pkg/errors)) = 0.9.1
Provides: bundled(golang(github.com/prometheus/client_golang)) = 1.11.1
Provides: bundled(golang(github.com/prometheus/client_model)) = 0.2.0
Provides: bundled(golang(github.com/prometheus/common)) = 0.26.0
Provides: bundled(golang(github.com/robfig/cron)) = 0.0.0-20180505203441.b41be1df6967
Provides: bundled(golang(github.com/robfig/cron/v3)) = 3.0.1
Provides: bundled(golang(github.com/russellhaering/goxmldsig)) = 1.1.0
Provides: bundled(golang(github.com/smartystreets/goconvey)) = 1.6.4
Provides: bundled(golang(github.com/stretchr/testify)) = 1.7.0
Provides: bundled(golang(github.com/teris-io/shortid)) = 0.0.0-20171029131806.771a37caa5cf
Provides: bundled(golang(github.com/timberio/go-datemath)) = 0.1.1-0.20200323150745.74ddef604fff
Provides: bundled(golang(github.com/ua-parser/uap-go)) = 0.0.0-20190826212731.daf92ba38329
Provides: bundled(golang(github.com/uber/jaeger-client-go)) = 2.25.0+incompatible
Provides: bundled(golang(github.com/unknwon/com)) = 1.0.1
Provides: bundled(golang(github.com/urfave/cli/v2)) = 2.3.0
Provides: bundled(golang(github.com/weaveworks/common)) = 0.0.0-20201119133501.0619918236ec
Provides: bundled(golang(github.com/xorcare/pointer)) = 1.1.0
Provides: bundled(golang(github.com/yudai/gojsondiff)) = 1.0.0
Provides: bundled(golang(go.opentelemetry.io/collector)) = 0.21.0
Provides: bundled(golang(golang.org/x/crypto)) = 0.0.0-20201221181555.eec23a3978ad
Provides: bundled(golang(golang.org/x/net)) = 0.0.0-20211015210444.4f30a5c0130f
Provides: bundled(golang(golang.org/x/oauth2)) = 0.0.0-20210113205817.d3ed898aa8a3
Provides: bundled(golang(golang.org/x/sync)) = 0.0.0-20210220032951.036812b2e83c
Provides: bundled(golang(golang.org/x/time)) = 0.0.0-20200630173020.3af7569d3a1e
Provides: bundled(golang(gonum.org/v1/gonum)) = 0.11.0
Provides: bundled(golang(google.golang.org/api)) = 0.40.0
Provides: bundled(golang(google.golang.org/grpc)) = 1.36.0
Provides: bundled(golang(gopkg.in/ini.v1)) = 1.62.0
Provides: bundled(golang(gopkg.in/ldap.v3)) = 3.0.2
Provides: bundled(golang(gopkg.in/macaron.v1)) = 1.4.0
Provides: bundled(golang(gopkg.in/mail.v2)) = 2.3.1
Provides: bundled(golang(gopkg.in/redis.v5)) = 5.2.9
Provides: bundled(golang(gopkg.in/square/go-jose.v2)) = 2.5.1
Provides: bundled(golang(gopkg.in/yaml.v2)) = 2.4.0
Provides: bundled(golang(xorm.io/core)) = 0.7.3
Provides: bundled(golang(xorm.io/xorm)) = 0.8.2
Provides: bundled(npm(@babel/core)) = 7.6.4
Provides: bundled(npm(@babel/core)) = 7.6.4
Provides: bundled(npm(@babel/plugin-proposal-nullish-coalescing-operator)) = 7.8.3
Provides: bundled(npm(@babel/plugin-proposal-optional-chaining)) = 7.8.3
Provides: bundled(npm(@babel/plugin-syntax-dynamic-import)) = 7.7.4
Provides: bundled(npm(@babel/preset-env)) = 7.7.4
Provides: bundled(npm(@babel/preset-env)) = 7.7.4
Provides: bundled(npm(@babel/preset-react)) = 7.8.3
Provides: bundled(npm(@babel/preset-typescript)) = 7.8.3
Provides: bundled(npm(@braintree/sanitize-url)) = 6.0.0
Provides: bundled(npm(@cypress/webpack-preprocessor)) = 4.1.3
Provides: bundled(npm(@emotion/core)) = 10.0.21
Provides: bundled(npm(@emotion/core)) = 10.0.21
Provides: bundled(npm(@grafana/api-documenter)) = 7.11.2
Provides: bundled(npm(@grafana/api-extractor)) = 7.10.1
Provides: bundled(npm(@grafana/aws-sdk)) = 0.0.3
Provides: bundled(npm(@grafana/aws-sdk)) = 0.0.3
Provides: bundled(npm(@grafana/eslint-config)) = 2.3.0
Provides: bundled(npm(@grafana/eslint-config)) = 2.3.0
Provides: bundled(npm(@grafana/slate-react)) = 0.22.9-grafana
Provides: bundled(npm(@grafana/slate-react)) = 0.22.9-grafana
Provides: bundled(npm(@grafana/tsconfig)) = 1.0.0rc1
Provides: bundled(npm(@grafana/tsconfig)) = 1.0.0rc1
Provides: bundled(npm(@grafana/tsconfig)) = 1.0.0rc1
Provides: bundled(npm(@grafana/tsconfig)) = 1.0.0rc1
Provides: bundled(npm(@grafana/tsconfig)) = 1.0.0rc1
Provides: bundled(npm(@grafana/tsconfig)) = 1.0.0rc1
Provides: bundled(npm(@iconscout/react-unicons)) = 1.1.4
Provides: bundled(npm(@mochajs/json-file-reporter)) = 1.2.0
Provides: bundled(npm(@popperjs/core)) = 2.5.4
Provides: bundled(npm(@popperjs/core)) = 2.5.4
Provides: bundled(npm(@reduxjs/toolkit)) = 1.5.0
Provides: bundled(npm(@rollup/plugin-commonjs)) = 16.0.0
Provides: bundled(npm(@rollup/plugin-commonjs)) = 16.0.0
Provides: bundled(npm(@rollup/plugin-commonjs)) = 16.0.0
Provides: bundled(npm(@rollup/plugin-commonjs)) = 16.0.0
Provides: bundled(npm(@rollup/plugin-commonjs)) = 16.0.0
Provides: bundled(npm(@rollup/plugin-image)) = 2.0.5
Provides: bundled(npm(@rollup/plugin-json)) = 4.1.0
Provides: bundled(npm(@rollup/plugin-node-resolve)) = 10.0.0
Provides: bundled(npm(@rollup/plugin-node-resolve)) = 10.0.0
Provides: bundled(npm(@rollup/plugin-node-resolve)) = 10.0.0
Provides: bundled(npm(@rollup/plugin-node-resolve)) = 10.0.0
Provides: bundled(npm(@rollup/plugin-node-resolve)) = 10.0.0
Provides: bundled(npm(@rtsao/plugin-proposal-class-properties)) = 7.0.1-patch.1
Provides: bundled(npm(@sentry/browser)) = 5.25.0
Provides: bundled(npm(@sentry/browser)) = 5.25.0
Provides: bundled(npm(@sentry/types)) = 5.24.2
Provides: bundled(npm(@sentry/utils)) = 5.24.2
Provides: bundled(npm(@storybook/addon-controls)) = 6.1.15
Provides: bundled(npm(@storybook/addon-essentials)) = 6.1.15
Provides: bundled(npm(@storybook/addon-knobs)) = 6.1.15
Provides: bundled(npm(@storybook/addon-storysource)) = 6.1.15
Provides: bundled(npm(@storybook/react)) = 6.1.15
Provides: bundled(npm(@storybook/theming)) = 6.1.15
Provides: bundled(npm(@testing-library/jest-dom)) = 5.11.5
Provides: bundled(npm(@testing-library/jest-dom)) = 5.11.5
Provides: bundled(npm(@testing-library/react)) = 11.1.2
Provides: bundled(npm(@testing-library/react-hooks)) = 3.2.1
Provides: bundled(npm(@testing-library/user-event)) = 12.1.3
Provides: bundled(npm(@torkelo/react-select)) = 3.0.8
Provides: bundled(npm(@torkelo/react-select)) = 3.0.8
Provides: bundled(npm(@types/angular)) = 1.6.56
Provides: bundled(npm(@types/angular-route)) = 1.7.0
Provides: bundled(npm(@types/antlr4)) = 4.7.1
Provides: bundled(npm(@types/classnames)) = 2.2.7
Provides: bundled(npm(@types/classnames)) = 2.2.7
Provides: bundled(npm(@types/classnames)) = 2.2.7
Provides: bundled(npm(@types/clipboard)) = 2.0.1
Provides: bundled(npm(@types/command-exists)) = 1.2.0
Provides: bundled(npm(@types/common-tags)) = 1.8.0
Provides: bundled(npm(@types/common-tags)) = 1.8.0
Provides: bundled(npm(@types/d3)) = 5.7.2
Provides: bundled(npm(@types/d3)) = 5.7.2
Provides: bundled(npm(@types/d3-force)) = 1.2.1
Provides: bundled(npm(@types/d3-interpolate)) = 1.3.1
Provides: bundled(npm(@types/d3-scale-chromatic)) = 1.3.1
Provides: bundled(npm(@types/debounce-promise)) = 3.1.3
Provides: bundled(npm(@types/deep-freeze)) = 0.1.2
Provides: bundled(npm(@types/enzyme)) = 3.10.3
Provides: bundled(npm(@types/enzyme-adapter-react-16)) = 1.0.6
Provides: bundled(npm(@types/expect-puppeteer)) = 3.3.1
Provides: bundled(npm(@types/file-saver)) = 2.0.1
Provides: bundled(npm(@types/fs-extra)) = 8.1.0
Provides: bundled(npm(@types/hoist-non-react-statics)) = 3.3.1
Provides: bundled(npm(@types/hoist-non-react-statics)) = 3.3.1
Provides: bundled(npm(@types/hoist-non-react-statics)) = 3.3.1
Provides: bundled(npm(@types/inquirer)) = 6.5.0
Provides: bundled(npm(@types/is-hotkey)) = 0.1.1
Provides: bundled(npm(@types/jest)) = 26.0.12
Provides: bundled(npm(@types/jest)) = 26.0.12
Provides: bundled(npm(@types/jest)) = 26.0.12
Provides: bundled(npm(@types/jest)) = 26.0.12
Provides: bundled(npm(@types/jest)) = 26.0.12
Provides: bundled(npm(@types/jquery)) = 3.3.38
Provides: bundled(npm(@types/jquery)) = 3.3.38
Provides: bundled(npm(@types/jquery)) = 3.3.38
Provides: bundled(npm(@types/jsurl)) = 1.2.28
Provides: bundled(npm(@types/lodash)) = 4.14.123
Provides: bundled(npm(@types/lodash)) = 4.14.123
Provides: bundled(npm(@types/lodash)) = 4.14.123
Provides: bundled(npm(@types/lodash)) = 4.14.123
Provides: bundled(npm(@types/lru-cache)) = 5.1.0
Provides: bundled(npm(@types/marked)) = 1.1.0
Provides: bundled(npm(@types/md5)) = 2.1.33
Provides: bundled(npm(@types/mock-raf)) = 1.0.2
Provides: bundled(npm(@types/moment)) = 2.13.0
Provides: bundled(npm(@types/moment-timezone)) = 0.5.13
Provides: bundled(npm(@types/mousetrap)) = 1.6.3
Provides: bundled(npm(@types/node)) = 10.14.1
Provides: bundled(npm(@types/node)) = 10.14.1
Provides: bundled(npm(@types/node)) = 10.14.1
Provides: bundled(npm(@types/node)) = 10.14.1
Provides: bundled(npm(@types/node)) = 10.14.1
Provides: bundled(npm(@types/node)) = 10.14.1
Provides: bundled(npm(@types/papaparse)) = 5.2.0
Provides: bundled(npm(@types/papaparse)) = 5.2.0
Provides: bundled(npm(@types/papaparse)) = 5.2.0
Provides: bundled(npm(@types/prettier)) = 1.18.3
Provides: bundled(npm(@types/prismjs)) = 1.16.0
Provides: bundled(npm(@types/puppeteer-core)) = 1.9.0
Provides: bundled(npm(@types/react)) = 16.9.9
Provides: bundled(npm(@types/react)) = 16.9.9
Provides: bundled(npm(@types/react)) = 16.9.9
Provides: bundled(npm(@types/react-beautiful-dnd)) = 12.1.2
Provides: bundled(npm(@types/react-beautiful-dnd)) = 12.1.2
Provides: bundled(npm(@types/react-color)) = 3.0.1
Provides: bundled(npm(@types/react-custom-scrollbars)) = 4.0.5
Provides: bundled(npm(@types/react-dev-utils)) = 9.0.4
Provides: bundled(npm(@types/react-dom)) = 16.9.2
Provides: bundled(npm(@types/react-grid-layout)) = 1.1.1
Provides: bundled(npm(@types/react-icons)) = 2.2.7
Provides: bundled(npm(@types/react-loadable)) = 5.5.2
Provides: bundled(npm(@types/react-redux)) = 7.1.7
Provides: bundled(npm(@types/react-select)) = 3.0.8
Provides: bundled(npm(@types/react-select)) = 3.0.8
Provides: bundled(npm(@types/react-table)) = 7.0.12
Provides: bundled(npm(@types/react-test-renderer)) = 16.9.1
Provides: bundled(npm(@types/react-test-renderer)) = 16.9.1
Provides: bundled(npm(@types/react-transition-group)) = 4.2.3
Provides: bundled(npm(@types/react-transition-group)) = 4.2.3
Provides: bundled(npm(@types/react-virtualized-auto-sizer)) = 1.0.0
Provides: bundled(npm(@types/react-window)) = 1.8.1
Provides: bundled(npm(@types/recompose)) = 0.30.7
Provides: bundled(npm(@types/redux-logger)) = 3.0.7
Provides: bundled(npm(@types/redux-mock-store)) = 1.0.2
Provides: bundled(npm(@types/reselect)) = 2.2.0
Provides: bundled(npm(@types/rimraf)) = 2.0.3
Provides: bundled(npm(@types/rollup-plugin-visualizer)) = 2.6.0
Provides: bundled(npm(@types/rollup-plugin-visualizer)) = 2.6.0
Provides: bundled(npm(@types/rollup-plugin-visualizer)) = 2.6.0
Provides: bundled(npm(@types/rollup-plugin-visualizer)) = 2.6.0
Provides: bundled(npm(@types/rollup-plugin-visualizer)) = 2.6.0
Provides: bundled(npm(@types/semver)) = 6.0.2
Provides: bundled(npm(@types/sinon)) = 7.5.2
Provides: bundled(npm(@types/slate)) = 0.47.1
Provides: bundled(npm(@types/slate)) = 0.47.1
Provides: bundled(npm(@types/slate-plain-serializer)) = 0.6.1
Provides: bundled(npm(@types/slate-react)) = 0.22.5
Provides: bundled(npm(@types/slate-react)) = 0.22.5
Provides: bundled(npm(@types/slate-react)) = 0.22.5
Provides: bundled(npm(@types/systemjs)) = 0.20.6
Provides: bundled(npm(@types/systemjs)) = 0.20.6
Provides: bundled(npm(@types/testing-library__jest-dom)) = 5.9.5
Provides: bundled(npm(@types/testing-library__react-hooks)) = 3.1.0
Provides: bundled(npm(@types/tinycolor2)) = 1.4.1
Provides: bundled(npm(@types/tinycolor2)) = 1.4.1
Provides: bundled(npm(@types/tmp)) = 0.1.0
Provides: bundled(npm(@types/uuid)) = 8.3.0
Provides: bundled(npm(@types/webpack)) = 4.39.3
Provides: bundled(npm(@typescript-eslint/eslint-plugin)) = 4.15.0
Provides: bundled(npm(@typescript-eslint/eslint-plugin)) = 4.15.0
Provides: bundled(npm(@typescript-eslint/parser)) = 4.15.0
Provides: bundled(npm(@typescript-eslint/parser)) = 4.15.0
Provides: bundled(npm(@visx/event)) = 1.3.0
Provides: bundled(npm(@visx/gradient)) = 1.0.0
Provides: bundled(npm(@visx/scale)) = 1.4.0
Provides: bundled(npm(@visx/shape)) = 1.4.0
Provides: bundled(npm(@visx/tooltip)) = 1.3.0
Provides: bundled(npm(@welldone-software/why-did-you-render)) = 4.0.6
Provides: bundled(npm(@wojtekmaj/enzyme-adapter-react-17)) = 0.3.1
Provides: bundled(npm(abortcontroller-polyfill)) = 1.4.0
Provides: bundled(npm(angular)) = 1.8.2
Provides: bundled(npm(angular-bindonce)) = 0.3.1
Provides: bundled(npm(angular-mocks)) = 1.6.6
Provides: bundled(npm(angular-route)) = 1.8.2
Provides: bundled(npm(angular-sanitize)) = 1.8.2
Provides: bundled(npm(antlr4)) = 4.8.0
Provides: bundled(npm(apache-arrow)) = 0.16.0
Provides: bundled(npm(autoprefixer)) = 9.7.4
Provides: bundled(npm(axios)) = 0.21.1
Provides: bundled(npm(axios)) = 0.21.1
Provides: bundled(npm(babel-core)) = 7.0.0-bridge.0
Provides: bundled(npm(babel-jest)) = 26.6.3
Provides: bundled(npm(babel-jest)) = 26.6.3
Provides: bundled(npm(babel-loader)) = 8.0.6
Provides: bundled(npm(babel-loader)) = 8.0.6
Provides: bundled(npm(babel-plugin-angularjs-annotate)) = 0.10.0
Provides: bundled(npm(babel-plugin-angularjs-annotate)) = 0.10.0
Provides: bundled(npm(baron)) = 3.0.3
Provides: bundled(npm(blink-diff)) = 1.0.13
Provides: bundled(npm(brace)) = 0.11.1
Provides: bundled(npm(calculate-size)) = 1.1.1
Provides: bundled(npm(centrifuge)) = 2.6.4
Provides: bundled(npm(chalk)) = 1.1.3
Provides: bundled(npm(chance)) = 1.1.4
Provides: bundled(npm(classnames)) = 2.2.6
Provides: bundled(npm(classnames)) = 2.2.6
Provides: bundled(npm(classnames)) = 2.2.6
Provides: bundled(npm(clean-webpack-plugin)) = 3.0.0
Provides: bundled(npm(clipboard)) = 2.0.4
Provides: bundled(npm(combokeys)) = 3.0.1
Provides: bundled(npm(command-exists)) = 1.2.8
Provides: bundled(npm(commander)) = 2.17.1
Provides: bundled(npm(commander)) = 2.17.1
Provides: bundled(npm(commander)) = 2.17.1
Provides: bundled(npm(common-tags)) = 1.8.0
Provides: bundled(npm(common-tags)) = 1.8.0
Provides: bundled(npm(concurrently)) = 4.1.0
Provides: bundled(npm(copy-to-clipboard)) = 3.3.1
Provides: bundled(npm(copy-webpack-plugin)) = 5.1.2
Provides: bundled(npm(core-js)) = 1.2.7
Provides: bundled(npm(css-loader)) = 3.4.2
Provides: bundled(npm(css-loader)) = 3.4.2
Provides: bundled(npm(cypress)) = 6.3.0
Provides: bundled(npm(cypress-file-upload)) = 4.0.7
Provides: bundled(npm(d3)) = 5.15.0
Provides: bundled(npm(d3)) = 5.15.0
Provides: bundled(npm(d3-force)) = 1.2.1
Provides: bundled(npm(d3-scale-chromatic)) = 1.5.0
Provides: bundled(npm(dangerously-set-html-content)) = 1.0.6
Provides: bundled(npm(debounce-promise)) = 3.1.2
Provides: bundled(npm(deep-freeze)) = 0.0.1
Provides: bundled(npm(emotion)) = 10.0.27
Provides: bundled(npm(emotion)) = 10.0.27
Provides: bundled(npm(emotion)) = 10.0.27
Provides: bundled(npm(enzyme)) = 3.11.0
Provides: bundled(npm(enzyme)) = 3.11.0
Provides: bundled(npm(enzyme-adapter-react-16)) = 1.15.2
Provides: bundled(npm(enzyme-to-json)) = 3.4.4
Provides: bundled(npm(es-abstract)) = 1.18.0-next.1
Provides: bundled(npm(es6-promise)) = 4.2.8
Provides: bundled(npm(es6-shim)) = 0.35.5
Provides: bundled(npm(eslint)) = 2.13.1
Provides: bundled(npm(eslint)) = 2.13.1
Provides: bundled(npm(eslint-config-prettier)) = 7.2.0
Provides: bundled(npm(eslint-config-prettier)) = 7.2.0
Provides: bundled(npm(eslint-plugin-jsdoc)) = 31.6.1
Provides: bundled(npm(eslint-plugin-jsdoc)) = 31.6.1
Provides: bundled(npm(eslint-plugin-no-only-tests)) = 2.4.0
Provides: bundled(npm(eslint-plugin-prettier)) = 3.3.1
Provides: bundled(npm(eslint-plugin-prettier)) = 3.3.1
Provides: bundled(npm(eslint-plugin-react)) = 7.22.0
Provides: bundled(npm(eslint-plugin-react-hooks)) = 4.2.0
Provides: bundled(npm(eslint-plugin-react-hooks)) = 4.2.0
Provides: bundled(npm(eventemitter3)) = 3.1.2
Provides: bundled(npm(eventemitter3)) = 3.1.2
Provides: bundled(npm(execa)) = 0.7.0
Provides: bundled(npm(execa)) = 0.7.0
Provides: bundled(npm(execa)) = 0.7.0
Provides: bundled(npm(expect-puppeteer)) = 4.1.1
Provides: bundled(npm(expect.js)) = 0.3.1
Provides: bundled(npm(expose-loader)) = 0.7.5
Provides: bundled(npm(fast-text-encoding)) = 1.0.0
Provides: bundled(npm(file-loader)) = 5.0.2
Provides: bundled(npm(file-loader)) = 5.0.2
Provides: bundled(npm(file-saver)) = 2.0.2
Provides: bundled(npm(fork-ts-checker-webpack-plugin)) = 1.0.0
Provides: bundled(npm(fork-ts-checker-webpack-plugin)) = 1.0.0
Provides: bundled(npm(fs-extra)) = 0.30.0
Provides: bundled(npm(fuzzy)) = 0.1.3
Provides: bundled(npm(gaze)) = 1.1.3
Provides: bundled(npm(glob)) = 7.1.3
Provides: bundled(npm(globby)) = 6.1.0
Provides: bundled(npm(hoist-non-react-statics)) = 2.5.5
Provides: bundled(npm(hoist-non-react-statics)) = 2.5.5
Provides: bundled(npm(hoist-non-react-statics)) = 2.5.5
Provides: bundled(npm(html-loader)) = 0.5.5
Provides: bundled(npm(html-loader)) = 0.5.5
Provides: bundled(npm(html-webpack-harddisk-plugin)) = 1.0.1
Provides: bundled(npm(html-webpack-plugin)) = 3.2.0
Provides: bundled(npm(html-webpack-plugin)) = 3.2.0
Provides: bundled(npm(husky)) = 4.2.1
Provides: bundled(npm(immutable)) = 3.8.2
Provides: bundled(npm(immutable)) = 3.8.2
Provides: bundled(npm(inquirer)) = 0.12.0
Provides: bundled(npm(is-hotkey)) = 0.1.4
Provides: bundled(npm(jest)) = 26.6.3
Provides: bundled(npm(jest)) = 26.6.3
Provides: bundled(npm(jest-canvas-mock)) = 2.3.0
Provides: bundled(npm(jest-canvas-mock)) = 2.3.0
Provides: bundled(npm(jest-coverage-badges)) = 1.1.2
Provides: bundled(npm(jest-date-mock)) = 1.0.8
Provides: bundled(npm(jest-environment-jsdom-fifteen)) = 1.0.2
Provides: bundled(npm(jest-junit)) = 6.4.0
Provides: bundled(npm(jest-matcher-utils)) = 26.0.0
Provides: bundled(npm(jquery)) = 3.5.1
Provides: bundled(npm(jquery)) = 3.5.1
Provides: bundled(npm(json-markup)) = 1.1.3
Provides: bundled(npm(jsurl)) = 0.1.5
Provides: bundled(npm(lerna)) = 3.22.1
Provides: bundled(npm(less)) = 3.11.1
Provides: bundled(npm(less-loader)) = 5.0.0
Provides: bundled(npm(lint-staged)) = 10.0.7
Provides: bundled(npm(load-grunt-tasks)) = 5.1.0
Provides: bundled(npm(lodash)) = 4.17.21
Provides: bundled(npm(lodash)) = 4.17.21
Provides: bundled(npm(lodash)) = 4.17.21
Provides: bundled(npm(lodash)) = 4.17.21
Provides: bundled(npm(lodash)) = 4.17.21
Provides: bundled(npm(lodash)) = 4.17.21
Provides: bundled(npm(lru-cache)) = 4.1.5
Provides: bundled(npm(lru-memoize)) = 1.1.0
Provides: bundled(npm(marked)) = 2.0.1
Provides: bundled(npm(md5)) = 2.2.1
Provides: bundled(npm(md5-file)) = 4.0.0
Provides: bundled(npm(memoize-one)) = 4.1.0
Provides: bundled(npm(memoize-one)) = 4.1.0
Provides: bundled(npm(mini-css-extract-plugin)) = 0.7.0
Provides: bundled(npm(mini-css-extract-plugin)) = 0.7.0
Provides: bundled(npm(mocha)) = 7.0.1
Provides: bundled(npm(mock-raf)) = 1.0.1
Provides: bundled(npm(module-alias)) = 2.2.2
Provides: bundled(npm(moment)) = 2.24.0
Provides: bundled(npm(moment)) = 2.24.0
Provides: bundled(npm(moment)) = 2.24.0
Provides: bundled(npm(moment-timezone)) = 0.5.28
Provides: bundled(npm(monaco-editor)) = 0.20.0
Provides: bundled(npm(monaco-editor)) = 0.20.0
Provides: bundled(npm(monaco-editor-webpack-plugin)) = 1.9.0
Provides: bundled(npm(mousetrap)) = 1.6.5
Provides: bundled(npm(mousetrap-global-bind)) = 1.1.0
Provides: bundled(npm(mutationobserver-shim)) = 0.3.3
Provides: bundled(npm(ngtemplate-loader)) = 2.0.1
Provides: bundled(npm(nodemon)) = 2.0.2
Provides: bundled(npm(optimize-css-assets-webpack-plugin)) = 5.0.4
Provides: bundled(npm(optimize-css-assets-webpack-plugin)) = 5.0.4
Provides: bundled(npm(ora)) = 4.0.3
Provides: bundled(npm(papaparse)) = 5.3.0
Provides: bundled(npm(papaparse)) = 5.3.0
Provides: bundled(npm(pixelmatch)) = 5.1.0
Provides: bundled(npm(pngjs)) = 2.3.1
Provides: bundled(npm(postcss-browser-reporter)) = 0.6.0
Provides: bundled(npm(postcss-flexbugs-fixes)) = 4.2.0
Provides: bundled(npm(postcss-loader)) = 3.0.0
Provides: bundled(npm(postcss-loader)) = 3.0.0
Provides: bundled(npm(postcss-preset-env)) = 6.7.0
Provides: bundled(npm(postcss-reporter)) = 6.0.1
Provides: bundled(npm(prettier)) = 2.0.5
Provides: bundled(npm(prettier)) = 2.0.5
Provides: bundled(npm(pretty-format)) = 21.2.1
Provides: bundled(npm(pretty-format)) = 21.2.1
Provides: bundled(npm(pretty-format)) = 21.2.1
Provides: bundled(npm(pretty-format)) = 21.2.1
Provides: bundled(npm(prismjs)) = 1.21.0
Provides: bundled(npm(prop-types)) = 15.7.2
Provides: bundled(npm(puppeteer-core)) = 1.18.1
Provides: bundled(npm(rc-cascader)) = 1.0.1
Provides: bundled(npm(rc-cascader)) = 1.0.1
Provides: bundled(npm(rc-drawer)) = 3.1.3
Provides: bundled(npm(rc-slider)) = 9.6.4
Provides: bundled(npm(rc-time-picker)) = 3.7.3
Provides: bundled(npm(re-resizable)) = 6.2.0
Provides: bundled(npm(react)) = 16.13.1
Provides: bundled(npm(react)) = 16.13.1
Provides: bundled(npm(react-beautiful-dnd)) = 13.0.0
Provides: bundled(npm(react-beautiful-dnd)) = 13.0.0
Provides: bundled(npm(react-calendar)) = 2.19.2
Provides: bundled(npm(react-color)) = 2.18.0
Provides: bundled(npm(react-custom-scrollbars)) = 4.2.1
Provides: bundled(npm(react-dev-utils)) = 10.2.1
Provides: bundled(npm(react-docgen-typescript-loader)) = 3.7.2
Provides: bundled(npm(react-dom)) = 17.0.1
Provides: bundled(npm(react-dom)) = 17.0.1
Provides: bundled(npm(react-grid-layout)) = 1.2.0
Provides: bundled(npm(react-highlight-words)) = 0.16.0
Provides: bundled(npm(react-highlight-words)) = 0.16.0
Provides: bundled(npm(react-hook-form)) = 5.1.3
Provides: bundled(npm(react-hot-loader)) = 4.8.0
Provides: bundled(npm(react-icons)) = 2.2.7
Provides: bundled(npm(react-is)) = 16.8.0
Provides: bundled(npm(react-loadable)) = 5.5.0
Provides: bundled(npm(react-monaco-editor)) = 0.36.0
Provides: bundled(npm(react-popper)) = 2.2.4
Provides: bundled(npm(react-popper)) = 2.2.4
Provides: bundled(npm(react-redux)) = 7.2.0
Provides: bundled(npm(react-reverse-portal)) = 2.0.1
Provides: bundled(npm(react-select-event)) = 5.1.0
Provides: bundled(npm(react-sizeme)) = 2.6.12
Provides: bundled(npm(react-split-pane)) = 0.1.89
Provides: bundled(npm(react-storybook-addon-props-combinations)) = 1.1.0
Provides: bundled(npm(react-table)) = 7.0.0
Provides: bundled(npm(react-test-renderer)) = 16.10.2
Provides: bundled(npm(react-test-renderer)) = 16.10.2
Provides: bundled(npm(react-transition-group)) = 4.3.0
Provides: bundled(npm(react-transition-group)) = 4.3.0
Provides: bundled(npm(react-use)) = 13.27.0
Provides: bundled(npm(react-virtualized-auto-sizer)) = 1.0.2
Provides: bundled(npm(react-window)) = 1.8.5
Provides: bundled(npm(recompose)) = 0.25.1
Provides: bundled(npm(redux)) = 3.7.2
Provides: bundled(npm(redux-logger)) = 3.0.6
Provides: bundled(npm(redux-mock-store)) = 1.5.4
Provides: bundled(npm(redux-thunk)) = 2.3.0
Provides: bundled(npm(regenerator-runtime)) = 0.11.1
Provides: bundled(npm(regexp-replace-loader)) = 1.0.1
Provides: bundled(npm(replace-in-file)) = 4.1.3
Provides: bundled(npm(replace-in-file-webpack-plugin)) = 1.0.6
Provides: bundled(npm(reselect)) = 4.0.0
Provides: bundled(npm(resolve-as-bin)) = 2.1.0
Provides: bundled(npm(rimraf)) = 2.6.3
Provides: bundled(npm(rimraf)) = 2.6.3
Provides: bundled(npm(rollup)) = 0.63.5
Provides: bundled(npm(rollup)) = 0.63.5
Provides: bundled(npm(rollup)) = 0.63.5
Provides: bundled(npm(rollup)) = 0.63.5
Provides: bundled(npm(rollup)) = 0.63.5
Provides: bundled(npm(rollup-plugin-copy)) = 3.3.0
Provides: bundled(npm(rollup-plugin-sourcemaps)) = 0.6.3
Provides: bundled(npm(rollup-plugin-sourcemaps)) = 0.6.3
Provides: bundled(npm(rollup-plugin-sourcemaps)) = 0.6.3
Provides: bundled(npm(rollup-plugin-sourcemaps)) = 0.6.3
Provides: bundled(npm(rollup-plugin-sourcemaps)) = 0.6.3
Provides: bundled(npm(rollup-plugin-terser)) = 7.0.2
Provides: bundled(npm(rollup-plugin-terser)) = 7.0.2
Provides: bundled(npm(rollup-plugin-terser)) = 7.0.2
Provides: bundled(npm(rollup-plugin-terser)) = 7.0.2
Provides: bundled(npm(rollup-plugin-terser)) = 7.0.2
Provides: bundled(npm(rollup-plugin-typescript2)) = 0.29.0
Provides: bundled(npm(rollup-plugin-typescript2)) = 0.29.0
Provides: bundled(npm(rollup-plugin-typescript2)) = 0.29.0
Provides: bundled(npm(rollup-plugin-typescript2)) = 0.29.0
Provides: bundled(npm(rollup-plugin-typescript2)) = 0.29.0
Provides: bundled(npm(rollup-plugin-visualizer)) = 4.2.0
Provides: bundled(npm(rollup-plugin-visualizer)) = 4.2.0
Provides: bundled(npm(rollup-plugin-visualizer)) = 4.2.0
Provides: bundled(npm(rollup-plugin-visualizer)) = 4.2.0
Provides: bundled(npm(rollup-plugin-visualizer)) = 4.2.0
Provides: bundled(npm(rst2html)) = 1.0.4
Provides: bundled(npm(rxjs)) = 6.5.5
Provides: bundled(npm(rxjs)) = 6.5.5
Provides: bundled(npm(rxjs-spy)) = 7.5.1
Provides: bundled(npm(sass)) = 1.27.0
Provides: bundled(npm(sass)) = 1.27.0
Provides: bundled(npm(sass-lint)) = 1.12.1
Provides: bundled(npm(sass-loader)) = 8.0.2
Provides: bundled(npm(sass-loader)) = 8.0.2
Provides: bundled(npm(search-query-parser)) = 1.5.4
Provides: bundled(npm(semver)) = 5.7.1
Provides: bundled(npm(simple-git)) = 1.132.0
Provides: bundled(npm(sinon)) = 8.1.1
Provides: bundled(npm(sinon)) = 8.1.1
Provides: bundled(npm(slate)) = 0.47.8
Provides: bundled(npm(slate)) = 0.47.8
Provides: bundled(npm(slate-plain-serializer)) = 0.7.10
Provides: bundled(npm(storybook-dark-mode)) = 1.0.4
Provides: bundled(npm(style-loader)) = 1.1.3
Provides: bundled(npm(style-loader)) = 1.1.3
Provides: bundled(npm(systemjs)) = 0.20.19
Provides: bundled(npm(systemjs-plugin-css)) = 0.1.37
Provides: bundled(npm(terser-webpack-plugin)) = 1.4.5
Provides: bundled(npm(terser-webpack-plugin)) = 1.4.5
Provides: bundled(npm(tether)) = 1.4.7
Provides: bundled(npm(tether-drop)) = 1.5.0
Provides: bundled(npm(tinycolor2)) = 1.4.1
Provides: bundled(npm(tinycolor2)) = 1.4.1
Provides: bundled(npm(tinycolor2)) = 1.4.1
Provides: bundled(npm(ts-jest)) = 26.4.4
Provides: bundled(npm(ts-jest)) = 26.4.4
Provides: bundled(npm(ts-loader)) = 6.2.1
Provides: bundled(npm(ts-loader)) = 6.2.1
Provides: bundled(npm(ts-loader)) = 6.2.1
Provides: bundled(npm(ts-loader)) = 6.2.1
Provides: bundled(npm(ts-node)) = 9.0.0
Provides: bundled(npm(ts-node)) = 9.0.0
Provides: bundled(npm(ts-node)) = 9.0.0
Provides: bundled(npm(tslib)) = 1.10.0
Provides: bundled(npm(tslib)) = 1.10.0
Provides: bundled(npm(tti-polyfill)) = 0.2.2
Provides: bundled(npm(tween-functions)) = 1.2.0
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(typescript)) = 3.9.7
Provides: bundled(npm(uplot)) = 1.6.9
Provides: bundled(npm(url-loader)) = 2.2.0
Provides: bundled(npm(uuid)) = 3.3.3
Provides: bundled(npm(visjs-network)) = 4.25.0
Provides: bundled(npm(webpack)) = 4.41.5
Provides: bundled(npm(webpack)) = 4.41.5
Provides: bundled(npm(webpack-bundle-analyzer)) = 3.6.0
Provides: bundled(npm(webpack-cleanup-plugin)) = 0.5.1
Provides: bundled(npm(webpack-cli)) = 3.3.10
Provides: bundled(npm(webpack-dev-server)) = 3.11.1
Provides: bundled(npm(webpack-filter-warnings-plugin)) = 1.2.1
Provides: bundled(npm(webpack-merge)) = 4.2.2
Provides: bundled(npm(whatwg-fetch)) = 3.0.0
Provides: bundled(npm(xss)) = 1.0.6
Provides: bundled(npm(yaml)) = 1.7.2
Provides: bundled(npm(yaml)) = 1.7.2
Provides: bundled(npm(zone.js)) = 0.7.8


%description
Grafana is an open source, feature rich metrics dashboard and graph editor for
Graphite, InfluxDB & OpenTSDB.


%prep
%setup -q -T -D -b 0
%setup -q -T -D -b 1
%if %{compile_frontend} == 0
# remove bundled plugins source, otherwise they'll get merged
# with the compiled bundled plugins when extracting the webpack
rm -r plugins-bundled
%setup -q -T -D -b 2
%endif

%patch1 -p1
%patch2 -p1
%patch3 -p1
%ifarch s390x
%patch4 -p1
%endif
%patch5 -p1
%patch6 -p1
%patch8 -p1
%patch9 -p1
%if %{enable_fips_mode}
%patch10 -p1
%endif
%if 0%{?fedora} || 0%{?rhel} > 8
%patch11 -p1
%endif
%patch12 -p1
%patch13 -p1
%patch14 -p1
%patch15 -p1
%patch16 -p1
%patch17 -p1

# Set up build subdirs and links
mkdir -p %{_builddir}/src/github.com/grafana
ln -s %{_builddir}/%{name}-%{version} \
    %{_builddir}/src/github.com/grafana/grafana


%build
# Build the frontend
%if %{compile_frontend}
%{SOURCE5}
%endif

# Build the backend
cd %{_builddir}/src/github.com/grafana/grafana
export GOPATH=%{_builddir}

# required since RHEL 8.8 to fix the following error:
# "imports crypto/boring: build constraints exclude all Go files in /usr/lib/golang/src/crypto/boring"
# can be removed in a future Go release
export GOEXPERIMENT=boringcrypto

# see grafana-X.X.X/build.go
export LDFLAGS="-X main.version=%{version} -X main.buildstamp=${SOURCE_DATE_EPOCH}"
for cmd in grafana-cli grafana-server; do
    %gobuild -o %{_builddir}/bin/${cmd} ./pkg/cmd/${cmd}
done


%install
# dirs, shared files, public html, webpack
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_libexecdir}/%{name}
cp -a conf public plugins-bundled %{buildroot}%{_datadir}/%{name}

# wrappers
install -p -m 755 packaging/wrappers/grafana-cli %{buildroot}%{_sbindir}/%{name}-cli

# binaries
install -p -m 755 %{_builddir}/bin/%{name}-server %{buildroot}%{_sbindir}
install -p -m 755 %{_builddir}/bin/%{name}-cli %{buildroot}%{_libexecdir}/%{name}

# man pages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 docs/man/man1/* %{buildroot}%{_mandir}/man1

# config dirs
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_sysconfdir}/%{name}/provisioning
install -d %{buildroot}%{_sysconfdir}/%{name}/provisioning/dashboards
install -d %{buildroot}%{_sysconfdir}/%{name}/provisioning/datasources
install -d %{buildroot}%{_sysconfdir}/%{name}/provisioning/notifiers
install -d %{buildroot}%{_sysconfdir}/%{name}/provisioning/plugins
install -d %{buildroot}%{_sysconfdir}/sysconfig

# config defaults
install -p -m 640 %{SOURCE3} %{buildroot}%{_sysconfdir}/%{name}/grafana.ini
install -p -m 640 conf/ldap.toml %{buildroot}%{_sysconfdir}/%{name}/ldap.toml
install -p -m 644 %{SOURCE3} %{buildroot}%{_datadir}/%{name}/conf/defaults.ini
install -p -m 644 packaging/rpm/sysconfig/grafana-server \
    %{buildroot}%{_sysconfdir}/sysconfig/grafana-server

# config database directory and plugins
install -d -m 750 %{buildroot}%{_sharedstatedir}/%{name}
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{name}/plugins

# log directory
install -d %{buildroot}%{_localstatedir}/log/%{name}

# systemd service files
install -d %{buildroot}%{_unitdir} # only needed for manual rpmbuilds
install -p -m 644 packaging/rpm/systemd/grafana-server.service \
    %{buildroot}%{_unitdir}

# daemon run pid file config for using tmpfs
install -d %{buildroot}%{_tmpfilesdir}
echo "d %{_rundir}/%{name} 0755 %{GRAFANA_USER} %{GRAFANA_GROUP} -" \
    > %{buildroot}%{_tmpfilesdir}/%{name}.conf

%pre
getent group %{GRAFANA_GROUP} >/dev/null || groupadd -r %{GRAFANA_GROUP}
getent passwd %{GRAFANA_USER} >/dev/null || \
    useradd -r -g %{GRAFANA_GROUP} -d %{GRAFANA_HOME} -s /sbin/nologin \
    -c "%{GRAFANA_USER} user account" %{GRAFANA_USER}
exit 0

%preun
%systemd_preun grafana-server.service

%post
%systemd_post grafana-server.service
# create grafana.db with secure permissions on new installations
# otherwise grafana-server is creating grafana.db on first start
# with world-readable permissions, which may leak encrypted datasource
# passwords to all users (if the secret_key in grafana.ini was not changed)

# https://bugzilla.redhat.com/show_bug.cgi?id=1805472
if [ "$1" = 1 ] && [ ! -f %{_sharedstatedir}/%{name}/grafana.db ]; then
    touch %{_sharedstatedir}/%{name}/grafana.db
fi

# apply secure permissions to grafana.db if it exists
# (may not exist on upgrades, because users can choose between sqlite/mysql/postgres)
if [ -f %{_sharedstatedir}/%{name}/grafana.db ]; then
    chown %{GRAFANA_USER}:%{GRAFANA_GROUP} %{_sharedstatedir}/%{name}/grafana.db
    chmod 640 %{_sharedstatedir}/%{name}/grafana.db
fi

# required for upgrades
chmod 640 %{_sysconfdir}/%{name}/grafana.ini
chmod 640 %{_sysconfdir}/%{name}/ldap.toml

%postun
%systemd_postun_with_restart grafana-server.service


%check
# Test frontend
%if %{compile_frontend}
node_modules/.bin/jest
%endif

# Test backend
cd %{_builddir}/src/github.com/grafana/grafana
export GOPATH=%{_builddir}

# in setting_test.go there is a unit test which checks if 10 days are 240 hours
# which is usually true except if the dayligt saving time change falls into the last 10 days, then it's either 239 or 241 hours...
# let's set the time zone to a time zone without daylight saving time
export TZ=GMT

# GO111MODULE=on automatically skips vendored macaron sources in pkg/macaron
# GO111MODULE=off doesn't skip them, and fails with an error due to the canoncial import path
rm -r pkg/macaron

# required since RHEL 8.8 to fix the following error:
# "imports crypto/boring: build constraints exclude all Go files in /usr/lib/golang/src/crypto/boring"
# can be removed in a future Go release
export GOEXPERIMENT=boringcrypto

#%gotest "-tags=integration" ./pkg/...

#%if %{enable_fips_mode}
#OPENSSL_FORCE_FIPS_MODE=1 GOLANG_FIPS=1 go test -v ./pkg/util -run TestEncryption
#%endif

%files
# binaries and wrappers
%{_sbindir}/%{name}-server
%{_sbindir}/%{name}-cli
%{_libexecdir}/%{name}

# config files
%config(noreplace) %{_sysconfdir}/sysconfig/grafana-server
%dir %{_sysconfdir}/%{name}
%attr(0755, root, %{GRAFANA_GROUP}) %dir %{_sysconfdir}/%{name}/provisioning
%attr(0755, root, %{GRAFANA_GROUP}) %dir %{_sysconfdir}/%{name}/provisioning/dashboards
%attr(0750, root, %{GRAFANA_GROUP}) %dir %{_sysconfdir}/%{name}/provisioning/datasources
%attr(0755, root, %{GRAFANA_GROUP}) %dir %{_sysconfdir}/%{name}/provisioning/notifiers
%attr(0755, root, %{GRAFANA_GROUP}) %dir %{_sysconfdir}/%{name}/provisioning/plugins
%attr(0640, root, %{GRAFANA_GROUP}) %config(noreplace) %{_sysconfdir}/%{name}/grafana.ini
%attr(0640, root, %{GRAFANA_GROUP}) %config(noreplace) %{_sysconfdir}/%{name}/ldap.toml

# config database directory and plugins
%attr(0750, %{GRAFANA_USER}, %{GRAFANA_GROUP}) %dir %{_sharedstatedir}/%{name}
%attr(-,    %{GRAFANA_USER}, %{GRAFANA_GROUP}) %dir %{_sharedstatedir}/%{name}/plugins

# shared directory and all files therein
%{_datadir}/%{name}
%attr(-, root, %{GRAFANA_GROUP}) %{_datadir}/%{name}/conf/*

# systemd service file
%{_unitdir}/grafana-server.service

# Grafana configuration to dynamically create /run/grafana/grafana.pid on tmpfs
%{_tmpfilesdir}/%{name}.conf

# log directory - grafana.log is created by grafana-server, and it does it's own log rotation
%attr(0755, %{GRAFANA_USER}, %{GRAFANA_GROUP}) %dir %{_localstatedir}/log/%{name}

# man pages for grafana binaries
%{_mandir}/man1/%{name}-server.1*
%{_mandir}/man1/%{name}-cli.1*

# other docs and license
%license LICENSE
%doc CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md GOVERNANCE.md ISSUE_TRIAGE.md MAINTAINERS.md NOTICE.md
%doc PLUGIN_DEV.md README.md ROADMAP.md SECURITY.md SUPPORT.md UPGRADING_DEPENDENCIES.md WORKFLOW.md


%changelog
* Tue Oct 17 2023 Sam Feifer <sfeifer@redhat.com> 7.5.15-5
- resolve RHEL-13284
- resolve CVE-2023-39325 CVE-2023-44487 rapid stream resets can cause excessive work
- testing is turned off due to test failures caused by testing date mismatch

* Mon Oct 31 2022 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.15-4
- resolve CVE-2022-39229 grafana: using email as a username can block other users from signing in
- resolve CVE-2022-27664 golang: net/http: handle server errors after sending GOAWAY
- resolve CVE-2022-41715 golang: regexp/syntax: limit memory used by parsing regexps
- resolve CVE-2022-2880 golang: net/http/httputil: ReverseProxy should not forward unparseable query parameters
- run integration tests in check phase
- update FIPS patch with latest changes in Go packaging

* Wed Aug 10 2022 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.15-3
- resolve CVE-2022-1962 golang: go/parser: stack exhaustion in all Parse* functions
- resolve CVE-2022-1705 golang: net/http: improper sanitization of Transfer-Encoding header
- resolve CVE-2022-32148 golang: net/http/httputil: NewSingleHostReverseProxy - omit X-Forwarded-For not working
- resolve CVE-2022-30631 golang: compress/gzip: stack exhaustion in Reader.Read
- resolve CVE-2022-30630 golang: io/fs: stack exhaustion in Glob
- resolve CVE-2022-30632 golang: path/filepath: stack exhaustion in Glob
- resolve CVE-2022-30635 golang: encoding/gob: stack exhaustion in Decoder.Decode
- resolve CVE-2022-28131 golang: encoding/xml: stack exhaustion in Decoder.Skip
- resolve CVE-2022-30633 golang: encoding/xml: stack exhaustion in Unmarshal

* Wed Jul 20 2022 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.15-2
- resolve CVE-2022-31107 grafana: OAuth account takeover

* Fri Apr 22 2022 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.15-1
- update to 7.5.15 tagged upstream community sources, see CHANGELOG
- resolve CVE-2022-21673 grafana: Forward OAuth Identity Token can allow users to access some data sources
- resolve CVE-2022-21702 grafana: XSS vulnerability in data source handling
- resolve CVE-2022-21703 grafana: CSRF vulnerability can lead to privilege escalation
- resolve CVE-2022-21713 grafana: IDOR vulnerability can lead to information disclosure
- resolve CVE-2021-23648 sanitize-url: XSS
- resolve CVE-2022-21698 prometheus/client_golang: Denial of service using InstrumentHandlerCounter
- declare Node.js dependencies of subpackages
- make vendor and webpack tarballs reproducible

* Thu Dec 16 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.11-2
- resolve CVE-2021-44716 golang: net/http: limit growth of header canonicalization cache
- resolve CVE-2021-43813 grafana: directory traversal vulnerability for *.md files

* Mon Oct 11 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.11-1
- update to 7.5.11 tagged upstream community sources, see CHANGELOG
- resolve CVE-2021-39226

* Thu Sep 30 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.10-1
- update to 7.5.10 tagged upstream community sources, see CHANGELOG

* Mon Aug 16 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.9-3
- rebuild to resolve CVE-2021-34558

* Thu Jul 08 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.9-2
- remove unused dependency property-information
- always include FIPS patch in SRPM

* Fri Jun 25 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.9-1
- update to 7.5.9 tagged upstream community sources, see CHANGELOG

* Mon Jun 21 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.8-1
- update to 7.5.8 tagged upstream community sources, see CHANGELOG
- remove unused dependencies selfsigned, http-signature and gofpdf

* Fri Jun 11 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.7-2
- remove unused cryptographic implementations
- use cryptographic functions from OpenSSL if FIPS mode is enabled

* Tue May 25 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.5.7-1
- update to 7.5.7 tagged upstream community sources, see CHANGELOG

* Fri Jan 22 2021 Andreas Gerstmayr <agerstmayr@redhat.com> 7.3.6-2
- change working dir to $GRAFANA_HOME in grafana-cli wrapper (fixes Red Hat BZ #1916083)
- add pcp-redis-datasource to allow_loading_unsigned_plugins config option

* Mon Dec 21 2020 Andreas Gerstmayr <agerstmayr@redhat.com> 7.3.6-1
- update to 7.3.6 tagged upstream community sources, see CHANGELOG
- remove dependency on SAML (not supported in the open source version of Grafana)

* Wed Nov 25 2020 Andreas Gerstmayr <agerstmayr@redhat.com> 7.3.4-1
- update to 7.3.4 tagged upstream community sources, see CHANGELOG
- bundle golang dependencies
- optionally bundle node.js dependencies and build and test frontend as part of the specfile
- merge all datasources into main grafana package
- change default provisioning path to /etc/grafana/provisioning
- resolve https://bugzilla.redhat.com/show_bug.cgi?id=1843170

* Thu Aug 20 2020 Andreas Gerstmayr <agerstmayr@redhat.com> 6.7.4-3
- apply patch for CVE-2020-13430 also to sources, not only to compiled webpack

* Wed Aug 19 2020 Andreas Gerstmayr <agerstmayr@redhat.com> 6.7.4-2
- security fix for CVE-2020-13430

* Fri Jun 05 2020 Andreas Gerstmayr <agerstmayr@redhat.com> 6.7.4-1
- update to 6.7.4 tagged upstream community sources, see CHANGELOG
- security fix for CVE-2020-13379

* Tue Apr 28 2020 Andreas Gerstmayr <agerstmayr@redhat.com> 6.7.3-1
- update to 6.7.3 tagged upstream community sources, see CHANGELOG
- add scripts to list Go dependencies and bundled npmjs dependencies
- set Grafana version in Grafana UI and grafana-cli --version
- declare README.md as documentation of datasource plugins
- create grafana.db on first installation (fixes RH BZ #1805472)
- change permissions of /var/lib/grafana to 750 (CVE-2020-12458)
- change permissions of /var/lib/grafana/grafana.db to 640 and
  user/group grafana:grafana (CVE-2020-12458)
- change permissions of grafana.ini and ldap.toml to 640 (CVE-2020-12459)

* Wed Feb 26 2020 Mark Goodwin <mgoodwin@redhat.com> 6.6.2-1
- added patch0 to set the version string correctly
- removed patch 004-xerrors.patch, it's now upstream
- added several patches for golang vendored vrs build dep differences
- added patch to move grafana-cli binary to libexec dir
- update to 6.6.2 tagged upstream community sources, see CHANGELOG

* Wed Nov 20 2019 Mark Goodwin <mgoodwin@redhat.com> 6.3.6-1
- add weak depenency on grafana-pcp
- add patch to mute shellcheck SC1090 for grafana-cli
- update to 6.3.6 upstream community sources, see CHANGELOG

* Thu Sep 05 2019 Mark Goodwin <mgoodwin@redhat.com> 6.3.5-1
- drop uaparser patch now it's upstream
- add xerrors patch, see https://github.com/golang/go/issues/32246
- use vendor sources on rawhide until modules are fully supported
- update to latest upstream community sources, see CHANGELOG

* Fri Aug 30 2019 Mark Goodwin <mgoodwin@redhat.com> 6.3.4-1
- include fix for CVE-2019-15043
- add patch for uaparser on 32bit systems
- update to latest upstream community sources, see CHANGELOG

* Wed Jul 31 2019 Mark Goodwin <mgoodwin@redhat.com> 6.2.5-1
- update to latest upstream community sources, see CHANGELOG

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 6.2.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Jun 07 2019 Mark Goodwin <mgoodwin@redhat.com> 6.2.2-1
- split out some datasource plugins to sub-packages
- update to latest upstream community sources, see CHANGELOG

* Wed Jun 05 2019 Mark Goodwin <mgoodwin@redhat.com> 6.2.1-1
- update to latest upstream community sources, see CHANGELOG

* Fri May 24 2019 Mark Goodwin <mgoodwin@redhat.com> 6.2.0-1
- update to latest upstream community sources
- drop a couple of patches

* Wed May 08 2019 Mark Goodwin <mgoodwin@redhat.com> 6.1.6-2
- add conditional unbundle_vendor_sources macro

* Tue Apr 30 2019 Mark Goodwin <mgoodwin@redhat.com> 6.1.6-1
- update to latest upstream stable release 6.1.6, see CHANGELOG
- includes jQuery 3.4.0 security update

* Wed Apr 24 2019 Mark Goodwin <mgoodwin@redhat.com> 6.1.4-1
- update to latest upstream stable release 6.1.4, see CHANGELOG
- use gobuild and gochecks macros, eliminate arch symlinks
- re-enable grafana-debugsource package
- fix GRAFANA_GROUP typo
- fix more modes for brp-mangle-shebangs
- vendor source unbundling now done in prep after patches
- remove all rhel and fedora conditional guff

* Tue Apr 16 2019 Mark Goodwin <mgoodwin@redhat.com> 6.1.3-1
- update to latest upstream stable release 6.1.3, see CHANGELOG
- unbundle all vendor sources, replace with BuildRequires, see
  the long list of blocker BZs linked to BZ#1670656
- BuildRequires go-plugin >= v1.0.0 for grpc_broker (thanks eclipseo)
- tweak make_webpack to no longer use grunt, switch to prod build
- add ExclusiveArch lua script (thanks quantum.analyst)
- move db directory and plugins to /var/lib/grafana
- split out into 6 patches, ready for upstream PRs
- add check to run go tests for gating checks

* Thu Apr 04 2019 Mark Goodwin <mgoodwin@redhat.com> 6.1.0-1
- update to latest upstream stable release 6.1.0, see CHANGELOG

* Thu Mar 21 2019 Mark Goodwin <mgoodwin@redhat.com> 6.0.2-1
- bump to latest upstream stable release 6.0.2-1
- unbundle almost all remaining vendor code, see linked blockers in BZ#1670656

* Fri Mar 15 2019 Mark Goodwin <mgoodwin@redhat.com> 6.0.1-3
- bump to latest upstream stable release 6.0.1-1

* Thu Mar 14 2019 Mark Goodwin <mgoodwin@redhat.com> 6.0.1-2
- unbundle and add BuildRequires for golang-github-rainycape-unidecode-devel

* Thu Mar 07 2019 Mark Goodwin <mgoodwin@redhat.com> 6.0.1-1
- update to v6.0.1 upstream sources, tweak distro config, re-do patch
- simplify make_webpack.sh script (Elliott Sales de Andrade)
- vendor/github.com/go-ldap is now gone, so don't unbundle it

* Thu Mar 07 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-11
- tweak after latest feedback, bump to 5.4.3-11 (BZ 1670656)
- build debuginfo package again
- unbundle BuildRequires for golang-github-hashicorp-version-devel
- remove some unneeded development files
- remove macros from changelog and other rpmlint tweaks

* Fri Feb 22 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-10
- tweak spec for available and unavailable (bundled) golang packages

* Wed Feb 20 2019 Xavier Bachelot <xavier@bachelot.org> 5.4.3-9
- Remove extraneous slash (cosmetic)
- Create directories just before moving stuff in them
- Truncate long lines
- Group all golang stuff
- Simplify BuildRequires/bundled Provides
- Sort BuildRequires/bundled Provides
- Fix bundled go packages Provides

* Fri Feb 15 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-8
- add BuildRequires (and unbundle) vendor sources available in Fedora
- declare Provides for remaining (bundled) vendor go sources
- do not attempt to unbundle anything on RHEL < 7 or Fedora < 28

* Thu Feb 07 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-7
- further refinement for spec doc section from Xavier Bachelot
- disable debug_package to avoid empty debugsourcefiles.list

* Wed Feb 06 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-6
- further refinement following review by Xavier Bachelot

* Tue Feb 05 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-5
- further refinement following review by Xavier Bachelot

* Fri Feb 01 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-4
- further spec updates after packaging review
- reworked post-install scriplets

* Thu Jan 31 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-3
- tweak FHS patch, update spec after packaging review

* Wed Jan 30 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.3-2
- add patch to be standard FHS compliant, remove phantomjs
- update to v5.4.3 upstream community sources

* Wed Jan 09 2019 Mark Goodwin <mgoodwin@redhat.com> 5.4.2-1
- update to v5.4.2 upstream community sources

* Thu Oct 18 2018 Mark Goodwin <mgoodwin@redhat.com> 5.3.1-1
- update to v5.3.1 upstream community sources

* Tue Oct 02 2018 Mark Goodwin <mgoodwin@redhat.com> 5.2.5-1
- native RPM spec build with current tagged v5.2.5 sources
