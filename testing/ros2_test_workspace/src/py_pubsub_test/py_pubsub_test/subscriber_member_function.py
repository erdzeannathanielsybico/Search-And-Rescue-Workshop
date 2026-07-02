import rclpy                      # ROS2 Python library
from rclpy.node import Node       # base class to inherit from so this becomes a ROS2 node
from std_msgs.msg import String   # message type — has to match what the publisher is sending

# the node — inherits Node to get all ROS2 capabilities
class MinimalSubscriber(Node):

    # setup() — runs once, registers the subscription
    def __init__(self):
        super().__init__('minimal_subscriber')                                            # register this node with ROS2 under the name 'minimal_subscriber'
        self.subscription = self.create_subscription(String, 'topic', self.pub_listener, 10)  # listen on 'topic', call pub_listener when a message arrives, buffer 10

    # fires automatically when a message arrives on 'topic' — ROS2 passes the message in as msg
    def pub_listener(self, msg):
        self.get_logger().info(f'Listening: "{msg.data}"')   # print the message content to terminal, like Serial.println()

def main(args=None):
    rclpy.init(args=args)                    # start ROS2
    minimal_subscriber = MinimalSubscriber() # create the node once — runs __init__
    rclpy.spin(minimal_subscriber)           # keep running, fires pub_listener every time a message arrives on 'topic'
    minimal_subscriber.destroy_node()        # only reached on Ctrl+C — clean up
    rclpy.shutdown()                         # shut down ROS2


if __name__ == '__main__':
    main()  # entry point — what runs when you do: ros2 run py_pubsub listener