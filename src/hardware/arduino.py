import serial
import time


class ArduinoController:

    def __init__(
        self,
        port="COM3",
        baud_rate=9600,
        timeout=1
    ):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout

        self.serial_connection = None

    def connect(self):

        try:

            self.serial_connection = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=self.timeout
            )

            time.sleep(2)

            print(
                f"Arduino connected on {self.port}"
            )

            return True

        except serial.SerialException as error:

            print(
                f"Arduino connection failed: {error}"
            )

            self.serial_connection = None

            return False

    def send_command(self, command):

        if self.serial_connection is None:

            print("Arduino is not connected.")

            return False

        try:

            command = command.strip()

            self.serial_connection.write(
                (command + "\n").encode()
            )

            print(
                f"Command sent: {command}"
            )

            return True

        except serial.SerialException as error:

            print(
                f"Failed to send command: {error}"
            )

            return False

    def disconnect(self):

        if self.serial_connection:

            self.serial_connection.close()

            print("Arduino disconnected.")

            self.serial_connection = None