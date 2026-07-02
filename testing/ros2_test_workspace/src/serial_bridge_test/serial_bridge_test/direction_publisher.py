import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DirectionPublisher(Node):
    def __init__(self):
        super().__init__('direction_publisher')
        self.publisher = self.create_publisher(String, 'Direction', 10)
        timer_period = 1
        self.direction = String()
        self.direction.data = 'forward'
        self.timer = self.create_timer(timer_period, self.direction_switcher)

    def direction_switcher(self):
        if self.direction.data == 'forward':
            self.direction.data = 'backward'
        else:
            self.direction.data = 'forward'
        self.publisher.publish(self.direction)
        self.get_logger().info(f'Publishing: {self.direction.data}')


def main(args=None):
    rclpy.init(args=args)
    direction_publisher = DirectionPublisher()
    rclpy.spin(direction_publisher)
    direction_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()