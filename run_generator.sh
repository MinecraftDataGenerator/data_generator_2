#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# Usage function
usage() {
    echo "Usage: $0 <path-to-server.jar>"
    echo
    echo "Example:"
    echo "  $0 ./server.jar"
    echo
    echo "Runs the Minecraft data generator."
    exit 1
}

# Check arguments
if [[ $# -ne 1 ]]; then
    echo "Error: Exactly one argument is required."
    usage
fi

JAR_FILE="$1"

# Check jar file
if [[ ! -f "$JAR_FILE" ]]; then
    echo "Error: File '$JAR_FILE' does not exist."
    usage
fi

# Helper function to run commands with logging
run_command() {
    echo "Running: $*"
    "$@"
}

# First attempt (old method)
echo "Starting first attempt..."
if run_command java -cp "$JAR_FILE" net.minecraft.data.Main --all; then
    echo "First command succeeded."
    exit 0
else
    echo "First command failed, trying bundled attempt..."
fi

# Bundled attempt
echo "Starting bundled attempt..."
if run_command java -DbundlerMainClass=net.minecraft.data.Main -jar "$JAR_FILE" --all; then
    echo "Bundled attempt succeeded."
    exit 0
else
    echo "Bundled attempt also failed."
    exit 1
fi