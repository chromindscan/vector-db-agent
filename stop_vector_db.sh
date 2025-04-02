#!/bin/bash

# Stop Vector DB Environment
# This script stops the Chromia node and any running Python scripts

echo "========== Stopping Chromia Vector Database Environment =========="

# Step 1: Find and stop any running Python scripts
echo "Stopping any running Python scripts..."
pkill -f "python crypto_agent.py" || echo "No crypto_agent.py processes found"
pkill -f "python embed_crypto_data.py" || echo "No embed_crypto_data.py processes found"

# Step 2: Find and stop the Chromia Docker container
echo "Finding Chromia Docker container..."
CONTAINER_ID=$(docker ps | grep "chromaway/example-projects/directory1-example/managed-single" | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "No running Chromia Docker container found."
else
    echo "Stopping Docker container: $CONTAINER_ID"
    docker stop $CONTAINER_ID
    if [ $? -eq 0 ]; then
        echo "Docker container stopped successfully."
    else
        echo "Error stopping Docker container. You may need to stop it manually."
    fi
fi

# Step 3: Clean up environment variables
echo "Cleaning up environment variables..."
unset VECTOR_BRID

echo "========== Chromia Vector Database Environment Stopped ==========" 