#!/bin/bash

# Load ROS 2 environment
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=5
source ~/gazebo_test/install/setup.bash

# Run the node
exec ros2 run check_sensor_subscription check_sensor_subscription 
