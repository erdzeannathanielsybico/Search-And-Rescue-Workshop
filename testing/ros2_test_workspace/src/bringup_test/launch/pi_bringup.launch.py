from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='command_switcher_test', executable='command_switcher'),
        Node(package='automatic_direction_test', executable='automatic_direction_controller'),
        Node(package='serial_bridge_test', executable='direction_to_serial'),
        Node(package='camera_feed_test', executable='camera_feed_publisher'),
    ])
