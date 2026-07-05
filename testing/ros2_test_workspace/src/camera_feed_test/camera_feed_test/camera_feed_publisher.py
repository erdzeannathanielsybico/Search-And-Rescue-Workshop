import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage


class CameraFeedPublisher(Node):
    def __init__(self):
        super().__init__('camera_feed_publisher')

        self.declare_parameter('camera_index', 0)
        camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value

        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            self.get_logger().error(f'Could not open camera index {camera_index}')

        self.publisher = self.create_publisher(CompressedImage, 'camera_feed', 10)
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
