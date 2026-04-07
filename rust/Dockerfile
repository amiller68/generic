# Build stage
FROM rust:1.89-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*

# Copy manifests first for layer caching
COPY rust/Cargo.toml rust/Cargo.lock ./
COPY rust/crates/app/Cargo.toml crates/app/
COPY rust/crates/app/build.rs crates/app/

# Create dummy src for dependency caching
RUN mkdir -p crates/app/src crates/app/bin && \
    echo "fn main() {}" > crates/app/src/main.rs && \
    echo "" > crates/app/src/lib.rs && \
    echo "fn main() {}" > crates/app/bin/seed.rs && \
    mkdir -p crates/app/migrations && \
    cargo build --release 2>/dev/null || true

# Copy real source (templates and static are compiled into the binary)
COPY rust/crates/app/src crates/app/src
COPY rust/crates/app/bin crates/app/bin
COPY rust/crates/app/templates crates/app/templates
COPY rust/crates/app/static crates/app/static
COPY rust/crates/app/migrations crates/app/migrations

# Build for real
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/generic-rust-app /usr/local/bin/generic-rust-app
COPY --from=builder /build/target/release/seed /usr/local/bin/seed

WORKDIR /data

ENV LISTEN_ADDRESS=0.0.0.0:3000
ENV SQLITE_DATABASE_URL=sqlite:///data/app.db
ENV LOG_LEVEL=info

EXPOSE 3000

CMD ["generic-rust-app"]
