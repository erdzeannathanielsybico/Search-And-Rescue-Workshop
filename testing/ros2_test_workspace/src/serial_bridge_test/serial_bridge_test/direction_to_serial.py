import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial   # pyserial — talks to the ESP32/Nano over the USB serial connection


class DirectionToSerial(Node):
    def __init__(self):
        super().__init__('direction_to_serial')

        # declare_parameter lets the port/baud be overridden from the command line
        # without touching this file, e.g.:
        #   ros2 run serial_bridge_test direction_to_serial --ros-args -p serial_port:=/dev/ttyUSB1
        self.declare_parameter('serial_port', '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0')
        self.declare_parameter('baud_rate', 115200)

        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('baud_rate').get_parameter_value().integer_value

        # opened once here, not inside the callback — reopening per-message would be
        # slow and would drop the connection state between messages
        self.serial_conn = serial.Serial(port, baud, timeout=1)
        self.get_logger().info(f'Opened serial port {port} at {baud} baud')

        self.subscription = self.create_subscription(String, 'Direction', self.serial_bridge, 10)

    def serial_bridge(self, direction):
        self.get_logger().info(f'Listening: {direction.data}')

        # serial.write() needs bytes, not str — .encode() converts it.
        # '\n' is appended so the ESP32 side can tell where one command ends
        # and the next begins, once you write the code to read it there.
        self.serial_conn.write((direction.data + '\n').encode('utf-8'))

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