#!/usr/bin/env bash

usage() {
    cat <<EOF
Usage: $(basename $0) COMMAND [options]

Commands:
    build         Build the docker container
    run           Run the docker container
    push        Deploy the container to REPOSITORY
    help          Show this help message

Build Options:
    -p PLATFORM   Specify platform (e.g., linux/amd64, linux/arm64)
                  Default: host platform

Run Options:
    -p PORT       Specify port mapping (e.g., 8080:80 maps host port 8080 to container port 80)

Deploy Options:
    -S            Skip branch name validation (allows non-main/dev branches)
    -D            Allow pushing from dirty working directory (not allowed for main/dev)
    -L            Also tag unknown branches as staging-latest
    -F            Force push to latest tag (use with caution)

Environment variables required for push (if not using -I):
    DO_TOKEN

Example:
    $(basename $0) build 
    $(basename $0) build -p linux/amd64
    $(basename $0) run -p 8080:80
    $(basename $0) push 

Note:
    Use -p linux/amd64 when building images for deployment.

EOF
    exit 1
}

# Default values for push command
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
SKIP_BRANCH_CHECK=0
ALLOW_DIRTY=0
SERVICE_NAME="app"
TAG_AS_STAGING_LATEST=0
FORCE_LATEST=0

validate_platform() {
    # Check if image exists
    if ! docker image inspect "generic-py/$SERVICE_NAME:latest" >/dev/null 2>&1; then
        echo "Error: Image generic-py/$SERVICE_NAME:latest not found"
        exit 1
    fi

    # Check image platform
    PLATFORM=$(docker image inspect "generic-py/$SERVICE_NAME:latest" --format '{{.Os}}/{{.Architecture}}')

    # For deployment to AWS Fargate, we need to ensure the image is linux/amd64
    if [[ "$COMMAND" == "deploy" ]]; then
        if [[ "$PLATFORM" != "linux/amd64" ]]; then
            echo "Error: AWS Fargate requires linux/amd64 platform"
            echo "Current platform: $PLATFORM"
            echo "Please rebuild the image with: $0 build $SERVICE_NAME -p linux/amd64"
            exit 1
        fi
    # For other commands, either amd64 or arm64 is acceptable
    elif [[ "$PLATFORM" != "linux/amd64" && "$PLATFORM" != "linux/arm64" ]]; then
        echo "Error: Image must be built for linux/amd64 or linux/arm64"
        echo "Current platform: $PLATFORM"
        exit 1
    fi

    echo "Image platform validated: $PLATFORM"
}

validate_branch() {
    local current_branch=$1
    local is_dirty=$(git status --porcelain)

    # NEVER allow dirty commits from main and dev
    if [[ -n "$is_dirty" ]] && [[ "$current_branch" =~ ^(main|dev)$ ]]; then
        echo "Error: Dirty working directory not allowed for main or dev branches"
        exit 1
    fi

    # For other branches, check dirty flag
    if [[ -n "$is_dirty" ]] && [[ "$ALLOW_DIRTY" != 1 ]]; then
        echo "Error: Working directory not clean"
        exit 1
    fi

    # Check branch name restrictions if we're not skipping
    if [[ "$SKIP_BRANCH_CHECK" != 1 ]]; then
        if [[ ! "$current_branch" =~ ^(main|dev)$ ]]; then
            echo "Error: Deployments only allowed from main or dev branches"
            echo "Current branch: $current_branch"
            echo "Use -S flag to bypass this restriction"
            exit 1
        fi
    fi
}

