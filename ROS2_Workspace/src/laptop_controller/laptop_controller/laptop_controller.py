"""
Keyboard controls:
  Arrow keys    - drive (held = moving, released = stop)
  1 / 2 / 3 / 4 - set speed, low to high
  Q / W         - claw open / close
  9 / 0         - camera view: raw / box (detection overlay)
  O / P         - request automatic / manual mode
Click the window first so it has keyboard focus. Close it to quit.
"""

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

KEY_TO_VIEW_MODE = {
    pygame.K_9: 'RAW',
    pygame.K_0: 'BOX',
}

# A request, not a command — the Nano decides whether/when it actually
# switches and reports back over serial; this doesn't assume it took effect.
KEY_TO_MODE_REQUEST = {
    pygame.K_o: 'MODE,AUTO',
    pygame.K_p: 'MODE,MANUAL',
}

# Matches the camera feed's requested resolution (camera_feed_publisher.py)
WINDOW_SIZE = (1280, 720)


class LaptopController(Node):
    def __init__(self):
        super().__init__('laptop_controller')
        # Movement/speed/claw go through command_switcher, which only forwards
        # them to Direction while we're actually the active mode.
        self.publisher = self.create_publisher(String, 'ManualDirection', 10)
        # Mode requests go through command_switcher, not straight to Direction —
        # it needs to see the request itself so it can stop trusting
        # AutomaticDirection immediately, rather than waiting on the Nano's
        # round-trip confirmation over ControlMode.
        self.mode_request_publisher = self.create_publisher(String, 'ModeRequest', 10)
        # QoS must match the publisher's (best-effort, shallow queue) or the
        # two won't connect at all — a reliable subscriber can't pair with a
        # best-effort publisher in DDS.
        self.camera_subscription = self.create_subscription(
            CompressedImage, 'CameraFeed', self.on_camera_frame, qos_profile_sensor_data)
        self.view_mode_publisher = self.create_publisher(String, 'CameraViewMode', 10)
        self.control_mode_subscription = self.create_subscription(
            String, 'ControlMode', self.on_control_mode, 10)
        # Best-effort, matches how UltrasonicData is published — same
        # reasoning as CameraFeed, only the latest reading ever matters.
        self.ultrasonic_subscription = self.create_subscription(
            String, 'UltrasonicData', self.on_ultrasonic_data, qos_profile_sensor_data)
        self.current_key = None  # which arrow key (if any) is currently held down
        self.last_command = 'STOP'
        self.last_view_mode = 'RAW'  # matches camera_feed_publisher's own default
        self.latest_frame_surface = None  # None until the first camera frame arrives
        self.current_mode = 'MANUAL'  # mirrors ControlMode; a guess until the Nano actually confirms
        self.latest_distance_cm = None  # None until UltrasonicData arrives

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

    def on_control_mode(self, msg):
        self.current_mode = msg.data

    def on_ultrasonic_data(self, msg):
        self.latest_distance_cm = msg.data

    def publish_command(self, command):
        if command == self.last_command:
            return  # only publish when the command actually changes
        self.last_command = command
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: {command}')

    def publish_mode_request(self, mode_command):
        msg = String()
        msg.data = mode_command
        self.mode_request_publisher.publish(msg)
        self.get_logger().info(f'Requesting: {mode_command}')

    def publish_view_mode(self, mode):
        if mode == self.last_view_mode:
            return
        self.last_view_mode = mode
        msg = String()
        msg.data = mode
        self.view_mode_publisher.publish(msg)
        self.get_logger().info(f'Camera view mode: {mode}')

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption('Robot Controller')
        clock = pygame.time.Clock()
        # Bottom-left, so it never overlaps camera_feed_publisher's own
        # top-left detection label when the view mode is BOX.
        hud_font = pygame.font.SysFont(None, 36)

        self.get_logger().info(
            'Arrow keys drive, 1-4 set speed, Q/W open/close claw, 9/0 raw/box view, '
            'O/P automatic/manual mode. Click the window first. Close it to quit.')

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
                    # Left/right are equal here — manual driving has no need to
                    # bias one side, that's only for automatic tracking later.
                    speed = KEY_TO_SPEED[event.key]
                    self.publish_command(f'SPEED,{speed},{speed}')
                elif event.type == pygame.KEYDOWN and event.key in KEY_TO_CLAW:
                    self.publish_command(KEY_TO_CLAW[event.key])
                elif event.type == pygame.KEYDOWN and event.key in KEY_TO_VIEW_MODE:
                    self.publish_view_mode(KEY_TO_VIEW_MODE[event.key])
                elif event.type == pygame.KEYDOWN and event.key in KEY_TO_MODE_REQUEST:
                    self.publish_mode_request(KEY_TO_MODE_REQUEST[event.key])

            rclpy.spin_once(self, timeout_sec=0)

            if self.latest_frame_surface is not None:
                screen.blit(self.latest_frame_surface, (0, 0))
            else:
                screen.fill((30, 30, 30))  # placeholder until the first frame arrives

            distance_text = f'{self.latest_distance_cm}cm' if self.latest_distance_cm is not None else '--'
            hud_surface = hud_font.render(f'{self.current_mode}  |  {distance_text}', True, (0, 255, 0))
            screen.blit(hud_surface, (20, WINDOW_SIZE[1] - 50))

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
