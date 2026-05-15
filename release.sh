#!/bin/bash
# Tag a git release and push Docker image
# Usage: ./release.sh -m "Release message"
# Version is read from pyproject.toml — bump it there before releasing.

set -e

DOCKER_USER="potatorocket"
IMAGE_NAME="daily-greeting"

VERSION=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version in pyproject.toml must follow semver (e.g. 0.1.0, 1.2.3)"
    exit 1
fi

# Check if tag already exists
if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
    TAG_EXISTS=true
    echo "Tag v${VERSION} already exists, skipping git tag"
else
    TAG_EXISTS=false
    if [ "$1" != "-m" ] || [ -z "$2" ]; then
        echo "Usage: ./release.sh -m \"Release message\""
        echo "Bump the version in pyproject.toml before running."
        exit 1
    fi
    MESSAGE="$2"

    # Fail if working tree is dirty
    if [ -n "$(git status --porcelain)" ]; then
        echo "Error: Working tree has uncommitted changes"
        exit 1
    fi
fi

echo "Releasing v${VERSION}${MESSAGE:+: ${MESSAGE}}"
echo ""

# Git tag (skip if already exists)
if [ "$TAG_EXISTS" = false ]; then
    echo "Tagging git commit..."
    git tag "v${VERSION}" -m "${MESSAGE}"
    git push origin "v${VERSION}"
fi

# Docker build and push
echo "Building Docker image..."
docker compose build

echo "Tagging Docker image..."
docker tag "${IMAGE_NAME}:dev" "${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
docker tag "${IMAGE_NAME}:dev" "${DOCKER_USER}/${IMAGE_NAME}:latest"

echo "Pushing to Docker Hub..."
docker push "${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
docker push "${DOCKER_USER}/${IMAGE_NAME}:latest"

echo "Cleaning up..."
docker image rm "${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
docker image rm "${DOCKER_USER}/${IMAGE_NAME}:latest"

echo ""
echo "Released v${VERSION} successfully"
echo "  Git: v${VERSION}"
echo "  Docker: ${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
echo "          ${DOCKER_USER}/${IMAGE_NAME}:latest"
