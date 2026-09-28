import cv2
from pathlib import Path
import sys
import time
import ctypes


# =================================
# PROJECT PATH
# =================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ZONE_CONFIG = PROJECT_ROOT / "config" / "zones.json"

DATABASE_PATH = PROJECT_ROOT / "data" / "classroom.db"


# =================================
# IMPORT MODULES
# =================================

sys.path.append(
    str(PROJECT_ROOT / "src")
)


from vision.detector import PersonDetector
from vision.zones import ZoneManager
from automation.controller import AutomationController
from hardware.arduino import ArduinoController
from database.database import ClassroomDatabase


# =================================
# GLOBAL Q KEY CHECK
# =================================

def q_pressed():

    # Windows virtual key code for Q = 0x51
    return (
        ctypes.windll.user32.GetAsyncKeyState(0x51)
        & 0x8000
    ) != 0


# =================================
# START
# =================================

print(
    "Starting Smart Classroom Automation..."
)

print(
    f"Zone config: {ZONE_CONFIG}"
)

print(
    f"Database: {DATABASE_PATH}"
)


# =================================
# YOLO
# =================================

detector = PersonDetector()


# =================================
# ZONES
# =================================

zone_manager = ZoneManager(
    str(ZONE_CONFIG)
)

print(
    f"Loaded {len(zone_manager.zones)} zones."
)


# =================================
# AUTOMATION
# =================================

automation = AutomationController(

    zone_manager.zones,

    light_on_delay=2,

    fan_on_delay=4,

    light_off_delay=3,

    fan_off_delay=3
)


# =================================
# DATABASE
# =================================

database = ClassroomDatabase(
    str(DATABASE_PATH)
)

print(
    "Database connected."
)


# =================================
# ARDUINO
# =================================

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


# =================================
# OCCUPANCY TRACKING
# =================================

previous_people_count = {

    zone["name"]: 0

    for zone in zone_manager.zones
}


# =================================
# APPLIANCE TIMERS
# =================================

appliance_start_time = {

    zone["name"]: {

        "light": None,

        "fan": None

    }

    for zone in zone_manager.zones
}


# =================================
# SESSION OCCUPANCY
# =================================

appliance_start_people = {

    zone["name"]: {

        "light": None,

        "fan": None

    }

    for zone in zone_manager.zones
}


# =================================
# POWER RATINGS
# =================================

LIGHT_POWER_WATTS = 40

FAN_POWER_WATTS = 75


# =================================
# CAMERA
# =================================

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
    "Press Q anywhere to stop."
)


# =================================
# MAIN LOOP
# =================================

