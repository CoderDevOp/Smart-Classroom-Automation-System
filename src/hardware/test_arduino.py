from arduino import ArduinoController
import time


print()
print("========================================")
print("   SMART CLASSROOM ARDUINO TEST")
print("========================================")
print()


# ----------------------------------------
# CREATE ARDUINO CONTROLLER
# ----------------------------------------

arduino = ArduinoController(
    port="COM3",
    baud_rate=9600,
    timeout=1
)


# ----------------------------------------
# CONNECT
# ----------------------------------------

if not arduino.connect():

    print()
    print("ERROR: Could not connect to Arduino.")
    print("Check:")
    print("1. Arduino USB cable")
    print("2. COM3")
    print("3. Arduino IDE is closed")
    print()

    exit()


print()


# ----------------------------------------
# TEST 1
# ZONE 1 ON
# ----------------------------------------

print("----------------------------------------")
print("TEST 1")
print("Zone 1 LIGHT + FAN -> ON")
print("----------------------------------------")

arduino.send_zone_command(
    zone_number=1,
    light=True,
    fan=True
)

time.sleep(3)


# ----------------------------------------
# TEST 2
# ZONE 1 OFF
# ----------------------------------------

print()
print("----------------------------------------")
print("TEST 2")
print("Zone 1 LIGHT + FAN -> OFF")
print("----------------------------------------")

arduino.send_zone_command(
    zone_number=1,
    light=False,
    fan=False
)

time.sleep(3)


# ----------------------------------------
# TEST 3
# ZONE 2 ON
# ----------------------------------------

print()
print("----------------------------------------")
print("TEST 3")
print("Zone 2 LIGHT + FAN -> ON")
print("----------------------------------------")

arduino.send_zone_command(
    zone_number=2,
    light=True,
    fan=True
)

time.sleep(3)


# ----------------------------------------
# TEST 4
# ZONE 2 OFF
# ----------------------------------------

print()
print("----------------------------------------")
print("TEST 4")
print("Zone 2 LIGHT + FAN -> OFF")
print("----------------------------------------")

arduino.send_zone_command(
    zone_number=2,
    light=False,
    fan=False
)

time.sleep(2)


# ----------------------------------------
# DISCONNECT
# ----------------------------------------

arduino.disconnect()


print()
print("========================================")
print("   TEST COMPLETE")
print("========================================")
print()