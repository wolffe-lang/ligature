FROM docker.io/library/ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
# Binary packages only. No linker, binutils or libc source is fetched/built.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential=12.10ubuntu1 binutils=2.42-4ubuntu2.10 lld-17=1:17.0.6-9ubuntu1 musl-dev=1.2.4-2 musl-tools=1.2.4-2 ca-certificates curl python3 && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/ld.lld-17 /usr/local/bin/ld.lld
ENV LC_ALL=C CARGO_INCREMENTAL=0
WORKDIR /work
