import sqlite3
from pathlib import Path


class ClassroomDatabase:

    def __init__(
        self,
        database_path="data/classroom.db"
    ):

        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.create_tables()

    # ============================================
    # DATABASE CONNECTION
    # ============================================

    def connect(self):

        return sqlite3.connect(
            self.database_path
        )

    # ============================================
    # CREATE TABLE
    # ============================================

    def create_tables(self):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_features (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                date TEXT NOT NULL UNIQUE,

                day_type TEXT NOT NULL,

                max_zone1_people INTEGER NOT NULL DEFAULT 0,

                max_zone2_people INTEGER NOT NULL DEFAULT 0,

                max_total_people_count INTEGER NOT NULL DEFAULT 0,

                zone1_occupancy_status INTEGER NOT NULL DEFAULT 0,

                zone2_occupancy_status INTEGER NOT NULL DEFAULT 0,

                zone1_occupancy_duration REAL NOT NULL DEFAULT 0,

                zone2_occupancy_duration REAL NOT NULL DEFAULT 0,

                zone1_light_hours REAL NOT NULL DEFAULT 0,

                zone1_fan_hours REAL NOT NULL DEFAULT 0,

                zone2_light_hours REAL NOT NULL DEFAULT 0,

                zone2_fan_hours REAL NOT NULL DEFAULT 0,

                zone1_energy_kwh REAL NOT NULL DEFAULT 0,

                zone2_energy_kwh REAL NOT NULL DEFAULT 0,

                daily_energy_kwh REAL NOT NULL DEFAULT 0,

                working_day INTEGER NOT NULL DEFAULT 0,

                holiday INTEGER NOT NULL DEFAULT 0,

                exam_day INTEGER NOT NULL DEFAULT 0,

                special_class INTEGER NOT NULL DEFAULT 0,

                event_day INTEGER NOT NULL DEFAULT 0,

                vacation_day INTEGER NOT NULL DEFAULT 0,

                temperature REAL NOT NULL DEFAULT 0,

                humidity REAL NOT NULL DEFAULT 0,

                average_class_duration REAL NOT NULL DEFAULT 0

            )
            """
        )

        connection.commit()
        connection.close()

    # ============================================
    # SAVE DAILY FEATURES
    # ============================================

    def save_daily_features(
        self,
        date,
        day_type,
        max_zone1_people,
        max_zone2_people,
        max_total_people_count,
        zone1_occupancy_status,
        zone2_occupancy_status,
        zone1_occupancy_duration,
        zone2_occupancy_duration,
        zone1_light_hours,
        zone1_fan_hours,
        zone2_light_hours,
        zone2_fan_hours,
        zone1_energy_kwh,
        zone2_energy_kwh,
        daily_energy_kwh,
        working_day,
        holiday,
        exam_day,
        special_class,
        event_day,
        vacation_day,
        temperature,
        humidity,
        average_class_duration
    ):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO daily_features
            (
                date,
                day_type,

                max_zone1_people,
                max_zone2_people,
                max_total_people_count,

                zone1_occupancy_status,
                zone2_occupancy_status,

                zone1_occupancy_duration,
                zone2_occupancy_duration,

                zone1_light_hours,
                zone1_fan_hours,

                zone2_light_hours,
                zone2_fan_hours,

                zone1_energy_kwh,
                zone2_energy_kwh,
                daily_energy_kwh,

                working_day,
                holiday,
                exam_day,
                special_class,
                event_day,
                vacation_day,

                temperature,
                humidity,

                average_class_duration
            )

            VALUES
            (
                ?,
                ?,

                ?,
                ?,
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,
                ?,

                ?,
                ?,
                ?,

                ?,
                ?,
                ?,
                ?,
                ?,
                ?,

                ?,
                ?,

                ?
            )

            ON CONFLICT(date)
            DO UPDATE SET

                day_type =
                    excluded.day_type,

                max_zone1_people =
                    excluded.max_zone1_people,

                max_zone2_people =
                    excluded.max_zone2_people,

                max_total_people_count =
                    excluded.max_total_people_count,

                zone1_occupancy_status =
                    excluded.zone1_occupancy_status,

                zone2_occupancy_status =
                    excluded.zone2_occupancy_status,

                zone1_occupancy_duration =
                    excluded.zone1_occupancy_duration,

                zone2_occupancy_duration =
                    excluded.zone2_occupancy_duration,

                zone1_light_hours =
                    excluded.zone1_light_hours,

                zone1_fan_hours =
                    excluded.zone1_fan_hours,

                zone2_light_hours =
                    excluded.zone2_light_hours,

                zone2_fan_hours =
                    excluded.zone2_fan_hours,

                zone1_energy_kwh =
                    excluded.zone1_energy_kwh,

                zone2_energy_kwh =
                    excluded.zone2_energy_kwh,

                daily_energy_kwh =
                    excluded.daily_energy_kwh,

                working_day =
                    excluded.working_day,

                holiday =
                    excluded.holiday,

                exam_day =
                    excluded.exam_day,

                special_class =
                    excluded.special_class,

                event_day =
                    excluded.event_day,

                vacation_day =
                    excluded.vacation_day,

                temperature =
                    excluded.temperature,

                humidity =
                    excluded.humidity,

                average_class_duration =
                    excluded.average_class_duration
            """,
            (
                date,
                day_type,

                int(max_zone1_people),
                int(max_zone2_people),
                int(max_total_people_count),

                int(zone1_occupancy_status),
                int(zone2_occupancy_status),

                float(zone1_occupancy_duration),
                float(zone2_occupancy_duration),

                float(zone1_light_hours),
                float(zone1_fan_hours),

                float(zone2_light_hours),
                float(zone2_fan_hours),

                float(zone1_energy_kwh),
                float(zone2_energy_kwh),
                float(daily_energy_kwh),

                int(working_day),
                int(holiday),
                int(exam_day),
                int(special_class),
                int(event_day),
                int(vacation_day),

                float(temperature),
                float(humidity),

                float(average_class_duration)
            )
        )

        connection.commit()
        connection.close()

    # ============================================
    # GET DAILY FEATURES
    # ============================================

    def get_daily_features(
        self,
        limit=100
    ):

        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT

                id,
                date,
                day_type,

                max_zone1_people,
                max_zone2_people,
                max_total_people_count,

                zone1_occupancy_status,
                zone2_occupancy_status,

                zone1_occupancy_duration,
                zone2_occupancy_duration,

                zone1_light_hours,
                zone1_fan_hours,

                zone2_light_hours,
                zone2_fan_hours,

                zone1_energy_kwh,
                zone2_energy_kwh,
                daily_energy_kwh,

                working_day,
                holiday,
                exam_day,
                special_class,
                event_day,
                vacation_day,

                temperature,
                humidity,

                average_class_duration

            FROM daily_features

            ORDER BY date DESC

            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        connection.close()

        return rows