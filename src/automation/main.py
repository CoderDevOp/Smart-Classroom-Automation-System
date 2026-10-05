import cv2
from pathlib import Path
import sys
import time
import ctypes
from datetime import datetime


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

LIVE_FRAME_PATH = (
    PROJECT_ROOT
    / "data"
    / "live_camera.jpg"
)

LIVE_FRAME_TEMP_PATH = (
    PROJECT_ROOT
    / "data"
    / "live_camera.tmp.jpg"
)


sys.path.append(
    str(PROJECT_ROOT / "src")
)


from vision.detector import PersonDetector
from vision.zones import ZoneManager
from automation.controller import AutomationController
from hardware.arduino import ArduinoController
from database.database import ClassroomDatabase


def q_pressed():

    return (
        ctypes.windll.user32.GetAsyncKeyState(
            0x51
        )
        & 0x8000
    ) != 0


def get_day_context():

    today = datetime.now()

    weekday = today.weekday()

    if weekday == 6:

        return {
            "day_type": "Holiday",
            "working_day": 0,
            "holiday": 1,
            "exam_day": 0,
            "special_class": 0,
            "event_day": 0,
            "vacation_day": 0
        }

    if weekday == 5:

        return {
            "day_type": "Saturday_Class",
            "working_day": 1,
            "holiday": 0,
            "exam_day": 0,
            "special_class": 0,
            "event_day": 0,
            "vacation_day": 0
        }

    return {
        "day_type": "Normal_Weekday",
        "working_day": 1,
        "holiday": 0,
        "exam_day": 0,
        "special_class": 0,
        "event_day": 0,
        "vacation_day": 0
    }


def save_live_frame(frame):

    try:

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                85
            ]
        )

        if not success:
            return

        LIVE_FRAME_TEMP_PATH.write_bytes(
            encoded.tobytes()
        )

        LIVE_FRAME_TEMP_PATH.replace(
            LIVE_FRAME_PATH
        )

    except Exception as error:

        print(
            f"Could not update live camera: {error}"
        )


print()
print("========================================")
print("   SMART CLASSROOM AUTOMATION")
print("========================================")
print()


detector = PersonDetector()


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


automation = AutomationController(
    zone_manager.zones,
    light_on_delay=2,
    fan_on_delay=4,
    light_off_delay=3,
    fan_off_delay=3
)


database = ClassroomDatabase(
    str(DATABASE_PATH)
)


print(
    "Database connected."
)


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


previous_people_count = {
    zone["name"]: 0
    for zone in zone_manager.zones
}


appliance_start_time = {
    zone["name"]: {
        "light": None,
        "fan": None
    }
    for zone in zone_manager.zones
}


LIGHT_POWER_WATTS = 40
FAN_POWER_WATTS = 75


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


daily_max_total_people = 0


current_total_people = 0


last_daily_database_update = 0


DAILY_DATABASE_UPDATE_INTERVAL = 10


previous_loop_time = time.time()


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
    "Camera is being streamed to the dashboard."
)

print(
    "Press Q to stop."
)

print()


