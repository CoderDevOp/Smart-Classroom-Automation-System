import cv2

from pathlib import Path

import sys

import time

import ctypes

from datetime import datetime


# ============================================
# PROJECT PATH
# ============================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


ZONE_CONFIG = (
    PROJECT_ROOT
    / "config"
    / "zones.json"
)


DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "classroom.db"
)


# ============================================
# IMPORT MODULES
# ============================================

sys.path.append(
    str(PROJECT_ROOT / "src")
)


from vision.detector import (
    PersonDetector
)

from vision.zones import (
    ZoneManager
)

from automation.controller import (
    AutomationController
)

from hardware.arduino import (
    ArduinoController
)

from database.database import (
    ClassroomDatabase
)


# ============================================
# Q KEY DETECTION
# ============================================

def q_pressed():

    return (
        ctypes.windll.user32.GetAsyncKeyState(
            0x51
        )
        & 0x8000
    ) != 0


# ============================================
# START
# ============================================

print()

print(
    "========================================"
)

print(
    "   SMART CLASSROOM AUTOMATION"
)

print(
    "========================================"
)

print()


# ============================================
# YOLO
# ============================================

detector = PersonDetector()


# ============================================
# ZONES
# ============================================

zone_manager = ZoneManager(
    str(ZONE_CONFIG)
)


print(
    f"Loaded {len(zone_manager.zones)} zones."
)


if len(zone_manager.zones) < 2:

    print(
        "ERROR: At least 2 zones are required."
    )

    exit()


# ============================================
# AUTOMATION
# ============================================

automation = AutomationController(

    zone_manager.zones,

    light_on_delay=2,

    fan_on_delay=4,

    light_off_delay=3,

    fan_off_delay=3
)


# ============================================
# DATABASE
# ============================================

database = ClassroomDatabase(
    str(DATABASE_PATH)
)


print(
    "Database connected."
)


# ============================================
# ARDUINO
# ============================================

arduino = ArduinoController(

    port="COM3",

    baud_rate=9600,

    timeout=1
)


arduino_connected = (
    arduino.connect()
)


if not arduino_connected:

    print(
        "WARNING: Arduino unavailable."
    )


# ============================================
# OCCUPANCY CHANGE TRACKING
# ============================================

previous_people_count = {

    zone["name"]: 0

    for zone in zone_manager.zones
}


# ============================================
# APPLIANCE START TIMES
# ============================================

appliance_start_time = {

    zone["name"]: {

        "light": None,

        "fan": None

    }

    for zone in zone_manager.zones
}


# ============================================
# PEOPLE COUNT WHEN APPLIANCE STARTS
# ============================================

appliance_start_people = {

    zone["name"]: {

        "light": None,

        "fan": None

    }

    for zone in zone_manager.zones
}


# ============================================
# POWER RATINGS
# ============================================

LIGHT_POWER_WATTS = 40

FAN_POWER_WATTS = 75


# ============================================
# DAILY FEATURE ACCUMULATORS
# ============================================

daily_zone_people_max = {

    zone["name"]: 0

    for zone in zone_manager.zones
}


daily_zone_people_min = {

    zone["name"]: None

    for zone in zone_manager.zones
}


daily_zone_occupancy_duration = {

    zone["name"]: 0.0

    for zone in zone_manager.zones
}


daily_light_hours = {

    zone["name"]: 0.0

    for zone in zone_manager.zones
}


daily_fan_hours = {

    zone["name"]: 0.0

    for zone in zone_manager.zones
}


# ============================================
# MAX TOTAL PEOPLE
# ============================================

daily_max_total_people = 0


# ============================================
# CURRENT TOTAL PEOPLE
# ============================================

current_total_people = 0


# ============================================
# DAILY DATABASE UPDATE
# ============================================

last_daily_database_update = 0

DAILY_DATABASE_UPDATE_INTERVAL = 10


# ============================================
# LOOP TIME
# ============================================

previous_loop_time = time.time()


