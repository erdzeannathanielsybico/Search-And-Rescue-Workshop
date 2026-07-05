import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from rclpy.qos import qos_profile_sensor_data


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
        self.timer = self.create_timer(1 / 30, self.publish_frame)

    def publish_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

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