try:

    while True:

        if q_pressed():

            print(
                "Q pressed. Stopping system..."
            )

            break


        success, frame = camera.read()


        if not success:

            print(
                "ERROR: Could not read camera frame."
            )

            break


        current_time = time.time()


        elapsed_seconds = (
            current_time
            - previous_loop_time
        )


        previous_loop_time = current_time


        if elapsed_seconds < 0:

            elapsed_seconds = 0


        if elapsed_seconds > 1:

            elapsed_seconds = 1


        persons = detector.detect(
            frame
        )


        frame = zone_manager.draw_zones(
            frame
        )


        zone_counts = {
            zone["name"]: 0
            for zone in zone_manager.zones
        }


        outside_count = 0


        for person in persons:

            x1, y1, x2, y2 = (
                person["box"]
            )

            confidence = (
                person["confidence"]
            )


            center_x = int(
                (x1 + x2) / 2
            )

            top_y = y1


            zone = zone_manager.get_zone(
                center_x,
                top_y
            )


            if zone in zone_counts:

                zone_counts[zone] += 1

            else:

                outside_count += 1


            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


            cv2.circle(
                frame,
                (center_x, top_y),
                6,
                (0, 0, 255),
                -1
            )


            label = (
                f"{zone} "
                f"{confidence:.2f}"
            )


            cv2.putText(
                frame,
                label,
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


        current_total_people = len(
            persons
        )


        if current_total_people > daily_max_total_people:

            daily_max_total_people = (
                current_total_people
            )


        for zone_name, people_count in (
            zone_counts.items()
        ):

            if (
                people_count
                > daily_zone_people_max[
                    zone_name
                ]
            ):

                daily_zone_people_max[
                    zone_name
                ] = people_count


            current_min = (
                daily_zone_people_min[
                    zone_name
                ]
            )


            if current_min is None:

                daily_zone_people_min[
                    zone_name
                ] = people_count

            elif people_count < current_min:

                daily_zone_people_min[
                    zone_name
                ] = people_count


            if people_count > 0:

                daily_zone_occupancy_duration[
                    zone_name
                ] += elapsed_seconds


        for zone_name, people_count in (
            zone_counts.items()
        ):

            previous_count = (
                previous_people_count[
                    zone_name
                ]
            )


            if people_count != previous_count:

                print(
                    f"DB: {zone_name} "
                    f"occupancy = "
                    f"{people_count}"
                )


                previous_people_count[
                    zone_name
                ] = people_count


        decisions = automation.update(
            zone_counts
        )


        for index, zone in enumerate(
            zone_manager.zones,
            start=1
        ):

            zone_name = zone["name"]


            data = decisions[
                zone_name
            ]


            if data["light"]:

                daily_light_hours[
                    zone_name
                ] += (
                    elapsed_seconds
                    / 3600
                )


            if data["fan"]:

                daily_fan_hours[
                    zone_name
                ] += (
                    elapsed_seconds
                    / 3600
                )


            if data["light_changed"]:

                new_light_state = (
                    data["light"]
                )


                if new_light_state:

                    appliance_start_time[
                        zone_name
                    ]["light"] = (
                        current_time
                    )

                else:

                    appliance_start_time[
                        zone_name
                    ]["light"] = None


                print(
                    f"DB: {zone_name} "
                    f"Light -> "
                    f"{'ON' if new_light_state else 'OFF'}"
                )


            if data["fan_changed"]:

                new_fan_state = (
                    data["fan"]
                )


                if new_fan_state:

                    appliance_start_time[
                        zone_name
                    ]["fan"] = (
                        current_time
                    )

                else:

                    appliance_start_time[
                        zone_name
                    ]["fan"] = None


                print(
                    f"DB: {zone_name} "
                    f"Fan -> "
                    f"{'ON' if new_fan_state else 'OFF'}"
                )


            if data["state_changed"]:

                if arduino_connected:

                    arduino.send_zone_command(
                        zone_number=index,
                        light=data["light"],
                        fan=data["fan"]
                    )


        if (
            current_time
            - last_daily_database_update
            >= DAILY_DATABASE_UPDATE_INTERVAL
        ):

            today = (
                datetime.now()
                .strftime("%Y-%m-%d")
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


            zone1_status = int(
                zone1_current_people > 0
            )


            zone2_status = int(
                zone2_current_people > 0
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


            average_class_duration = (
                (
                    daily_zone_occupancy_duration[
                        zone1_name
                    ]
                    +
                    daily_zone_occupancy_duration[
                        zone2_name
                    ]
                )
                / 2
            )


            zone1_energy_kwh = (
                (
                    daily_light_hours[
                        zone1_name
                    ]
                    * LIGHT_POWER_WATTS
                )
                +
                (
                    daily_fan_hours[
                        zone1_name
                    ]
                    * FAN_POWER_WATTS
                )
            ) / 1000


            zone2_energy_kwh = (
                (
                    daily_light_hours[
                        zone2_name
                    ]
                    * LIGHT_POWER_WATTS
                )
                +
                (
                    daily_fan_hours[
                        zone2_name
                    ]
                    * FAN_POWER_WATTS
                )
            ) / 1000


            daily_energy_kwh = (
                zone1_energy_kwh
                + zone2_energy_kwh
            )


            day_context = (
                get_day_context()
            )


            database.save_daily_features(
                date=today,
                day_type=(
                    day_context["day_type"]
                ),
                max_zone1_people=(
                    daily_zone_people_max[
                        zone1_name
                    ]
                ),
                max_zone2_people=(
                    daily_zone_people_max[
                        zone2_name
                    ]
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
                ),
                zone1_energy_kwh=(
                    zone1_energy_kwh
                ),
                zone2_energy_kwh=(
                    zone2_energy_kwh
                ),
                daily_energy_kwh=(
                    daily_energy_kwh
                ),
                working_day=(
                    day_context["working_day"]
                ),
                holiday=(
                    day_context["holiday"]
                ),
                exam_day=(
                    day_context["exam_day"]
                ),
                special_class=(
                    day_context["special_class"]
                ),
                event_day=(
                    day_context["event_day"]
                ),
                vacation_day=(
                    day_context["vacation_day"]
                ),
                temperature=0.0,
                humidity=0.0,
                average_class_duration=(
                    average_class_duration
                )
            )


            last_daily_database_update = (
                current_time
            )


        y_position = 25


        for zone in zone_manager.zones:

            zone_name = zone["name"]

            people = zone_counts.get(
                zone_name,
                0
            )

            light = (
                "ON"
                if decisions[
                    zone_name
                ]["light"]
                else "OFF"
            )

            fan = (
                "ON"
                if decisions[
                    zone_name
                ]["fan"]
                else "OFF"
            )


            text = (
                f"{zone_name}: "
                f"People={people} "
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


        arduino_status = (
            "Arduino: CONNECTED"
            if arduino_connected
            else "Arduino: DISCONNECTED"
        )


        cv2.putText(
            frame,
            arduino_status,
            (15, y_position),
            cv2.FONT_HERSHEY_COMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA
        )


        y_position += 25


        cv2.putText(
            frame,
            "Dashboard: LIVE",
            (15, y_position),
            cv2.FONT_HERSHEY_COMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )


        save_live_frame(
            frame
        )


finally:

    try:

        today = (
            datetime.now()
            .strftime("%Y-%m-%d")
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


        zone1_status = int(
            zone1_current_people > 0
        )


        zone2_status = int(
            zone2_current_people > 0
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


        average_class_duration = (
            (
                daily_zone_occupancy_duration[
                    zone1_name
                ]
                +
                daily_zone_occupancy_duration[
                    zone2_name
                ]
            )
            / 2
        )


        zone1_energy_kwh = (
            (
                daily_light_hours[
                    zone1_name
                ]
                * LIGHT_POWER_WATTS
            )
            +
            (
                daily_fan_hours[
                    zone1_name
                ]
                * FAN_POWER_WATTS
            )
        ) / 1000


        zone2_energy_kwh = (
            (
                daily_light_hours[
                    zone2_name
                ]
                * LIGHT_POWER_WATTS
            )
            +
            (
                daily_fan_hours[
                    zone2_name
                ]
                * FAN_POWER_WATTS
            )
        ) / 1000


        daily_energy_kwh = (
            zone1_energy_kwh
            + zone2_energy_kwh
        )


        day_context = (
            get_day_context()
        )


        database.save_daily_features(
            date=today,
            day_type=(
                day_context["day_type"]
            ),
            max_zone1_people=(
                daily_zone_people_max[
                    zone1_name
                ]
            ),
            max_zone2_people=(
                daily_zone_people_max[
                    zone2_name
                ]
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
            ),
            zone1_energy_kwh=(
                zone1_energy_kwh
            ),
            zone2_energy_kwh=(
                zone2_energy_kwh
            ),
            daily_energy_kwh=(
                daily_energy_kwh
            ),
            working_day=(
                day_context["working_day"]
            ),
            holiday=(
                day_context["holiday"]
            ),
            exam_day=(
                day_context["exam_day"]
            ),
            special_class=(
                day_context["special_class"]
            ),
            event_day=(
                day_context["event_day"]
            ),
            vacation_day=(
                day_context["vacation_day"]
            ),
            temperature=0.0,
            humidity=0.0,
            average_class_duration=(
                average_class_duration
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


    print(
        "Cleaning up..."
    )


    camera.release()


    arduino.disconnect()


    try:

        if LIVE_FRAME_TEMP_PATH.exists():

            LIVE_FRAME_TEMP_PATH.unlink()

    except Exception:

        pass


    print(
        "Automation stopped."
    )