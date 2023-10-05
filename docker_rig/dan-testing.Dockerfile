# syntax = docker/dockerfile:1.3

# https://hub.docker.com/_/rust
ARG RUST_VERSION=1.72

# Node Version
ARG NODE_MAJOR=20

# rust source compile with cross platform build support
FROM --platform=$BUILDPLATFORM rust:$RUST_VERSION-bullseye as builder-tari

# Declare to make available
ARG BUILDPLATFORM
ARG BUILDOS
ARG BUILDARCH
ARG BUILDVARIANT
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
ARG RUST_TOOLCHAIN
ARG RUST_TARGET
ARG RUST_VERSION

ARG DAN_TESTING_WEBUI_PORT

# Node Version
ARG NODE_MAJOR
ENV NODE_MAJOR=$NODE_MAJOR

# Prep nodejs lts - 20.x
RUN apt-get update && apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      gpg && \
      mkdir -p /etc/apt/keyrings && \
      curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
      echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

RUN apt-get update && apt-get install -y \
      libreadline-dev \
      libsqlite3-0 \
      openssl \
      cargo \
      clang \
      gcc-aarch64-linux-gnu \
      g++-aarch64-linux-gnu \
      cmake \
      nodejs \
      python3-grpc-tools

ARG ARCH=native
#ARG FEATURES=avx2
ARG FEATURES=safe
ENV RUSTFLAGS="-C target_cpu=$ARCH"
ENV ROARING_ARCH=$ARCH
ENV CARGO_HTTP_MULTIPLEXING=false

ARG VERSION=0.0.1

RUN if [ "${BUILDARCH}" != "${TARGETARCH}" ] && [ "${ARCH}" = "native" ] ; then \
      echo "!! Cross-compile and native ARCH not a good idea !! " ; \
    fi

WORKDIR /tari

ADD tari .
ADD cross-compile-aarch64.sh .

RUN if [ "${TARGETARCH}" = "arm64" ] && [ "${BUILDARCH}" != "${TARGETARCH}" ] ; then \
      # Hardcoded ARM64 envs for cross-compiling - FixMe soon
      # source /tari/cross-compile-aarch64.sh
      . /tari/cross-compile-aarch64.sh ; \
    fi && \
    if [ -n "${RUST_TOOLCHAIN}" ] ; then \
      # Install a non-standard toolchain if it has been requested.
      # By default we use the toolchain specified in rust-toolchain.toml
      rustup toolchain install ${RUST_TOOLCHAIN} --force-non-host ; \
    fi && \
    rustup target list --installed && \
    rustup toolchain list && \
    rustup show && \
    cargo build ${RUST_TARGET} \
      --release --features ${FEATURES} --locked \
      --bin minotari_node \
      --bin minotari_console_wallet \
      --bin minotari_miner && \
    # Copy executable out of the cache so it is available in the runtime image.
    cp -v /tari/target/${BUILD_TARGET}release/minotari_node /usr/local/bin/ && \
    cp -v /tari/target/${BUILD_TARGET}release/minotari_console_wallet /usr/local/bin/ && \
    cp -v /tari/target/${BUILD_TARGET}release/minotari_miner /usr/local/bin/ && \
    echo "Tari Build Done"

