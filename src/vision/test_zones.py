import cv2
from pathlib import Path
import sys


# --------------------------------
# PROJECT PATH
# --------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ZONE_CONFIG = PROJECT_ROOT / "config" / "zones.json"


# --------------------------------
# IMPORT PROJECT MODULES
# --------------------------------

sys.path.append(
    str(PROJECT_ROOT / "src")
)


from vision.detector import PersonDetector
from vision.zones import ZoneManager
from automation.controller import AutomationController
from hardware.arduino import ArduinoController


# --------------------------------
# START
# --------------------------------

print(
    "Starting Smart Classroom Automation..."
)

print(
    f"Zone config: {ZONE_CONFIG}"
)


# --------------------------------
# YOLO
# --------------------------------

detector = PersonDetector()


# --------------------------------
# ZONE MANAGER
# --------------------------------

zone_manager = ZoneManager(
    str(ZONE_CONFIG)
)


print(
    f"Loaded {len(zone_manager.zones)} zones."
)


# --------------------------------
# AUTOMATION CONTROLLER
# --------------------------------

automation = AutomationController(

    zone_manager.zones,

    light_on_delay=2,

    fan_on_delay=4,

    light_off_delay=3,

    fan_off_delay=3
)


# --------------------------------
# ARDUINO
# --------------------------------

arduino = ArduinoController(

    port="COM3",

    baud_rate=9600,

    timeout=1
)


arduino_connected = arduino.connect()


if not arduino_connected:

    print(
        "WARNING: Arduino unavailable."
    )

    print(
        "Running without hardware control."
    )


# --------------------------------
# CAMERA
# --------------------------------

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print(
        "ERROR: Could not open webcam."
    )

    arduino.disconnect()

    exit()


print(
    "Camera opened successfully."
)

print(
    "Press Q to stop."
)


# --------------------------------
# MAIN LOOP
# --------------------------------

while True:

    success, frame = camera.read()


    if not success:

        print(
            "ERROR: Could not read camera frame."
        )

        break


    # =================================
    # PERSON DETECTION
    # =================================

    persons = detector.detect(
        frame
    )


    # =================================
    # DRAW ZONES
    # =================================

    frame = zone_manager.draw_zones(
        frame
    )


    # =================================
    # INITIALIZE COUNTS
    # =================================

    zone_counts = {

        zone["name"]: 0

        for zone in zone_manager.zones
    }


    outside_count = 0


    # =================================
    # PROCESS PERSONS
    # =================================

    for person in persons:

        x1, y1, x2, y2 = (
            person["box"]
        )

        confidence = (
            person["confidence"]
        )


        # --------------------------------
        # TOP CENTER POINT
        # --------------------------------

        center_x = int(
            (x1 + x2) / 2
        )

        top_y = y1


        # --------------------------------
        # FIND ZONE
        # --------------------------------

        zone = zone_manager.get_zone(

            center_x,

            top_y
        )


        # --------------------------------
        # COUNT
        # --------------------------------

        if zone in zone_counts:

            zone_counts[zone] += 1

        else:

            outside_count += 1


        # --------------------------------
        # BOUNDING BOX
        # --------------------------------

        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2
        )


        # --------------------------------
        # TOP CENTER RED POINT
        # --------------------------------

        cv2.circle(

            frame,

            (center_x, top_y),

            6,

            (0, 0, 255),

            -1
        )


        # --------------------------------
        # PERSON LABEL
        # --------------------------------

        cv2.putText(

            frame,

            f"{zone} {confidence:.2f}",

            (
                x1,
                max(y1 - 8, 18)
            ),

            cv2.FONT_HERSHEY_COMPLEX,

            0.45,

            (0, 0, 255),

            1,

            cv2.LINE_AA
        )


    # =================================
    # AUTOMATION DECISION
    # =================================

    decisions = automation.update(

        zone_counts
    )


    # =================================
    # SEND ONLY CHANGED STATES
    # =================================

    if arduino_connected:

        for index, zone in enumerate(

            zone_manager.zones,

            start=1
        ):

            zone_name = zone["name"]

            data = decisions[
                zone_name
            ]


            # Send command ONLY when
            # light/fan state changes

            if data["state_changed"]:

                arduino.send_zone_command(

                    zone_number=index,

                    light=data["light"],

                    fan=data["fan"]
                )


    # =================================
    # DISPLAY AUTOMATION STATUS
    # =================================

    y_position = 30


    for zone_name, data in decisions.items():

        people = data["people"]


        light = (

            "ON"

            if data["light"]

            else "OFF"
        )


        fan = (

            "ON"

            if data["fan"]

            else "OFF"
        )


        text = (

            f"{zone_name}: "

            f"{people} | "

            f"L:{light} "

            f"F:{fan}"
        )


        cv2.putText(

            frame,

            text,

            (15, y_position),

            cv2.FONT_HERSHEY_COMPLEX,

            0.5,

            (0, 0, 255),

            1,

            cv2.LINE_AA
        )


        y_position += 25


    # =================================
    # OUTSIDE COUNT
    # =================================

    cv2.putText(

        frame,

        f"Outside: {outside_count}",

        (15, y_position),

        cv2.FONT_HERSHEY_COMPLEX,

        0.5,

        (0, 0, 255),

        1,

        cv2.LINE_AA
    )


    y_position += 25


    # =================================
    # TOTAL
    # =================================

    cv2.putText(

        frame,

        f"Total: {len(persons)}",

        (15, y_position),

        cv2.FONT_HERSHEY_COMPLEX,

        0.5,

        (0, 0, 255),

        1,

        cv2.LINE_AA
    )


    y_position += 25


    # =================================
    # ARDUINO STATUS
    # =================================

    hardware_status = (

        "Arduino: CONNECTED"

        if arduino_connected

        else "Arduino: DISCONNECTED"
    )


    cv2.putText(

        frame,

        hardware_status,

        (15, y_position),

        cv2.FONT_HERSHEY_COMPLEX,

        0.5,

        (0, 0, 255),

        1,

        cv2.LINE_AA
    )


    y_position += 25


    # =================================
    # STOP
    # =================================

    cv2.putText(

        frame,

        "Q: Stop",

        (15, y_position),

        cv2.FONT_HERSHEY_COMPLEX,

        0.5,

        (0, 0, 255),

        1,

        cv2.LINE_AA
    )


    # =================================
    # SHOW
    # =================================

    cv2.imshow(

        "Smart Classroom Automation",

        frame
    )


    # =================================
    # QUIT
    # =================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =================================
# CLEANUP
# =================================

camera.release()

cv2.destroyAllWindows()

arduino.disconnect()


print(
    "Automation stopped."
)