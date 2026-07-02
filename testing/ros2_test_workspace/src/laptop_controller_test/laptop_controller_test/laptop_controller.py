import sys
import termios
import tty
import select

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Arrow keys arrive as a 3-character escape sequence: ESC, then '[', then a letter
ARROW_UP = '\x1b[A'
ARROW_DOWN = '\x1b[B'
ARROW_RIGHT = '\x1b[C'
ARROW_LEFT = '\x1b[D'

KEY_TO_COMMAND = {
    ARROW_UP: 'FORWARD',
    ARROW_DOWN: 'BACKWARD',
    ARROW_LEFT: 'LEFT',
    ARROW_RIGHT: 'RIGHT',
}

# Terminals don't report "key released" — if no key arrives within this many
# seconds, we assume the arrow key was let go and stop the motors.
NO_KEY_TIMEOUT = 0.3


class LaptopController(Node):
    def __init__(self):
        super().__init__('laptop_controller')
        # Publishing to 'ControllerTest' for now, not 'Direction' — lets us
        # check what this node sends with `ros2 topic echo` before wiring it
        # into the real serial bridge.
        self.publisher = self.create_publisher(String, 'ControllerTest', 10)
        self.last_command = 'STOP'

    def publish_command(self, command):
        if command == self.last_command:
            return  # only publish when the command actually changes
        self.last_command = command
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: {command}')

    def read_key(self):
        # Waits up to NO_KEY_TIMEOUT seconds for a keypress; '' means timed out
        ready, _, _ = select.select([sys.stdin], [], [], NO_KEY_TIMEOUT)
        if not ready:
            return ''
        key = sys.stdin.read(1)
        if key == '\x1b':  # start of an arrow key escape sequence
            key += sys.stdin.read(2)
        return key

    def run(self):
        self.get_logger().info('Arrow keys drive the robot. Release = stop. Ctrl+C to quit.')

        # Puts the terminal in "raw" mode so a single keypress is available
        # immediately, without waiting for Enter to be pressed.
        original_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        try:
            while rclpy.ok():
                key = self.read_key()
                command = KEY_TO_COMMAND.get(key, 'STOP')
                self.publish_command(command)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)


def main(args=None):
    rclpy.init(args=args)
    laptop_controller = LaptopController()
    laptop_controller.run()
    laptop_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
