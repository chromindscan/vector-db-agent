#!/bin/bash

# Start Vector DB Setup
# This script automates the process of starting a Chromia node and deploying the vector database blockchain

set -e  # Exit on any error
echo "========== Starting Chromia Vector Database Setup =========="

# Step 1: Start the Chromia node using Docker
echo "Starting Chromia node using Docker..."
CONTAINER_ID=$(docker run -d -p 7740:7740 registry.gitlab.com/chromaway/example-projects/directory1-example/managed-single:latest)
echo "Docker container started with ID: $CONTAINER_ID"

# Step 2: Wait for the node to initialize
echo "Waiting for Chromia node to initialize (20 seconds)..."
sleep 20

# Step 3: Build the Rell application
echo "Building Rell application..."
cd rell
chr build
if [ $? -ne 0 ]; then
    echo "Error: Failed to build Rell application."
    exit 1
fi
cd ..

# Step 4: Deploy the blockchain
echo "Deploying vector blockchain..."
pmc blockchain add -bc rell/build/vector_example.xml -c dapp -n vector_blockchain
if [ $? -ne 0 ]; then
    echo "Error: Failed to deploy vector blockchain."
    exit 1
fi

# Step 5: Get and set the blockchain RID
echo "Getting blockchain RID..."
VECTOR_BRID=$(pmc blockchains | grep -A 1 vector_blockchain | grep "Rid" | awk -F'"' '{print $4}')
if [ -z "$VECTOR_BRID" ]; then
    echo "Error: Could not extract blockchain RID."
    exit 1
fi

# Set the environment variable
export VECTOR_BRID=$VECTOR_BRID
echo "Vector blockchain RID: $VECTOR_BRID"
echo "Environment variable VECTOR_BRID has been set."