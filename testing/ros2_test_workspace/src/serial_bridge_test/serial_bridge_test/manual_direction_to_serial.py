import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial   # pyserial — talks to the Arduino Nano over the USB serial connection

# Find this with `ls -l /dev/serial/by-id/` on the RPi — use the by-id path,
# not the /dev/ttyUSB0 it resolves to, since that number isn't stable across
# reboots/replugs but the by-id symlink is.
SERIAL_PORT = '/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'
BAUD_RATE = 115200


class ManualDirectionToSerial(Node):

    def __init__(self):
        super().__init__('manual_direction_to_serial')

        # opened once here, not inside the callback — reopening per-message would be
        # slow and would drop the connection state between messages
        self.serial_conn = serial.Serial(SERIAL_PORT, BAUD_RATE) # start serial connection to Nano
        self.get_logger().info(f'Opened serial port {SERIAL_PORT} at {BAUD_RATE} baud')

        self.subscription = self.create_subscription(String, 'ManualDirection', self.serial_bridge, 10)

    def serial_bridge(self, direction):
        self.get_logger().info(f'Listening: {direction.data}')

        # serial.write() needs bytes, not str — .encode() converts it.
        # '\n' marks where one command ends and the next begins for the Nano side.
        self.serial_conn.write((direction.data + '\n').encode('utf-8')) # Convert String to Bytes

    def destroy_node(self):
        # make sure the serial port is released cleanly on shutdown (Ctrl+C)
        self.serial_conn.close()
        super().destroy_node()


def main():
    rclpy.init()
    manual_direction_to_serial = ManualDirectionToSerial()
    rclpy.spin(manual_direction_to_serial)
    manual_direction_to_serial.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
