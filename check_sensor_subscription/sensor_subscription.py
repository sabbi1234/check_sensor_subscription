#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range, BatteryState
import requests
from datetime import datetime
import time
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor

# Health check configuration
ROVER_ID = "R_001"
RPI_NO = "Rpi_001"
POST_URL = "http://localhost:5000/logHealthCheckRPI"
ACTIVITY_URL = "http://localhost:5000/logActivity"
ERROR_URL = "http://localhost:5000/logError"
LOCATION_X = ""
LOCATION_Y = ""
LOCATION_Z = ""

class TopicMonitor(Node):
    def __init__(self):
        super().__init__('topic_monitor')
        
        # Create callback groups
        self.sensor_callback_group = ReentrantCallbackGroup()
        self.battery_callback_group = ReentrantCallbackGroup()
        
        # Range sensor topics with individual callbacks
        self.range_topics = {
            '/ultrasonic_distance_1': {'received': False, 'subscription': None},
            '/ultrasonic_distance_5': {'received': False, 'subscription': None},
            '/ultrasonic_distance_6': {'received': False, 'subscription': None},
            '/ultrasonic_distance_4': {'received': False, 'subscription': None}
        }
        
        # Battery topic
        self.battery_topic = '/battery_state'
        self.battery_received = False
        
        # Error tracking
        self.error_occurred = False
        self.error_messages = []
        
        # Create subscriptions
        self.setup_subscriptions()
            
    def setup_subscriptions(self):
        # Create individual subscriptions for each ultrasonic sensor
        for topic in self.range_topics.keys():
            sub = self.create_subscription(
                Range,
                topic,
                lambda msg, t=topic: self.range_callback(msg, t),
                10,
                callback_group=self.sensor_callback_group
            )
            self.range_topics[topic]['subscription'] = sub
        
        # QoS profile for battery state
        battery_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Subscribe to battery topic with its own callback group
        self.battery_subscription = self.create_subscription(
            BatteryState,
            self.battery_topic,
            self.battery_callback,
            battery_qos,
            callback_group=self.battery_callback_group
        )
            
    def range_callback(self, msg, topic):
        self.range_topics[topic]['received'] = True
        
    def battery_callback(self, msg):
        self.battery_received = True
        
    def send_health_check(self, component_name, status, value=None, remarks=""):
        now = datetime.now().isoformat()
        data = {
            "rover_id": ROVER_ID,
            "rpi_id": RPI_NO,
            "device_id": component_name,
            "check_status": status,
            "check_value": str(value) if value else "",
            "date_time": now,
            "location_x": LOCATION_X,
            "location_y": LOCATION_Y,
            "location_z": LOCATION_Z,
            "remarks": remarks
        }

        try:
            response = requests.post(POST_URL, headers={'Content-Type': 'application/json'}, json=data)
            print(f"✅-H Health check sent for {component_name} | Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌-H Failed to send health check: {str(e)}")
            
    def log_activity(self):
        payload = {
            "activity_id": "act-1001",
            "rover_id": ROVER_ID,
            "activity_type": "Topic Health Check",
            "description": "All ROS2 topics are publishing data",
            "location_x": LOCATION_X,
            "location_y": LOCATION_Y,
            "location_z": LOCATION_Z,
            "created_at": datetime.now().isoformat()
        }

        try:
            response = requests.post(ACTIVITY_URL, json=payload)
            print(f"✅-A Activity logged | Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌-A Failed to log activity: {str(e)}")

    def log_error(self):
        message = "\n".join(self.error_messages)
        payload = {
            "activity_id": "act-5647",
            "activity_type": "Topic Monitoring Error",
            "error_code": "E204",
            "rover_id": ROVER_ID,
            "error_message": message,
            "location_x": LOCATION_X,
            "location_y": LOCATION_Y,
            "location_z": LOCATION_Z,
            "created_at": datetime.now().isoformat()
        }

        try:
            response = requests.post(ERROR_URL, json=payload)
            print(f"✅-E Error logged | Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌-E Failed to log error: {str(e)}")

    def check_status(self):
        # Check for any range topics not publishing
        for topic, data in self.range_topics.items():
            if not data['received']:
                self.error_occurred = True
                error_msg = f"Topic not publishing: {topic}"
                self.error_messages.append(error_msg)
                self.send_health_check(topic, "0", None, f"Topic not publishing data: {topic}")
            else:
                self.send_health_check(topic, "1", None, f"Topic is publishing data: {topic}")
        
        # Check battery topic
        if not self.battery_received:
            self.error_occurred = True
            error_msg = f"Topic not publishing: {self.battery_topic}"
            self.error_messages.append(error_msg)
            self.send_health_check(self.battery_topic, "0", None, f"Topic not publishing data: {self.battery_topic}")
        else:
            self.send_health_check(self.battery_topic, "1", None, f"Topic is publishing data: {self.battery_topic}")

        # Print local status report
        print("\nTopic Status Report:")
        print("====================")
        for topic, data in self.range_topics.items():
            status = "OK" if data['received'] else "NOT PUBLISHING"
            print(f"[{status:^15}] {topic}")
        
        battery_status = "OK" if self.battery_received else "NOT PUBLISHING"
        print(f"[{battery_status:^15}] {self.battery_topic}")


def main():
    rclpy.init()
    
    # Create node
    monitor = TopicMonitor()
    
    # Use MultiThreadedExecutor to handle callbacks in parallel
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(monitor)
    
    # Monitoring loop with timeout
    try:
        # Spin for a few seconds to collect data
        # Use spin_once in a loop with timeout as an alternative to spin_for
        end_time = time.time() + 5.0  # 5 second timeout
        while time.time() < end_time:
            executor.spin_once(timeout_sec=0.1)
            # Check if all topics have been received
            all_received = all(data['received'] for data in monitor.range_topics.values()) and monitor.battery_received
            if all_received:
                monitor.get_logger().info("All topics received, stopping early")
                break
    except KeyboardInterrupt:
        pass
    finally:
        # Final status check and reporting
        monitor.check_status()
        
        # Send appropriate logs
        if monitor.error_occurred:
            monitor.log_error()
        else:
            monitor.log_activity()
            
        # Clean up
        executor.shutdown()
        monitor.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
