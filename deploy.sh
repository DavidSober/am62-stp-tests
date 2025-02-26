#!/bin/bash

# Set variables
TI_USER="root"
TI_IP="$1"
REMOTE_DIR="/root/test_deploy"
LOCAL_DEPLOY_DIR="$(dirname "$0")/to_deploy"  # Get the path to "to_deploy" relative to the script location

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

if [ -z "$TI_IP" ]; then
    error "Usage: ./deploy.sh <TI_BOARD_IP>"
fi

# Ensure the directory exists on the remote machine
log "Ensuring directory exists on TI board..."
ssh "$TI_USER@$TI_IP" "mkdir -p $REMOTE_DIR" || error "Failed to create directory on TI board."

# Copy all files from the "to_deploy/" directory using scp
log "Copying files using scp from $LOCAL_DEPLOY_DIR..."
scp -r "$LOCAL_DEPLOY_DIR/"* "$TI_USER@$TI_IP:$REMOTE_DIR" || error "File transfer failed."

log "Deployment successful!"