try:

    while True:

        # ---------------------------------
        # GLOBAL Q CHECK
        # ---------------------------------

        if q_pressed():

            print(
                "Q pressed. Stopping system..."
            )

            break


        # ---------------------------------
        # CAMERA FRAME
        # ---------------------------------

        success, frame = camera.read()


        if not success:

            print(
                "ERROR: Could not read camera frame."
            )

            break


        current_time = time.time()


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
        # ZONE COUNTS
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


            # ---------------------------------
            # TOP CENTER
            # ---------------------------------

            center_x = int(
                (x1 + x2) / 2
            )

            top_y = y1


            # ---------------------------------
            # FIND ZONE
            # ---------------------------------

            zone = zone_manager.get_zone(

                center_x,

                top_y
            )


            # ---------------------------------
            # COUNT
            # ---------------------------------

            if zone in zone_counts:

                zone_counts[zone] += 1

            else:

                outside_count += 1


            # ---------------------------------
            # BOUNDING BOX
            # ---------------------------------

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                2
            )


            # ---------------------------------
            # TOP CENTER POINT
            # ---------------------------------

            cv2.circle(

                frame,

                (center_x, top_y),

                6,

                (0, 0, 255),

                -1
            )


            # ---------------------------------
            # LABEL
            # ---------------------------------

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
        # LOG OCCUPANCY CHANGES
        # =================================

        for zone_name, people_count in zone_counts.items():

            previous_count = previous_people_count[
                zone_name
            ]


            if people_count != previous_count:

                database.log_occupancy(

                    zone_name=zone_name,

                    people_count=people_count
                )


                print(

                    f"DB: {zone_name} "

                    f"occupancy = "

                    f"{people_count}"
                )


                previous_people_count[
                    zone_name
                ] = people_count


        # =================================
        # AUTOMATION
        # =================================

        decisions = automation.update(
            zone_counts
        )


        # =================================
        # PROCESS EACH ZONE
        # =================================

        for index, zone in enumerate(

            zone_manager.zones,

            start=1
        ):

            zone_name = zone["name"]

            data = decisions[
                zone_name
            ]


            # =================================
            # LIGHT STATE CHANGE
            # =================================

            if data["light_changed"]:

                new_light_state = data["light"]


                # ---------------------------------
                # LIGHT ON
                # ---------------------------------

                if new_light_state:

                    appliance_start_time[
                        zone_name
                    ]["light"] = current_time


                    appliance_start_people[
                        zone_name
                    ]["light"] = data["people"]


                # ---------------------------------
                # LIGHT OFF
                # ---------------------------------

                else:

                    start_time = (

                        appliance_start_time[
                            zone_name
                        ]["light"]
                    )


                    start_people = (

                        appliance_start_people[
                            zone_name
                        ]["light"]
                    )


                    if start_time is not None:

                        duration_seconds = (

                            current_time

                            - start_time
                        )


                        if start_people is None:

                            start_people = 0


                        database.log_energy(

                            zone_name=zone_name,

                            appliance="light",

                            people_count=start_people,

                            duration_seconds=duration_seconds,

                            power_watts=LIGHT_POWER_WATTS
                        )


                        print(

                            f"ENERGY: "

                            f"{zone_name} Light | "

                            f"People: {start_people} | "

                            f"{duration_seconds:.2f}s"
                        )


                        appliance_start_time[
                            zone_name
                        ]["light"] = None


                        appliance_start_people[
                            zone_name
                        ]["light"] = None


                # ---------------------------------
                # DATABASE EVENT
                # ---------------------------------

                database.log_appliance_event(

                    zone_name=zone_name,

                    appliance="light",

                    previous_state=not new_light_state,

                    current_state=new_light_state
                )


                print(

                    f"DB: {zone_name} "

                    f"Light -> "

                    f"{'ON' if new_light_state else 'OFF'}"
                )


            # =================================
            # FAN STATE CHANGE
            # =================================

            if data["fan_changed"]:

                new_fan_state = data["fan"]


                # ---------------------------------
                # FAN ON
                # ---------------------------------

                if new_fan_state:

                    appliance_start_time[
                        zone_name
                    ]["fan"] = current_time


                    appliance_start_people[
                        zone_name
                    ]["fan"] = data["people"]


                # ---------------------------------
                # FAN OFF
                # ---------------------------------

                else:

                    start_time = (

                        appliance_start_time[
                            zone_name
                        ]["fan"]
                    )


                    start_people = (

                        appliance_start_people[
                            zone_name
                        ]["fan"]
                    )


                    if start_time is not None:

                        duration_seconds = (

                            current_time

                            - start_time
                        )


                        if start_people is None:

                            start_people = 0


                        database.log_energy(

                            zone_name=zone_name,

                            appliance="fan",

                            people_count=start_people,

                            duration_seconds=duration_seconds,

                            power_watts=FAN_POWER_WATTS
                        )


                        print(

                            f"ENERGY: "

                            f"{zone_name} Fan | "

                            f"People: {start_people} | "

                            f"{duration_seconds:.2f}s"
                        )


                        appliance_start_time[
                            zone_name
                        ]["fan"] = None


                        appliance_start_people[
                            zone_name
                        ]["fan"] = None


                # ---------------------------------
                # DATABASE EVENT
                # ---------------------------------

                database.log_appliance_event(

                    zone_name=zone_name,

                    appliance="fan",

                    previous_state=not new_fan_state,

                    current_state=new_fan_state
                )


                print(

                    f"DB: {zone_name} "

                    f"Fan -> "

                    f"{'ON' if new_fan_state else 'OFF'}"
                )


            # =================================
            # ARDUINO
            # =================================

            if data["state_changed"]:

                if arduino_connected:

                    arduino.send_zone_command(

                        zone_number=index,

                        light=data["light"],

                        fan=data["fan"]
                    )


        # =================================
        # DISPLAY
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
        # OUTSIDE
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

        status = (

            "Arduino: CONNECTED"

            if arduino_connected

            else "Arduino: DISCONNECTED"
        )


        cv2.putText(

            frame,

            status,

            (15, y_position),

            cv2.FONT_HERSHEY_COMPLEX,

            0.5,

            (0, 0, 255),

            1,

            cv2.LINE_AA
        )


        y_position += 25


        # =================================
        # STOP MESSAGE
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


        # ---------------------------------
        # OpenCV keyboard check
        # ---------------------------------

        key = cv2.waitKey(1) & 0xFF


        if key == ord("q") or key == ord("Q"):

            print(
                "Q pressed. Stopping system..."
            )

            break


# =================================
# CLEANUP
# =================================

except KeyboardInterrupt:

    print()
    print(
        "Ctrl+C pressed. Stopping system..."
    )


finally:

    print(
        "Cleaning up..."
    )

    camera.release()

    cv2.destroyAllWindows()

    arduino.disconnect()

    print(
        "Automation stopped."
    )