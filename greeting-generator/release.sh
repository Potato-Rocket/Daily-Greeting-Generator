#!/bin/bash
# Tag a git release and push Docker image
# Usage: ./release.sh 0.1.0 -m "Containerized generator with Piper TTS"

set -e

DOCKER_USER="potatorocket"
IMAGE_NAME="daily-greeting"

# Check that arguments follow correct format
if [ -z "$1" ] || [ "$2" != "-m" ] || [ -z "$3" ]; then
    echo "Usage: ./release.sh VERSION -m \"message\""
    echo "Example: ./release.sh 0.1.0 -m \"Containerized generator with Piper TTS\""
    exit 1
fi

VERSION=$1
MESSAGE="$3"

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must follow semver (e.g. 0.1.0, 1.2.3)"
    exit 1
fi

# Fail if working tree is dirty
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working tree has uncommitted changes"
    exit 1
fi

echo "Releasing v${VERSION}: ${MESSAGE}"
echo ""

# Git tag
echo "Tagging git commit..."
git tag "v${VERSION}" -m "${MESSAGE}"
git push origin "v${VERSION}"

# Docker build and push
echo "Building Docker image..."
docker compose build

echo "Pushing to Docker Hub..."
docker tag "${IMAGE_NAME}:dev" "${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
docker tag "${IMAGE_NAME}:dev" "${DOCKER_USER}/${IMAGE_NAME}:latest"
docker push "${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
docker push "${DOCKER_USER}/${IMAGE_NAME}:latest"

echo "Cleaning up..."

docker image rm "${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
docker image rm "${DOCKER_USER}/${IMAGE_NAME}:latest"

echo ""
echo "Released v${VERSION} successfully"
echo "  Git: v${VERSION}"
echo "  Docker: ${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"