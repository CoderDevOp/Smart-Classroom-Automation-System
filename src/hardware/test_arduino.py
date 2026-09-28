from arduino import ArduinoController
import time


arduino = ArduinoController(
    port="COM3",
    baud_rate=9600
)


# --------------------------------
# CONNECT
# --------------------------------

if not arduino.connect():

    print("Could not connect to Arduino.")

    exit()


# --------------------------------
# LIGHT + FAN ON
# --------------------------------

print()
print("Turning LIGHT and FAN ON...")

arduino.send_command(
    "Z1L1F1"
)

time.sleep(5)


# --------------------------------
# LIGHT + FAN OFF
# --------------------------------

print()
print("Turning LIGHT and FAN OFF...")

arduino.send_command(
    "Z1L0F0"
)

time.sleep(2)


# --------------------------------
# DISCONNECT
# --------------------------------

arduino.disconnect()

print()
print("Arduino test completed.")