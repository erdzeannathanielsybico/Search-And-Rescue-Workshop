import pygame

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

KEY_TO_COMMAND = {
    pygame.K_UP: 'FORWARD',
    pygame.K_DOWN: 'BACKWARD',
    pygame.K_LEFT: 'LEFT',
    pygame.K_RIGHT: 'RIGHT',
}

# Placeholder window size — becomes the camera feed's resolution once that exists
WINDOW_SIZE = (640, 480)


class LaptopController(Node):
    def __init__(self):
        super().__init__('laptop_controller')
        self.publisher = self.create_publisher(String, 'Direction', 10)
        self.current_key = None  # which arrow key (if any) is currently held down
        self.last_command = 'STOP'

    def publish_command(self, command):
        if command == self.last_command:
            return  # only publish when the command actually changes
        self.last_command = command
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: {command}')

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption('Robot Controller')
        clock = pygame.time.Clock()

        self.get_logger().info('Click the window, then use arrow keys. Close the window to quit.')

        running = True
        while running and rclpy.ok():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in KEY_TO_COMMAND:
                    self.current_key = event.key
                    self.publish_command(KEY_TO_COMMAND[event.key])
                elif event.type == pygame.KEYUP and event.key == self.current_key:
                    self.current_key = None
                    self.publish_command('STOP')

            rclpy.spin_once(self, timeout_sec=0)

            screen.fill((30, 30, 30))  # plain background until the camera feed replaces this
            pygame.display.flip()
            clock.tick(30)  # 30 fps cap — matches a typical webcam rate

        pygame.quit()


def main(args=None):
    rclpy.init(args=args)
    laptop_controller = LaptopController()
    laptop_controller.run()
    laptop_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
