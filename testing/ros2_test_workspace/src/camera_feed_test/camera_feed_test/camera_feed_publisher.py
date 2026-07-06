import cv2

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage
from rclpy.qos import qos_profile_sensor_data

from camera_feed_test import color_detection_tool

# Checked in this order — first color whose saved range finds a target
# wins. Sequential, not simultaneous, so two differently-colored objects
# in frame at once don't produce two competing detections.
COLOR_PRIORITY = ['RED', 'GREEN', 'BLUE']


class CameraFeedPublisher(Node):
    def __init__(self):
        super().__init__('camera_feed_publisher')

        self.declare_parameter('camera_index', 0)
        camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value

        # Pin the V4L2 backend explicitly so property-setting order below is
        # respected consistently (some backends silently reorder/ignore sets).
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.get_logger().error(f'Could not open camera index {camera_index}')

        # Force the camera's hardware MJPG encoder instead of raw YUYV. Must
        # be set before width/height — V4L2 only applies it at that point.
        # Raw YUYV at 1280x720@30fps needs ~66MB/s, more than the bus can
        # sustain, so frames arrive irregularly (the wobble) instead of at a
        # clean, lower, steady fps. MJPG is compressed in-camera and holds a
        # steady 30fps at this resolution (confirmed via
        # `v4l2-ctl --list-formats-ext`).
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # Keep only 1 frame in OpenCV's own capture buffer — otherwise read()
        # can hand back a frame that's already old, adding lag on top of
        # whatever's happening at the ROS/network level.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Default QoS is "reliable, keep everything" — fine for commands, bad
        # for video: if the network hiccups, it queues up stale frames instead
        # of dropping them. qos_profile_sensor_data is the standard ROS 2
        # profile for exactly this (best-effort, shallow queue depth).
        self.publisher = self.create_publisher(CompressedImage, 'CameraFeed', qos_profile_sensor_data)

        # Detection runs every frame regardless of view mode — automatic
        # driving needs it even while the HUD is showing RAW. TargetDetails
        # uses the same best-effort QoS as CameraFeed: a stale detection
        # shouldn't be queued/retried, only the latest one ever matters.
        self.target_details_publisher = self.create_publisher(String, 'TargetDetails', qos_profile_sensor_data)

        # RAW = publish frames untouched (fastest). BOX = also draw a box +
        # position around the detected target. Only ever publishing one —
        # laptop_controller picks which via a keypress.
        self.view_mode = 'RAW'
        self.view_mode_subscription = self.create_subscription(
            String, 'CameraViewMode', self.on_view_mode, 10)

        self.timer = self.create_timer(1 / 30, self.publish_frame)

    def on_view_mode(self, msg):
        self.view_mode = msg.data

    def detect_target(self, frame):
        """Return (color_name, bbox) for the highest-priority color with a match, or (None, None)."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        for candidate in COLOR_PRIORITY:
            lower, upper = color_detection_tool.range_for_color(candidate)
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            bbox = color_detection_tool.find_target(mask)
            if bbox is not None:
                return candidate, bbox
        return None, None

    def publish_target_details(self, frame_width, color_name, bbox):
        if bbox is None:
            data = 'NONE'
        else:
            x, y, w, h = bbox
            cx = x + w // 2
            # -1.0 (fully left) .. 0.0 (centered) .. 1.0 (fully right) —
            # matches the convention automatic_direction_controller expects.
            offset = (cx - frame_width / 2) / (frame_width / 2)
            data = f'{color_name},{offset:.2f}'

        msg = String()
        msg.data = data
        self.target_details_publisher.publish(msg)

    def draw_target_box(self, frame, color_name, bbox):
        frame_width = frame.shape[1]
        if bbox is None:
            cv2.putText(frame, 'NONE', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            return frame

        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cx = x + w // 2
        if cx < frame_width / 3:
            position = 'LEFT'
        elif cx > frame_width * 2 / 3:
            position = 'RIGHT'
        else:
            position = 'CENTER'

        cv2.putText(frame, f'{color_name} {position}', (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return frame

    def publish_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        color_name, bbox = self.detect_target(frame)
        self.publish_target_details(frame.shape[1], color_name, bbox)

        if self.view_mode == 'BOX':
            frame = self.draw_target_box(frame, color_name, bbox)

        ok, encoded = cv2.imencode('.jpg', frame)
        if not ok:
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.format = 'jpeg'
        msg.data = encoded.tobytes()
        self.publisher.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    camera_feed_publisher = CameraFeedPublisher()
    rclpy.spin(camera_feed_publisher)
    camera_feed_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
