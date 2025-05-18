#!/bin/bash
set -e  # Exit on any error

# ===== AUTOMATIC PATH CONFIGURATION =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKING_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"  # Goes up 3 levels from script
USER_NAME=$(whoami)
SERVICE_NAME="sensor_subscription"  # Change service name if needed

# Verify paths
if [ ! -d "$WORKING_DIR" ]; then
    echo "Error: Could not determine working directory!" >&2
    exit 1
fi

EXEC_START="$SCRIPT_DIR/check_sensor.sh"  # Assumes script is in same directory
# ========================================

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== Creating Systemd Service ==="
echo "Service Name: $SERVICE_NAME"
echo "User: $USER_NAME"
echo "Working Directory: $WORKING_DIR"
echo "Executable: $EXEC_START"
echo "Detected Script Location: $SCRIPT_DIR"

# Verify executable exists
if [ ! -f "$EXEC_START" ]; then
    echo "Error: Executable script not found at $EXEC_START" >&2
    exit 1
fi

# Create service file
echo -e "\n[1/3] Creating service file at $SERVICE_FILE..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=ROS 2 $SERVICE_NAME Service
After=network.target

[Service]
Type=oneshot
User=$USER_NAME
WorkingDirectory=$WORKING_DIR
ExecStart=$EXEC_START
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo -e "\n[2/3] Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo -e "\n[3/3] Enabling $SERVICE_NAME..."
sudo systemctl enable "$SERVICE_NAME.service"

# Verification
echo -e "\n=== Service Created Successfully ==="
echo "Service file: $SERVICE_FILE"
echo -e "\nTo start the service:"
echo "  sudo systemctl start $SERVICE_NAME"
echo -e "\nCurrent status:"
sudo systemctl status "$SERVICE_NAME" --no-pager || true