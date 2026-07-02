import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DirectionToSerial(Node):
    def __init__(self):
        super().__init__('direction_to_serial')
        self.subscription = self.create_subscription(String, 'Direction', self.serial_bridge, 10)

    def serial_bridge(self, direction):
        self.get_logger().info(f'Listening: {direction.data}')


def main(args=None):
    rclpy.init(args=args)
    direction_to_serial = DirectionToSerial()
    rclpy.spin(direction_to_serial)
    direction_to_serial.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()