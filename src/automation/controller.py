import time


class AutomationController:

    def __init__(
        self,
        zones,
        light_on_delay=2,
        fan_on_delay=4,
        light_off_delay=3,
        fan_off_delay=3
    ):
        self.zones = zones

        self.light_on_delay = light_on_delay
        self.fan_on_delay = fan_on_delay
        self.light_off_delay = light_off_delay
        self.fan_off_delay = fan_off_delay

        self.light_state = {
            zone["name"]: False
            for zone in zones
        }

        self.fan_state = {
            zone["name"]: False
            for zone in zones
        }

        self.previous_light_state = {
            zone["name"]: False
            for zone in zones
        }

        self.previous_fan_state = {
            zone["name"]: False
            for zone in zones
        }

        self.occupied_since = {
            zone["name"]: None
            for zone in zones
        }

        self.empty_since = {
            zone["name"]: None
            for zone in zones
        }

    def update(self, zone_counts):

        current_time = time.time()

        decisions = {}

        for zone in self.zones:

            zone_name = zone["name"]

            people = zone_counts.get(
                zone_name,
                0
            )

            # --------------------------------
            # PEOPLE PRESENT
            # --------------------------------

            if people > 0:

                self.empty_since[zone_name] = None

                if self.occupied_since[zone_name] is None:

                    self.occupied_since[zone_name] = (
                        current_time
                    )

                occupied_time = (
                    current_time
                    - self.occupied_since[zone_name]
                )

                # Light ON after delay

                if occupied_time >= self.light_on_delay:

                    self.light_state[zone_name] = True

                # Fan ON after delay

                if occupied_time >= self.fan_on_delay:

                    self.fan_state[zone_name] = True

            # --------------------------------
            # NO PEOPLE
            # --------------------------------

            else:

                self.occupied_since[zone_name] = None

                if self.empty_since[zone_name] is None:

                    self.empty_since[zone_name] = (
                        current_time
                    )

                empty_time = (
                    current_time
                    - self.empty_since[zone_name]
                )

                # Light OFF after delay

                if empty_time >= self.light_off_delay:

                    self.light_state[zone_name] = False

                # Fan OFF after delay

                if empty_time >= self.fan_off_delay:

                    self.fan_state[zone_name] = False

            # --------------------------------
            # CHECK STATE CHANGE
            # --------------------------------

            light_changed = (
                self.light_state[zone_name]
                != self.previous_light_state[zone_name]
            )

            fan_changed = (
                self.fan_state[zone_name]
                != self.previous_fan_state[zone_name]
            )

            # --------------------------------
            # SAVE CURRENT STATE
            # --------------------------------

            self.previous_light_state[zone_name] = (
                self.light_state[zone_name]
            )

            self.previous_fan_state[zone_name] = (
                self.fan_state[zone_name]
            )

            # --------------------------------
            # DECISION
            # --------------------------------

            decisions[zone_name] = {

                "people": people,

                "light": self.light_state[
                    zone_name
                ],

                "fan": self.fan_state[
                    zone_name
                ],

                "light_changed": light_changed,

                "fan_changed": fan_changed,

                "state_changed": (
                    light_changed
                    or fan_changed
                )
            }

        return decisions