# TODO: digital ocean integration
push() {
    local branch_name=$1
    local is_dirty=$(git status --porcelain)

    COMMIT_HASH=$(git rev-parse --short HEAD)

    # Sanitize branch name for docker tag (replace / with -)
    SAFE_BRANCH_NAME=${branch_name//\//-}

    # Generate a short hash of the branch name for uniqueness
    BRANCH_HASH=$(echo "$SAFE_BRANCH_NAME" | md5sum | cut -c1-6)

    # Map branch to environment with short identifiers
    if [[ "$SAFE_BRANCH_NAME" == "main" ]]; then
        ENV_NAME="production"
    elif [[ "$SAFE_BRANCH_NAME" == "dev" ]]; then
        ENV_NAME="staging"
    else
        # Extract branch type (feature, fix, etc.) and create a short slug
        if [[ "$SAFE_BRANCH_NAME" =~ ^feature- ]]; then
            ENV_NAME="staging-feat-${BRANCH_HASH}"
        elif [[ "$SAFE_BRANCH_NAME" =~ ^fix- ]]; then
            ENV_NAME="staging-fix-${BRANCH_HASH}"
        elif [[ "$SAFE_BRANCH_NAME" =~ ^release- ]]; then
            ENV_NAME="staging-rel-${BRANCH_HASH}"
        else
            # For any other branch, use a generic prefix with hash
            ENV_NAME="staging-br-${BRANCH_HASH}"
        fi

        # Print mapping to console for reference
        echo "Branch mapping: $SAFE_BRANCH_NAME → $ENV_NAME"
    fi

    # Add dirty flag if working directory is not clean
    if [[ -n "$is_dirty" ]]; then
        ENV_NAME="${ENV_NAME}-dirty"
        echo "Working directory not clean, adding -dirty suffix"
    fi

    # Tag with environment name and commit hash
    if ! docker tag generic-py/$SERVICE_NAME:latest $REPOSITORY_URL:$ENV_NAME-$COMMIT_HASH ||
        ! docker tag generic-py/$SERVICE_NAME:latest $REPOSITORY_URL:$ENV_NAME-latest; then
        echo "Error: Failed to tag images"
        exit 1
    fi

    # For main/production or when force latest is enabled, tag as 'latest'
    if [[ "$ENV_NAME" == "production" ]] || [[ "$FORCE_LATEST" == 1 ]]; then
        if ! docker tag generic-py/$SERVICE_NAME:latest $REPOSITORY_URL:latest; then
            echo "Error: Failed to tag as latest"
            exit 1
        fi
        if [[ "$FORCE_LATEST" == 1 ]]; then
            echo "Warning: Forcing push to latest tag from non-production branch"
        fi
    fi

    # For custom branches, optionally tag as staging-latest
    if [[ "$TAG_AS_STAGING_LATEST" == 1 ]] && [[ ! "$SAFE_BRANCH_NAME" =~ ^(main|dev)$ ]]; then
        if ! docker tag generic-py/$SERVICE_NAME:latest $REPOSITORY_URL:staging-latest; then
            echo "Error: Failed to tag as staging-latest"
            exit 1
        fi
    fi

    # Push all tags
    PUSHED_TAGS=()

    if docker push $REPOSITORY_URL:$ENV_NAME-$COMMIT_HASH; then
        PUSHED_TAGS+=("$REPOSITORY_URL:$ENV_NAME-$COMMIT_HASH")
    else
        echo "Error: Failed to push $REPOSITORY_URL:$ENV_NAME-$COMMIT_HASH"
        exit 1
    fi

    if docker push $REPOSITORY_URL:$ENV_NAME-latest; then
        PUSHED_TAGS+=("$REPOSITORY_URL:$ENV_NAME-latest")
    else
        echo "Error: Failed to push $REPOSITORY_URL:$ENV_NAME-latest"
        exit 1
    fi

    # Push 'latest' tag for production or when force latest is enabled
    if [[ "$ENV_NAME" == "production" ]] || [[ "$FORCE_LATEST" == 1 ]]; then
        if docker push $REPOSITORY_URL:latest; then
            PUSHED_TAGS+=("$REPOSITORY_URL:latest")
        else
            echo "Error: Failed to push latest tag"
            exit 1
        fi
    fi

    # Push staging-latest for custom branches if requested
    if [[ "$TAG_AS_STAGING_LATEST" == 1 ]] && [[ ! "$SAFE_BRANCH_NAME" =~ ^(main|dev)$ ]]; then
        if docker push $REPOSITORY_URL:staging-latest; then
            PUSHED_TAGS+=("$REPOSITORY_URL:staging-latest")
        else
            echo "Error: Failed to push staging-latest tag"
            exit 1
        fi
    fi

    echo "Pushed images:"
    for tag in "${PUSHED_TAGS[@]}"; do
        echo " - $tag"
    done
}

# Main command processing
COMMAND=$1
shift 1

case $COMMAND in
build)
    # Default to host platform if not specified
    PLATFORM=""

    # Parse build-specific options
    while getopts "p:" opt; do
        case $opt in
        p) PLATFORM="--platform=$OPTARG" ;;
        ?) usage ;;
        esac
    done

    echo "Building docker container for $SERVICE_NAME..."
    if [ -n "$PLATFORM" ]; then
        echo "Using platform: $PLATFORM"
        docker build $PLATFORM -t generic-py/$SERVICE_NAME:latest -f Dockerfile .
    else
        docker build -t generic-py/$SERVICE_NAME:latest -f Dockerfile .
    fi
    ;;
run)
    # Default to no port mapping
    PORT_MAPPING=""

    # Parse run-specific options
    while getopts "p:" opt; do
        case $opt in
        p) PORT_MAPPING="-p $OPTARG" ;;
        ?) usage ;;
        esac
    done

    echo "Running docker container for $SERVICE_NAME..."
    if [ -n "$PORT_MAPPING" ]; then
        echo "Using port mapping: $PORT_MAPPING"
        docker run -it --rm $PORT_MAPPING generic-py/$SERVICE_NAME:latest
    else
        docker run -it --rm generic-py/$SERVICE_NAME:latest
    fi
    ;;
push)
    # Parse push-specific options
    while getopts "SDLF" opt; do
        case $opt in
        S) SKIP_BRANCH_CHECK=1 ;;
        D) ALLOW_DIRTY=1 ;;
        L) TAG_AS_STAGING_LATEST=1 ;;
        F) FORCE_LATEST=1 ;;
        ?) usage ;;
        esac
    done

    # Validate required environment variables
    echo $DO_TOKEN
    if [[ -z "$DO_TOKEN" ]]; then
        echo "Error: Missing required environment variables"
        usage
    fi

    # Always run platform validation
    validate_platform

    # Always validate the branch, but -S flag will modify the validation behavior
    validate_branch "$BRANCH_NAME"

    push "$BRANCH_NAME"
    ;;
help | --help | -h)
    usage
    ;;
*)
    echo "Error: Unknown command '$COMMAND'"
    usage
    ;;
esac