# ============================================
# CAMERA
# ============================================

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

print()


# ============================================
# MAIN LOOP
# ============================================

try:

    while True:

        # ====================================
        # GLOBAL Q CHECK
        # ====================================

        if q_pressed():

            print(
                "Q pressed. Stopping system..."
            )

            break


        # ====================================
        # READ CAMERA
        # ====================================

        success, frame = camera.read()


        if not success:

            print(
                "ERROR: Could not read camera frame."
            )

            break


        current_time = time.time()


        # ====================================
        # CALCULATE ELAPSED TIME
        # ====================================

        elapsed_seconds = (
            current_time
            - previous_loop_time
        )


        previous_loop_time = (
            current_time
        )


        # Prevent abnormal time jumps.

        if elapsed_seconds < 0:

            elapsed_seconds = 0


        if elapsed_seconds > 1:

            elapsed_seconds = 1


        # ====================================
        # YOLO PERSON DETECTION
        # ====================================

        persons = detector.detect(
            frame
        )


        # ====================================
        # DRAW ZONES
        # ====================================

        frame = zone_manager.draw_zones(
            frame
        )


        # ====================================
        # INITIALIZE ZONE COUNTS
        # ====================================

        zone_counts = {

            zone["name"]: 0

            for zone in zone_manager.zones
        }


        outside_count = 0


        # ====================================
        # PROCESS DETECTED PEOPLE
        # ====================================

        for person in persons:

            x1, y1, x2, y2 = (
                person["box"]
            )


            confidence = (
                person["confidence"]
            )


            # =================================
            # TOP CENTER POINT
            # =================================

            center_x = int(
                (x1 + x2) / 2
            )


            top_y = y1


            # =================================
            # FIND ZONE
            # =================================

            zone = zone_manager.get_zone(

                center_x,

                top_y
            )


            # =================================
            # COUNT PERSON
            # =================================

            if zone in zone_counts:

                zone_counts[zone] += 1

            else:

                outside_count += 1


            # =================================
            # DRAW BOUNDING BOX
            # =================================

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                2
            )


            # =================================
            # DRAW TOP CENTER
            # =================================

            cv2.circle(

                frame,

                (center_x, top_y),

                6,

                (0, 0, 255),

                -1
            )


            # =================================
            # DRAW LABEL
            # =================================

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


        # ====================================
        # CURRENT TOTAL PEOPLE
        # ====================================

        current_total_people = sum(
            zone_counts.values()
        )


        # ====================================
        # UPDATE MAX TOTAL PEOPLE
        # ====================================

        if (
            current_total_people
            > daily_max_total_people
        ):

            daily_max_total_people = (
                current_total_people
            )


        # ====================================
        # UPDATE DAILY OCCUPANCY FEATURES
        # ====================================

        for zone_name, people_count in (
            zone_counts.items()
        ):

            # --------------------------------
            # MAX PEOPLE IN THIS ZONE
            # --------------------------------

            if (
                people_count
                > daily_zone_people_max[
                    zone_name
                ]
            ):

                daily_zone_people_max[
                    zone_name
                ] = people_count


            # --------------------------------
            # MIN PEOPLE IN THIS ZONE
            # --------------------------------

            if (
                daily_zone_people_min[
                    zone_name
                ] is None
            ):

                daily_zone_people_min[
                    zone_name
                ] = people_count

            elif (
                people_count
                < daily_zone_people_min[
                    zone_name
                ]
            ):

                daily_zone_people_min[
                    zone_name
                ] = people_count


            # --------------------------------
            # OCCUPANCY DURATION
            # --------------------------------

            if people_count > 0:

                daily_zone_occupancy_duration[
                    zone_name
                ] += elapsed_seconds


        # ====================================
        # LOG OCCUPANCY CHANGES
        # ====================================

        for zone_name, people_count in (
            zone_counts.items()
        ):

            previous_count = (
                previous_people_count[
                    zone_name
                ]
            )


            if (
                people_count
                != previous_count
            ):

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


        # ====================================
        # AUTOMATION
        # ====================================

        decisions = automation.update(
            zone_counts
        )


        # ====================================
        # PROCESS EACH ZONE
        # ====================================

        for index, zone in enumerate(

            zone_manager.zones,

            start=1

        ):

            zone_name = zone["name"]


            data = decisions[
                zone_name
            ]


            # =================================
            # LIGHT HOURS
            # =================================

            if data["light"]:

                daily_light_hours[
                    zone_name
                ] += (

                    elapsed_seconds
                    / 3600

                )


            # =================================
            # FAN HOURS
            # =================================

            if data["fan"]:

                daily_fan_hours[
                    zone_name
                ] += (

                    elapsed_seconds
                    / 3600

                )


            # =================================
            # LIGHT STATE CHANGE
            # =================================

            if data["light_changed"]:

                new_light_state = (
                    data["light"]
                )


                # --------------------------------
                # LIGHT ON
                # --------------------------------

                if new_light_state:

                    appliance_start_time[
                        zone_name
                    ]["light"] = (
                        current_time
                    )


                    appliance_start_people[
                        zone_name
                    ]["light"] = (
                        data["people"]
                    )


                # --------------------------------
                # LIGHT OFF
                # --------------------------------

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

                            people_count=(
                                start_people
                            ),

                            duration_seconds=(
                                duration_seconds
                            ),

                            power_watts=(
                                LIGHT_POWER_WATTS
                            )
                        )


                        print(

                            f"ENERGY: "

                            f"{zone_name} Light | "

                            f"People: "

                            f"{start_people} | "

                            f"{duration_seconds:.2f}s"
                        )


                        appliance_start_time[
                            zone_name
                        ]["light"] = None


                        appliance_start_people[
                            zone_name
                        ]["light"] = None


                # --------------------------------
                # APPLIANCE EVENT
                # --------------------------------

                database.log_appliance_event(

                    zone_name=zone_name,

                    appliance="light",

                    previous_state=(
                        not new_light_state
                    ),

                    current_state=(
                        new_light_state
                    )
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

                new_fan_state = (
                    data["fan"]
                )


                # --------------------------------
                # FAN ON
                # --------------------------------

                if new_fan_state:

                    appliance_start_time[
                        zone_name
                    ]["fan"] = (
                        current_time
                    )


                    appliance_start_people[
                        zone_name
                    ]["fan"] = (
                        data["people"]
                    )


                # --------------------------------
                # FAN OFF
                # --------------------------------

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

                            people_count=(
                                start_people
                            ),

                            duration_seconds=(
                                duration_seconds
                            ),

                            power_watts=(
                                FAN_POWER_WATTS
                            )
                        )


                        print(

                            f"ENERGY: "

                            f"{zone_name} Fan | "

                            f"People: "

                            f"{start_people} | "

                            f"{duration_seconds:.2f}s"
                        )


                        appliance_start_time[
                            zone_name
                        ]["fan"] = None


                        appliance_start_people[
                            zone_name
                        ]["fan"] = None


                # --------------------------------
                # APPLIANCE EVENT
                # --------------------------------

                database.log_appliance_event(

                    zone_name=zone_name,

                    appliance="fan",

                    previous_state=(
                        not new_fan_state
                    ),

                    current_state=(
                        new_fan_state
                    )
                )


                print(

                    f"DB: {zone_name} "

                    f"Fan -> "

                    f"{'ON' if new_fan_state else 'OFF'}"
                )


            # =================================
            # SEND TO ARDUINO
            # =================================

            if data["state_changed"]:

                if arduino_connected:

                    arduino.send_zone_command(

                        zone_number=index,

                        light=data["light"],

                        fan=data["fan"]
                    )


        # ====================================
        # SAVE DAILY FEATURES EVERY 10 SEC
        # ====================================

        if (

            current_time
            - last_daily_database_update

            >=

            DAILY_DATABASE_UPDATE_INTERVAL

        ):

            today = (

                datetime.now()

                .strftime(
                    "%Y-%m-%d"
                )

            )


            # =================================
            # ZONE 1
            # =================================

            zone1_name = (
                zone_manager.zones[0]["name"]
            )


            zone1_current_people = (
                zone_counts.get(
                    zone1_name,
                    0
                )
            )


            zone1_status = int(
                zone1_current_people > 0
            )


            zone1_min = (
                daily_zone_people_min[
                    zone1_name
                ]
            )


            if zone1_min is None:

                zone1_min = 0


            # =================================
            # ZONE 2
            # =================================

            zone2_name = (
                zone_manager.zones[1]["name"]
            )


            zone2_current_people = (
                zone_counts.get(
                    zone2_name,
                    0
                )
            )


            zone2_status = int(
                zone2_current_people > 0
            )


            zone2_min = (
                daily_zone_people_min[
                    zone2_name
                ]
            )


            if zone2_min is None:

                zone2_min = 0


            # =================================
            # MAX ZONE PEOPLE
            # =================================

            max_zone_people = max(

                daily_zone_people_max[
                    zone1_name
                ],

                daily_zone_people_max[
                    zone2_name
                ]
            )


            # =================================
            # MIN ZONE PEOPLE
            # =================================

            min_zone_people = min(

                zone1_min,

                zone2_min
            )


            # =================================
            # SAVE DAILY DATA
            # =================================

            database.save_daily_features(

                date=today,

                zone1_people_count=(

                    daily_zone_people_max[
                        zone1_name
                    ]

                ),

                zone2_people_count=(

                    daily_zone_people_max[
                        zone2_name
                    ]

                ),

                max_zone_people=(

                    max_zone_people

                ),

                max_total_people_count=(

                    daily_max_total_people

                ),

                zone1_occupancy_status=(

                    zone1_status

                ),

                zone2_occupancy_status=(

                    zone2_status

                ),

                zone1_occupancy_duration=(

                    daily_zone_occupancy_duration[
                        zone1_name
                    ]

                ),

                zone2_occupancy_duration=(

                    daily_zone_occupancy_duration[
                        zone2_name
                    ]

                ),

                zone1_light_hours=(

                    daily_light_hours[
                        zone1_name
                    ]

                ),

                zone1_fan_hours=(

                    daily_fan_hours[
                        zone1_name
                    ]

                ),

                zone2_light_hours=(

                    daily_light_hours[
                        zone2_name
                    ]

                ),

                zone2_fan_hours=(

                    daily_fan_hours[
                        zone2_name
                    ]

                )
            )


            # =================================
            # PRINT DAILY FEATURES
            # =================================

            print()

            print(
                "----------------------------------------"
            )

            print(
                "DAILY FEATURES UPDATED"
            )

            print(
                "----------------------------------------"
            )

            print(
                f"Date: {today}"
            )

            print(

                f"Zone 1 max people: "

                f"{daily_zone_people_max[zone1_name]}"

            )

            print(

                f"Zone 2 max people: "

                f"{daily_zone_people_max[zone2_name]}"

            )

            print(

                f"Max total people: "

                f"{daily_max_total_people}"

            )

            print(

                f"Zone 1 light hours: "

                f"{daily_light_hours[zone1_name]:.4f}"

            )

            print(

                f"Zone 1 fan hours: "

                f"{daily_fan_hours[zone1_name]:.4f}"

            )

            print(

                f"Zone 2 light hours: "

                f"{daily_light_hours[zone2_name]:.4f}"

            )

            print(

                f"Zone 2 fan hours: "

                f"{daily_fan_hours[zone2_name]:.4f}"

            )

            print(
                "----------------------------------------"
            )

            print()


            last_daily_database_update = (
                current_time
            )


        # ====================================
        # DISPLAY ZONE INFORMATION
        # ====================================

        y_position = 30


        for zone_name, data in (
            decisions.items()
        ):

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


        # ====================================
        # OUTSIDE
        # ====================================

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


        # ====================================
        # TOTAL CURRENT PEOPLE
        # ====================================

        cv2.putText(

            frame,

            f"Total: {current_total_people}",

            (15, y_position),

            cv2.FONT_HERSHEY_COMPLEX,

            0.5,

            (0, 0, 255),

            1,

            cv2.LINE_AA

        )


        y_position += 25


        # ====================================
        # MAX TOTAL TODAY
        # ====================================

        cv2.putText(

            frame,

            f"Max Today: {daily_max_total_people}",

            (15, y_position),

            cv2.FONT_HERSHEY_COMPLEX,

            0.5,

            (0, 0, 255),

            1,

            cv2.LINE_AA

        )


        y_position += 25


        # ====================================
        # ARDUINO STATUS
        # ====================================

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


        # ====================================
        # STOP
        # ====================================

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


        # ====================================
        # SHOW CAMERA
        # ====================================

        cv2.imshow(

            "Smart Classroom Automation",

            frame

        )


        # ====================================
        # QUIT
        # ====================================

        key = (

            cv2.waitKey(1)

            & 0xFF

        )


        if (

            key == ord("q")

            or key == ord("Q")

        ):

            print(
                "Q pressed. Stopping system..."
            )

            break


