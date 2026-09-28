import cv2
import json
import numpy as np


class ZoneManager:

    def __init__(self, config_path="config/zones.json"):
        self.config_path = config_path
        self.zones = []
        self.load_zones()

    def load_zones(self):

        with open(self.config_path, "r") as file:
            data = json.load(file)

        self.zones = data["zones"]

    def get_zone(self, x, y):

        point = (float(x), float(y))

        for zone in self.zones:

            polygon = np.array(
                zone["points"],
                dtype=np.int32
            )

            inside = cv2.pointPolygonTest(
                polygon,
                point,
                False
            )

            if inside >= 0:
                return zone["name"]

        return "Outside"

    def draw_zones(self, frame):

        for zone in self.zones:

            polygon = np.array(
                zone["points"],
                dtype=np.int32
            )

            cv2.polylines(
                frame,
                [polygon],
                True,
                (255, 0, 0),
                2
            )

            center_x = int(np.mean(polygon[:, 0]))
            center_y = int(np.mean(polygon[:, 1]))

            cv2.putText(
                frame,
                zone["name"],
                (center_x, center_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        return frame