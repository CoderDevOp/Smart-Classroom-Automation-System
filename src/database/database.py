import sqlite3
from pathlib import Path
from datetime import datetime


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


    def connect(self):

        return sqlite3.connect(
            self.database_path
        )


    def create_tables(self):

        connection = self.connect()

        cursor = connection.cursor()


        # ----------------------------------------
        # ZONE OCCUPANCY TABLE
        # ----------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zone_occupancy (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                timestamp TEXT NOT NULL,

                zone_name TEXT NOT NULL,

                people_count INTEGER NOT NULL,

                occupancy_status INTEGER NOT NULL

            )
        """)


        # ----------------------------------------
        # APPLIANCE EVENTS TABLE
        # ----------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appliance_events (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                timestamp TEXT NOT NULL,

                zone_name TEXT NOT NULL,

                appliance TEXT NOT NULL,

                previous_state INTEGER NOT NULL,

                current_state INTEGER NOT NULL

            )
        """)


        # ----------------------------------------
        # ENERGY SESSION TABLE
        # ----------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS energy_logs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                timestamp TEXT NOT NULL,

                zone_name TEXT NOT NULL,

                appliance TEXT NOT NULL,

                people_count INTEGER NOT NULL,

                duration_seconds REAL NOT NULL,

                power_watts REAL NOT NULL,

                energy_wh REAL NOT NULL

            )
        """)


        connection.commit()
        connection.close()


    # ============================================
    # OCCUPANCY
    # ============================================

    def log_occupancy(
        self,
        zone_name,
        people_count
    ):

        connection = self.connect()

        cursor = connection.cursor()

        timestamp = datetime.now().isoformat()

        occupancy_status = (
            1
            if people_count > 0
            else 0
        )

        cursor.execute(
            """
            INSERT INTO zone_occupancy
            (
                timestamp,
                zone_name,
                people_count,
                occupancy_status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                timestamp,
                zone_name,
                people_count,
                occupancy_status
            )
        )

        connection.commit()
        connection.close()


    # ============================================
    # APPLIANCE EVENTS
    # ============================================

    def log_appliance_event(
        self,
        zone_name,
        appliance,
        previous_state,
        current_state
    ):

        connection = self.connect()

        cursor = connection.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO appliance_events
            (
                timestamp,
                zone_name,
                appliance,
                previous_state,
                current_state
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                zone_name,
                appliance,
                int(previous_state),
                int(current_state)
            )
        )

        connection.commit()
        connection.close()


    # ============================================
    # ENERGY SESSION
    # ============================================

    def log_energy(
        self,
        zone_name,
        appliance,
        people_count,
        duration_seconds,
        power_watts
    ):

        connection = self.connect()

        cursor = connection.cursor()

        timestamp = datetime.now().isoformat()

        duration_seconds = float(
            duration_seconds
        )

        power_watts = float(
            power_watts
        )

        # Energy calculation:
        #
        # Energy (Wh)
        # = Power (W) × Time (seconds) / 3600

        energy_wh = (
            power_watts
            * duration_seconds
            / 3600
        )

        cursor.execute(
            """
            INSERT INTO energy_logs
            (
                timestamp,
                zone_name,
                appliance,
                people_count,
                duration_seconds,
                power_watts,
                energy_wh
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                zone_name,
                appliance,
                int(people_count),
                duration_seconds,
                power_watts,
                energy_wh
            )
        )

        connection.commit()
        connection.close()


    # ============================================
    # READ OCCUPANCY
    # ============================================

    def get_recent_occupancy(
        self,
        limit=20
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                timestamp,
                zone_name,
                people_count,
                occupancy_status

            FROM zone_occupancy

            ORDER BY id DESC

            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        connection.close()

        return rows


    # ============================================
    # READ APPLIANCE EVENTS
    # ============================================

    def get_appliance_events(
        self,
        limit=20
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                timestamp,
                zone_name,
                appliance,
                previous_state,
                current_state

            FROM appliance_events

            ORDER BY id DESC

            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        connection.close()

        return rows


    # ============================================
    # READ ENERGY LOGS
    # ============================================

    def get_energy_logs(
        self,
        limit=20
    ):

        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                timestamp,
                zone_name,
                appliance,
                people_count,
                duration_seconds,
                power_watts,
                energy_wh

            FROM energy_logs

            ORDER BY id DESC

            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        connection.close()

        return rows