import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import qos_profile_sensor_data

# Cruising speed while centered, and how much one wheel is boosted/slowed
# per unit of offset. BASE_SPEED is kept below MAX_SPEED so TURN_GAIN has
# room to push one wheel up without clipping — see compute_speeds().
# MAX_SPEED is raw PWM (analogWrite on the Nano, see main.cpp setSpeed()),
# not a percentage — 255 is the real ceiling, matching laptop_controller's
# KEY_TO_SPEED range. Don't lower MAX_SPEED to throttle turns — that caps
# the fast wheel too and weakens the turn. TURN_GAIN is set high enough
# that a full-left/right offset clips to a full pivot (one wheel at 255,
# the other at 0) — the wheels are rubbery/high-friction enough that a
# partial differential (e.g. 210 vs 90) isn't enough to actually turn.
BASE_SPEED = 150
TURN_GAIN = 150
MAX_SPEED = 255

# offset is bent through TURN_CURVE before scaling by TURN_GAIN (see
# compute_speeds) so small offsets already get most of the turn strength —
# needed so the ultrasonic (narrow FOV, mounted facing forward) picks the
# cylinder back up well before the target drifts to the frame edge.
# 0.5 = square root: offset 0.3 -> ~0.55 turn strength, offset 1.0 -> 1.0.
# DEADBAND ignores offsets this small — without it, camera jitter around
# dead-center would get amplified by the curve (steepest right at 0) into
# a visibly twitchy/oscillating drive.
TURN_CURVE = 0.5
DEADBAND = 0.05


def clamp_speed(speed):
    return max(0, min(MAX_SPEED, speed))


def compute_speeds(offset):
    """offset: -1.0 (target fully left) .. 0.0 (centered) .. 1.0 (fully right).

    To turn toward the target, the wheel on that side slows relative to the
    other — e.g. offset > 0 (target right) slows the right wheel. Signs were
    flipped from the original left/right assumption because testing showed
    the robot turning the wrong way; left/right wiring has needed swapping
    before (see the note in main.cpp) — if wiring ever gets corrected on the
    hardware side, flip these signs back.
    """
    if abs(offset) < DEADBAND:
        turn = 0.0
    else:
        turn = math.copysign(abs(offset) ** TURN_CURVE, offset)

    left = clamp_speed(round(BASE_SPEED - turn * TURN_GAIN))
    right = clamp_speed(round(BASE_SPEED + turn * TURN_GAIN))
    return left, right


class AutomaticDirectionController(Node):
    def __init__(self):
        super().__init__('automatic_direction_controller')
        # Matches CameraFeed's QoS — a stale/dropped detection shouldn't be
        # queued and retried, only the latest one ever matters. Only cares
        # about location, not color — TargetColor exists as its own topic
        # for the LED strip, which this node has no reason to touch.
        self.subscription = self.create_subscription(
            String, 'TargetLocation', self.on_target_location, qos_profile_sensor_data)
        self.publisher = self.create_publisher(String, 'AutomaticDirection', 10)

    def on_target_location(self, msg):
        # No dedupe here on purpose — command_switcher may have been dropping
        # every message while we weren't the active mode, so there's no way
        # to know the Nano actually has our last-sent state. Resend fresh
        # every cycle instead of trusting local memory of what was "already sent".
        if msg.data == 'NONE':
            self.publish('STOP')
            return

        offset = float(msg.data)
        left, right = compute_speeds(offset)

        self.publish('FORWARD')
        self.publish(f'SPEED,{left},{right}')

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
