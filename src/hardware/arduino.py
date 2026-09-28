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
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )

            # Arduino resets when serial connection opens
            time.sleep(2)

            # Remove old messages
            self.serial_connection.reset_input_buffer()

            print(f"Arduino connected on {self.port}")

            return True

        except serial.SerialException as error:

            print(
                f"Arduino connection failed: {error}"
            )

            self.serial_connection = None

            return False

    def send_zone_command(
        self,
        zone_number,
        light,
        fan
    ):

        if self.serial_connection is None:

            print(
                "ERROR: Arduino is not connected."
            )

            return False


        command = (
            f"Z{zone_number}"
            f"L{1 if light else 0}"
            f"F{1 if fan else 0}"
        )


        try:

            print(
                f"PYTHON -> ARDUINO: {command}"
            )


            self.serial_connection.write(
                (command + "\n").encode()
            )


            self.serial_connection.flush()


            # Give Arduino a moment to process
            time.sleep(0.1)


            # Read Arduino response
            while self.serial_connection.in_waiting > 0:

                response = (
                    self.serial_connection
                    .readline()
                    .decode(
                        errors="ignore"
                    )
                    .strip()
                )

                if response:

                    print(
                        f"ARDUINO -> PYTHON: {response}"
                    )


            return True


        except serial.SerialException as error:

            print(
                f"Serial communication error: {error}"
            )

            return False

    def disconnect(self):

        if self.serial_connection:

            try:

                self.serial_connection.close()

            except serial.SerialException:

                pass

            self.serial_connection = None

            print(
                "Arduino disconnected."
            )