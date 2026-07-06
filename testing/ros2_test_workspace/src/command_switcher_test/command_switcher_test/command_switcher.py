import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class CommandSwitcher(Node):
    def __init__(self):
        super().__init__('command_switcher')
        self.mode = 'MANUAL'  # matches the Nano's own default until ControlMode says otherwise
        self.get_logger().info(f'Starting in {self.mode} mode (no ControlMode received yet)')

        self.publisher = self.create_publisher(String, 'Direction', 10)
        self.create_subscription(String, 'ControlMode', self.on_control_mode, 10)
        self.create_subscription(String, 'ManualDirection', self.on_manual_direction, 10)
        self.create_subscription(String, 'AutomaticDirection', self.on_automatic_direction, 10)

    def on_control_mode(self, msg):
        if msg.data != self.mode:
            self.get_logger().info(f'Mode: {self.mode} -> {msg.data}')
        self.mode = msg.data

    def on_manual_direction(self, msg):
        if self.mode == 'MANUAL':
            self.get_logger().info(f'[MANUAL] {msg.data}')
            self.publisher.publish(msg)

    def on_automatic_direction(self, msg):
        if self.mode == 'AUTO':
            self.get_logger().info(f'[AUTO] {msg.data}')
            self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CommandSwitcher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
