#!/bin/bash
set -e

SUBSCRIPTION_ID="aff3f8cf-511e-4af8-a2ae-ba765091e13a"
RESOURCE_GROUP="rg-cs-agent"
REGISTRY_NAME="crrqbabnxvnuxpe"
CONTAINER_APP="callcenterapp"
IMAGE_NAME="app"

# Build the container image in Azure Container Registry
IMAGE_TAG=$(date '+%m%d%H%M%S')
FULL_IMAGE="${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building image: ${FULL_IMAGE}"
az acr build \
  --subscription "${SUBSCRIPTION_ID}" \
  --registry "${REGISTRY_NAME}" \
  --image "${IMAGE_NAME}:${IMAGE_TAG}" \
  ./src/app

# Update the container app with the new image
echo "Deploying image to ${CONTAINER_APP}..."
az containerapp update \
  --name "${CONTAINER_APP}" \
  --resource-group "${RESOURCE_GROUP}" \
  --subscription "${SUBSCRIPTION_ID}" \
  --image "${FULL_IMAGE}"

echo "Deployment complete: ${FULL_IMAGE}"
