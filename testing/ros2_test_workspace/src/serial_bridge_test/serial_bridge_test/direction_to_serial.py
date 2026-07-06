import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import qos_profile_sensor_data
import serial   # pyserial — talks to the Arduino Nano over the USB serial connection


class DirectionToSerial(Node):
    def __init__(self):
        super().__init__('direction_to_serial')

        # declare_parameter lets the port/baud be overridden from the command line
        # without touching this file, e.g.:
        #   ros2 run serial_bridge_test direction_to_serial --ros-args -p serial_port:=/dev/ttyUSB1
        self.declare_parameter('serial_port', '/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0')
        self.declare_parameter('baud_rate', 115200)

        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('baud_rate').get_parameter_value().integer_value

        # opened once here, not inside the callback — reopening per-message would be
        # slow and would drop the connection state between messages
        self.serial_conn = serial.Serial(port, baud, timeout=1)
        self.get_logger().info(f'Opened serial port {port} at {baud} baud')

        self.subscription = self.create_subscription(String, 'Direction', self.serial_bridge, 10)
        self.control_mode_publisher = self.create_publisher(String, 'ControlMode', 10)
        # Best-effort, like CameraFeed/TargetDetails — the Nano streams this
        # every ~100ms regardless of whether anything's listening, so a
        # dropped reading isn't worth queuing/retrying, only the latest matters.
        self.ultrasonic_publisher = self.create_publisher(String, 'UltrasonicData', qos_profile_sensor_data)
        # rclpy subscriptions only fire on incoming ROS messages, not on serial
        # activity — poll for lines the Nano sends on its own (e.g. "MODE,AUTO").
        self.read_timer = self.create_timer(0.02, self.read_from_nano)

    def serial_bridge(self, direction):
        self.get_logger().info(f'Listening: {direction.data}')

        # serial.write() needs bytes, not str — .encode() converts it.
        # '\n' is appended so the Nano side (with the new bootloader) can tell
        # where one command ends and the next begins, once you write the code
        # to read it there.
        self.serial_conn.write((direction.data + '\n').encode('utf-8'))

    def read_from_nano(self):
        # Drain everything currently buffered, not just one line — the Nano
        # now streams MODE+DISTANCE continuously, so a fixed one-line-per-tick
        # read would let a backlog build up if this timer ever falls behind.
        while self.serial_conn.in_waiting > 0:
            line = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
            if not line:
                continue

            # Just relay the value, don't interpret it, same philosophy as the
            # write side. MODE changes rarely, worth logging; DISTANCE streams
            # every ~100ms and would flood the terminal if logged too.
            if line.startswith('MODE,'):
                self.get_logger().info(f'Nano says: {line}')
                msg = String()
                msg.data = line.split(',', 1)[1]
                self.control_mode_publisher.publish(msg)
            elif line.startswith('DISTANCE,'):
                msg = String()
                msg.data = line.split(',', 1)[1]
                self.ultrasonic_publisher.publish(msg)

    def destroy_node(self):
        # make sure the serial port is released cleanly on shutdown (Ctrl+C)
        self.serial_conn.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    direction_to_serial = DirectionToSerial()
    rclpy.spin(direction_to_serial)
    direction_to_serial.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()