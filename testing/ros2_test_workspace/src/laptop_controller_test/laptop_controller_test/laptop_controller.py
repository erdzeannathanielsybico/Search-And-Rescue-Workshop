import cv2
import numpy as np
import pygame

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage
from rclpy.qos import qos_profile_sensor_data

KEY_TO_COMMAND = {
    pygame.K_UP: 'FORWARD',
    pygame.K_DOWN: 'BACKWARD',
    pygame.K_LEFT: 'LEFT',
    pygame.K_RIGHT: 'RIGHT',
}

# 1-4 pick a speed (PWM value 0-255) — a real value the motors need, not an
# arbitrary code, so a number here isn't the same "magic number" problem
# direction commands had.
KEY_TO_SPEED = {
    pygame.K_1: 60,
    pygame.K_2: 120,
    pygame.K_3: 180,
    pygame.K_4: 255,
}

KEY_TO_CLAW = {
    pygame.K_q: 'CLAW,OPEN',
    pygame.K_w: 'CLAW,CLOSE',
}

# Matches the camera feed's requested resolution (camera_feed_publisher.py)
WINDOW_SIZE = (1280, 720)


class LaptopController(Node):
    def __init__(self):
        super().__init__('laptop_controller')
        self.publisher = self.create_publisher(String, 'Direction', 10)
        # QoS must match the publisher's (best-effort, shallow queue) or the
        # two won't connect at all — a reliable subscriber can't pair with a
        # best-effort publisher in DDS.
        self.camera_subscription = self.create_subscription(
            CompressedImage, 'CameraFeed', self.on_camera_frame, qos_profile_sensor_data)
        self.current_key = None  # which arrow key (if any) is currently held down
        self.last_command = 'STOP'
        self.latest_frame_surface = None  # None until the first camera frame arrives

    def on_camera_frame(self, msg):
        # msg.data is already JPEG-encoded bytes — decode back into a BGR image
        jpeg_bytes = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(jpeg_bytes, cv2.IMREAD_COLOR)
        if frame is None:
            return

        # pygame expects RGB, OpenCV decodes as BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, _ = frame.shape
        self.latest_frame_surface = pygame.image.frombuffer(frame.tobytes(), (width, height), 'RGB')

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

        self.get_logger().info('Arrow keys drive, 1-4 set speed, Q/W open/close claw. Click the window first. Close it to quit.')

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
                elif event.type == pygame.KEYDOWN and event.key in KEY_TO_SPEED:
                    # A setting, not a held direction — fires once, no release handling.
                    self.publish_command(f'SPEED,{KEY_TO_SPEED[event.key]}')
                elif event.type == pygame.KEYDOWN and event.key in KEY_TO_CLAW:
                    self.publish_command(KEY_TO_CLAW[event.key])

            rclpy.spin_once(self, timeout_sec=0)

            if self.latest_frame_surface is not None:
                screen.blit(self.latest_frame_surface, (0, 0))
            else:
                screen.fill((30, 30, 30))  # placeholder until the first frame arrives
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
