#!/bin/bash
# Tag a git release and push Docker image
# Usage: ./release.sh 0.1.0 -m "Containerized generator with Piper TTS"

set -e

DOCKER_USER="potatorocket"
IMAGE_NAME="daily-greeting"

# Check that version argument is provided
if [ -z "$1" ]; then
    echo "Usage: ./release.sh VERSION [-m \"message\"]"
    echo "Example: ./release.sh 0.1.0 -m \"Containerized generator with Piper TTS\""
    echo "If the tag already exists, -m is not required."
    exit 1
fi

VERSION=$1

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must follow semver (e.g. 0.1.0, 1.2.3)"
    exit 1
fi

# Check if tag already exists
if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
    TAG_EXISTS=true
    echo "Tag v${VERSION} already exists, skipping git tag"
else
    TAG_EXISTS=false
    if [ "$2" != "-m" ] || [ -z "$3" ]; then
        echo "Error: New tags require a message: ./release.sh ${VERSION} -m \"message\""
        exit 1
    fi
    MESSAGE="$3"

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
