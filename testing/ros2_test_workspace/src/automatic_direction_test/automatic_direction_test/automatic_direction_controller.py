import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import qos_profile_sensor_data

# Cruising speed while centered, and how much one wheel is boosted/slowed
# per unit of offset. BASE_SPEED is kept below MAX_SPEED so TURN_GAIN has
# room to push one wheel up without clipping — see compute_speeds().
BASE_SPEED = 70
TURN_GAIN = 30
MAX_SPEED = 100


def clamp_speed(speed):
    return max(0, min(MAX_SPEED, speed))


def compute_speeds(offset):
    """offset: -1.0 (target fully left) .. 0.0 (centered) .. 1.0 (fully right).

    To turn toward the target, the wheel on that side slows relative to the
    other — e.g. offset > 0 (target right) slows the right wheel. Flip the
    signs here if testing shows the robot turning the wrong way; left/right
    wiring has needed swapping before (see the note in main.cpp).
    """
    left = clamp_speed(round(BASE_SPEED + offset * TURN_GAIN))
    right = clamp_speed(round(BASE_SPEED - offset * TURN_GAIN))
    return left, right


class AutomaticDirectionController(Node):
    def __init__(self):
        super().__init__('automatic_direction_controller')
        # Matches CameraFeed's QoS — a stale/dropped detection shouldn't be
        # queued and retried, only the latest one ever matters.
        self.subscription = self.create_subscription(
            String, 'TargetDetails', self.on_target_details, qos_profile_sensor_data)
        self.publisher = self.create_publisher(String, 'AutomaticDirection', 10)
        self.last_direction = None  # dedupe FORWARD/STOP, same idea as laptop_controller's keys

    def on_target_details(self, msg):
        if msg.data == 'NONE':
            self.publish_direction('STOP')
            return

        _color, offset_str = msg.data.split(',')
        offset = float(offset_str)
        left, right = compute_speeds(offset)

        self.publish_direction('FORWARD')
        self.publish(f'SPEED,{left},{right}')

    def publish_direction(self, direction):
        if direction == self.last_direction:
            return
        self.last_direction = direction
        self.publish(direction)

    def publish(self, data):
        msg = String()
        msg.data = data
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: {data}')


def main(args=None):
    rclpy.init(args=args)
    node = AutomaticDirectionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