finally:

    # ========================================
    # FINAL DAILY DATABASE SAVE
    # ========================================

    try:

        today = (

            datetime.now()

            .strftime(
                "%Y-%m-%d"
            )

        )


        zone1_name = (
            zone_manager.zones[0]["name"]
        )


        zone2_name = (
            zone_manager.zones[1]["name"]
        )


        zone1_current_people = (
            zone_counts.get(
                zone1_name,
                0
            )
        )


        zone2_current_people = (
            zone_counts.get(
                zone2_name,
                0
            )
        )


        zone1_min = (
            daily_zone_people_min[
                zone1_name
            ]
        )


        zone2_min = (
            daily_zone_people_min[
                zone2_name
            ]
        )


        if zone1_min is None:

            zone1_min = 0


        if zone2_min is None:

            zone2_min = 0


        max_zone_people = max(

            daily_zone_people_max[
                zone1_name
            ],

            daily_zone_people_max[
                zone2_name
            ]
        )


        min_zone_people = min(

            zone1_min,

            zone2_min
        )


        database.save_daily_features(

            date=today,

            zone1_people_count=(

                daily_zone_people_max[
                    zone1_name
                ]

            ),

            zone2_people_count=(

                daily_zone_people_max[
                    zone2_name
                ]

            ),

            max_zone_people=(

                max_zone_people

            ),

            max_total_people_count=(

                daily_max_total_people

            ),

            zone1_occupancy_status=int(

                zone1_current_people > 0

            ),

            zone2_occupancy_status=int(

                zone2_current_people > 0

            ),

            zone1_occupancy_duration=(

                daily_zone_occupancy_duration[
                    zone1_name
                ]

            ),

            zone2_occupancy_duration=(

                daily_zone_occupancy_duration[
                    zone2_name
                ]

            ),

            zone1_light_hours=(

                daily_light_hours[
                    zone1_name
                ]

            ),

            zone1_fan_hours=(

                daily_fan_hours[
                    zone1_name
                ]

            ),

            zone2_light_hours=(

                daily_light_hours[
                    zone2_name
                ]

            ),

            zone2_fan_hours=(

                daily_fan_hours[
                    zone2_name
                ]

            )

        )


        print(
            "Final daily features saved."
        )


    except Exception as error:

        print(

            "Could not save final "

            f"daily features: {error}"

        )


    # ========================================
    # CLEANUP
    # ========================================

    print(
        "Cleaning up..."
    )


    camera.release()


    cv2.destroyAllWindows()


    arduino.disconnect()


    print(
        "Automation stopped."
    )