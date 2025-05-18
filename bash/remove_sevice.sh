#!/bin/bash
set -e  # Exit immediately if any command fails

# Configuration - must match your create script
SERVICE_NAME="sensor_subscription"  # Same name used when creating
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== Service Removal Utility ==="
echo "Target service: $SERVICE_NAME"

# Check if service exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file $SERVICE_FILE not found!" >&2
    exit 1
fi

# Stop the service if running
echo -e "\n[1/3] Stopping service..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
    echo "Service stopped."
else
    echo "Service was not running."
fi

# Disable the service
echo -e "\n[2/3] Disabling service..."
if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    sudo systemctl disable "$SERVICE_NAME"
    echo "Service disabled."
else
    echo "Service was not enabled."
fi

# Remove service file
echo -e "\n[3/3] Removing service file..."
sudo rm -v "$SERVICE_FILE"

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed

echo -e "\n=== Service Successfully Removed ==="
echo "To verify:"
echo "  systemctl list-unit-files | grep $SERVICE_NAME"