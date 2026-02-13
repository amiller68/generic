# Use node-20 as a base -- this should match our node version in our
#  package.json
FROM node:20-alpine AS base
# Set your Vite service name
ARG SERVICE_NAME=web
# Enable and set up PNPM
RUN corepack enable && corepack prepare pnpm@latest --activate
# 1. prune phase
FROM base AS pruner
# install deps
RUN apk update
RUN apk add --no-cache libc6-compat
WORKDIR /app
RUN npm i -g turbo@^2
# copy over the ts monorepo (sans .dockerignore matches)
COPY ts/ .
# generate the pruned artifacts required to build the example service
RUN turbo prune ${SERVICE_NAME} --docker
# 2. install + build phase
FROM base AS builder
# install deps
RUN apk update
# Install all required dependencies for building the canvas package
RUN apk add --no-cache \
    libc6-compat 
RUN npm i -g turbo@^2
# declare a workdir (where we run commands / copy resources)
WORKDIR /app
# copy pruned dependency artifacts from the pruner
#  this details everything regarding what packages we need / versions for same
COPY --from=pruner /app/out/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=pruner /app/out/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=pruner /app/out/json/ .
# copy .pnpmfile.cjs to ensure lockfile checksum matches
COPY --from=pruner /app/.pnpmfile.cjs ./.pnpmfile.cjs
# install dependencies
RUN pnpm install --frozen-lockfile
# copy pruned source code to from the pruner
COPY --from=pruner /app/out/full/ .
# Build the example app with its dependencies
RUN turbo run build --filter=${SERVICE_NAME}...
# Output the Vite build for debugging
RUN ls -la /app/apps/${SERVICE_NAME}/dist/

# 3. Switch to Nginx to serve static files
FROM nginx:alpine

# Copy the static build output from the builder stage
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html

# Create a separate Nginx config file
RUN mkdir -p /etc/nginx/templates

# Copy nginx.conf (created at build time)
COPY ts/apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