RUN mkdir -p "/usr/local/lib/minotari/protos/" && \
    python3 -m grpc_tools.protoc \
      --proto_path /tari/applications/minotari_app_grpc/proto/ \
      --python_out=/usr/local/lib/minotari/protos \
      --grpc_python_out=/usr/local/lib/minotari/protos /tari/applications/minotari_app_grpc/proto/*.proto

# rust source compile with cross platform build support
FROM --platform=$BUILDPLATFORM rust:$RUST_VERSION-bullseye as builder-tari-dan

# Declare to make available
ARG BUILDPLATFORM
ARG BUILDOS
ARG BUILDARCH
ARG BUILDVARIANT
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
ARG RUST_TOOLCHAIN
ARG RUST_TARGET
ARG RUST_VERSION

# Node Version
ARG NODE_MAJOR
ENV NODE_MAJOR=$NODE_MAJOR

# Prep nodejs lts - 20.x
RUN apt-get update && apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      gpg && \
      mkdir -p /etc/apt/keyrings && \
      curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
      echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

RUN apt-get update && apt-get install -y \
      libreadline-dev \
      libsqlite3-0 \
      openssl \
      cargo \
      clang \
      gcc-aarch64-linux-gnu \
      g++-aarch64-linux-gnu \
      cmake \
      nodejs

ARG ARCH=native
ENV RUSTFLAGS="-C target_cpu=$ARCH"
ENV ROARING_ARCH=$ARCH
ENV CARGO_HTTP_MULTIPLEXING=false

RUN if [ "${BUILDARCH}" != "${TARGETARCH}" ] && [ "${ARCH}" = "native" ] ; then \
      echo "!! Cross-compile and native ARCH not a good idea !! " ; \
    fi

WORKDIR /tari-dan

ADD tari-dan .
ADD cross-compile-aarch64.sh .

RUN if [ "${TARGETARCH}" = "arm64" ] && [ "${BUILDARCH}" != "${TARGETARCH}" ] ; then \
      # Hardcoded ARM64 envs for cross-compiling - FixMe soon
      # source /tari-dan/cross-compile-aarch64.sh
      . /tari-dan/cross-compile-aarch64.sh ; \
    fi && \
    if [ -n "${RUST_TOOLCHAIN}" ] ; then \
      # Install a non-standard toolchain if it has been requested.
      # By default we use the toolchain specified in rust-toolchain.toml
      rustup toolchain install ${RUST_TOOLCHAIN} --force-non-host ; \
    fi && \
    cd /tari-dan/applications/tari_indexer_web_ui && \
    npm install react-scripts && \
    npm run build && \
    cd /tari-dan/applications/tari_validator_node_web_ui && \
    npm install react-scripts && \
    npm run build && \
    cd /tari-dan/ && \
#    rustup toolchain install nightly --force-non-host && \
    rustup target add wasm32-unknown-unknown && \
#    rustup target add wasm32-unknown-unknown --toolchain nightly && \
#    rustup default nightly-2022-11-03 && \
    rustup target list --installed && \
    rustup toolchain list && \
    rustup show && \
#    cargo +nightly build ${RUST_TARGET} \
    cargo build ${RUST_TARGET} \
      --release --locked \
      --bin tari_indexer \
      --bin tari_dan_wallet_daemon \
      --bin tari_dan_wallet_cli \
      --bin tari_signaling_server \
      --bin tari_validator_node \
      --bin tari_validator_node_cli && \
    # Copy executable out of the cache so it is available in the runtime image.
    cp -v /tari-dan/target/${BUILD_TARGET}release/tari_indexer /usr/local/bin/ && \
    cp -v /tari-dan/target/${BUILD_TARGET}release/tari_dan_wallet_daemon /usr/local/bin/ && \
    cp -v /tari-dan/target/${BUILD_TARGET}release/tari_dan_wallet_cli /usr/local/bin/ && \
    cp -v /tari-dan/target/${BUILD_TARGET}release/tari_signaling_server /usr/local/bin/ && \
    cp -v /tari-dan/target/${BUILD_TARGET}release/tari_validator_node /usr/local/bin/ && \
    cp -v /tari-dan/target/${BUILD_TARGET}release/tari_validator_node_cli /usr/local/bin/ && \
    echo "Tari Dan Build Done"

# Create runtime base minimal image for the target platform executables
FROM --platform=$TARGETPLATFORM rust:$RUST_VERSION-bullseye as runtime

ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
ARG RUST_VERSION

ARG VERSION

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Node Version
ARG NODE_MAJOR
ENV NODE_MAJOR=$NODE_MAJOR

# Prep nodejs 20.x
RUN apt-get update && apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      gpg && \
      mkdir -p /etc/apt/keyrings && \
      curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
      echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

RUN apt-get update && apt-get --no-install-recommends install -y \
      libreadline8 \
      libreadline-dev \
      libsqlite3-0 \
      openssl \
      nodejs \
      python3-requests \
      python3-grpc-tools \
      python3-psutil \
      python3-pip && \
      pip install jsonrpcserver

RUN rustup target add wasm32-unknown-unknown

RUN rustup toolchain install nightly --force-non-host && \
    rustup target add wasm32-unknown-unknown --toolchain nightly
#    rustup default nightly-2022-11-03

# Debugging
RUN rustup target list --installed && \
    rustup toolchain list && \
    rustup show

RUN groupadd --gid 1000 tari && \
    useradd --create-home --no-log-init --shell /bin/bash \
      --home-dir /home/tari \
      --uid 1000 --gid 1000 tari

ENV dockerfile_target_platform=$TARGETPLATFORM
ENV dockerfile_version=$VERSION
ENV dockerfile_build_platform=$BUILDPLATFORM
ENV rust_version=$RUST_VERSION

# Setup some folder structure
RUN mkdir -p "/home/tari/sources/tari-connector" && \
    mkdir -p "/home/tari/sources/dan-testing/Data" && \
    mkdir -p "/home/tari/sources/tari" && \
    mkdir -p "/home/tari/sources/tari-dan" && \
    mkdir -p "/home/tari/data" && \
    chown -R tari:tari "/home/tari/" && \
    mkdir -p "/usr/local/lib/tari/protos" && \
    ln -vsf "/home/tari/sources/tari-connector/" "/usr/lib/node_modules/tari-connector" && \
    mkdir -p "/usr/local/lib/node_modules" && \
    chown -R tari:tari "/usr/local/lib/node_modules"

USER tari
WORKDIR /home/tari

# Debugging
RUN rustup target list --installed && \
    rustup toolchain list && \
    rustup show

# Move into python due to Cross-compile arm64 on amd64 issue
#RUN cargo install cargo-generate

WORKDIR /home/tari/sources
#ADD --chown=tari:tari tari tari
#ADD --chown=tari:tari tari-dan tari-dan
ADD --chown=tari:tari tari-connector tari-connector
ADD --chown=tari:tari dan-testing dan-testing

WORKDIR /home/tari/sources/tari-connector
RUN npm link

WORKDIR /home/tari/sources/dan-testing
RUN npm link tari-connector

COPY --chown=tari:tari --from=builder-tari /usr/local/lib/minotari/protos /home/tari/sources/dan-testing/protos
COPY --from=builder-tari /usr/local/bin/minotari_* /usr/local/bin/
COPY --from=builder-tari-dan /usr/local/bin/tari_* /usr/local/bin/

ENV DAN_TESTING_WEBUI_PORT=${DAN_TESTING_WEBUI_PORT:-18000}
ENV DAN_TESTING_STEPS_CREATE_ACCOUNT=True
ENV DAN_TESTING_STEPS_RUN_TARI_CONNECTOR_TEST_SITE=True
ENV DAN_TESTING_USE_BINARY_EXECUTABLE=True
ENV DAN_TESTING_DATA_FOLDER=/home/tari/data
ENV TARI_BINS_FOLDER=/usr/local/bin/
ENV TARI_DAN_BINS_FOLDER=/usr/local/bin/
ENV USER=tari
WORKDIR /home/tari/sources/dan-testing
CMD [ "python3", "main.py" ]
#CMD [ "tail", "-f", "/dev/null" ]
