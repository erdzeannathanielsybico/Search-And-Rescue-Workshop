import rclpy                      # the ROS2 Python library, like #include <Arduino.h>
from rclpy.node import Node       # base class every ROS2 node inherits from
from std_msgs.msg import String   # ROS2's own String message type


# this is the node — inheriting (Node) gives it all ROS2 capabilities for free
class MinimalPublisher(Node):

    # setup() — runs once when the node is created
    def __init__(self):
        super().__init__('minimal_publisher')                        # registers this node with ROS2 under the name 'minimal_publisher'
        self.publisher_ = self.create_publisher(String, 'topic', 10) # open a channel called 'topic', buffer up to 10 messages
        timer_period = 0.5                                           # seconds between each callback
        self.timer = self.create_timer(timer_period, self.timer_callback) # tell ROS2: call timer_callback every 0.5s (stored on self so it doesn't get deleted)
        self.i = 0                                                   # counter that persists between callbacks because it lives on the object

    # loop() — ROS2 calls this every 0.5s, you never call it yourself
    def timer_callback(self):
        msg = String()                                               # create a new empty String message
        msg.data = 'Hello World: %d' % self.i                       # fill it with text and the current count
        self.publisher_.publish(msg)                                 # send it out on the 'topic' channel
        self.get_logger().info('Publishing: "%s"' % msg.data)       # print to terminal, like Serial.println()
        self.i += 1                                                  # increment counter for next fire


def main(args=None):
    rclpy.init(args=args)                  # start ROS2
    minimal_publisher = MinimalPublisher() # create the node once — runs __init__
    rclpy.spin(minimal_publisher)          # blocking loop: holds the program alive and fires timer_callback every 0.5s forever
    minimal_publisher.destroy_node()       # only reached on Ctrl+C — clean up the node
    rclpy.shutdown()                       # shut down ROS2


if __name__ == '__main__':
    main()  # entry point — what runs when you do: ros2 run py_pubsub talker