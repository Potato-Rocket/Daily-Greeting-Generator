#!/bin/bash
set -e

DOCKER_USER="potatorocket"
IMAGE_NAME="greeting-demo"

echo "Building Docker image..."
docker build -t "${DOCKER_USER}/${IMAGE_NAME}:latest" ./

echo "Pushing to Docker Hub..."
docker push "${DOCKER_USER}/${IMAGE_NAME}:latest"

echo "Done."
