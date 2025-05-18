#!/bin/bash
set -e  # Exit on any error

# ===== CONFIGURATION =====
SERVICE_NAME="sensor_subscription"  # Change this to your desired service name
WORKING_NAME="gazebo_test"  # Change this to your working directory name
USER_NAME=$(whoami)
WORKING_DIR="/home/$USER_NAME/$WORKING_NAME"  # Change this to your working directory
EXEC_START="/home/$USER_NAME/$WORKING_NAME/src/check_sensor_subscription/bash/check_sensor.sh"



# =========================

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== Creating Systemd Service ==="
echo "Service Name: $SERVICE_NAME"
echo "User: $USER_NAME"
echo "Working Directory: $WORKING_DIR"
echo "Executable: $EXEC_START"

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