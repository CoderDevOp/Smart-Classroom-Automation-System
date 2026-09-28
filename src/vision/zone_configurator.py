import cv2
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "zones.json"

zones = []
current_points = []


def mouse_callback(event, x, y, flags, param):
    global current_points

    if event == cv2.EVENT_LBUTTONDOWN:
        current_points.append([x, y])
        print(f"Point added: ({x}, {y})")


camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    exit()

cv2.namedWindow("Zone Configuration")
cv2.setMouseCallback("Zone Configuration", mouse_callback)

print()
print("POLYGON ZONE CONFIGURATION")
print("--------------------------")
print("Left Click : Add polygon point")
print("N          : Finish current zone")
print("C          : Clear current zone")
print("R          : Clear all zones")
print("S          : Save zones")
print("Q          : Quit")
print()

while True:

    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read camera.")
        break

    display = frame.copy()

    # Draw saved zones
    for index, zone in enumerate(zones):

        points = zone["points"]

        cv2.polylines(
            display,
            [__import__("numpy").array(points, dtype="int32")],
            True,
            (255, 0, 0),
            2
        )

        center_x = int(sum(point[0] for point in points) / len(points))
        center_y = int(sum(point[1] for point in points) / len(points))

        cv2.putText(
            display,
            zone["name"],
            (center_x, center_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

    # Draw current polygon
    if len(current_points) > 0:

        for point in current_points:

            cv2.circle(
                display,
                tuple(point),
                5,
                (0, 0, 255),
                -1
            )

        if len(current_points) > 1:

            cv2.polylines(
                display,
                [
                    __import__("numpy").array(
                        current_points,
                        dtype="int32"
                    )
                ],
                False,
                (0, 255, 255),
                2
            )

    # Instructions
    cv2.putText(
        display,
        "Click: Point | N: Finish | C: Clear | R: Reset | S: Save | Q: Quit",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.imshow("Zone Configuration", display)

    key = cv2.waitKey(1) & 0xFF

    # Finish current polygon
    if key == ord("n"):

        if len(current_points) >= 3:

            zones.append({
                "name": f"Zone {len(zones) + 1}",
                "points": current_points.copy()
            })

            print(
                f"Zone {len(zones)} created with "
                f"{len(current_points)} points."
            )

            current_points.clear()

        else:
            print("A zone needs at least 3 points.")

    # Clear current polygon
    elif key == ord("c"):
        current_points.clear()
        print("Current polygon cleared.")

    # Clear all zones
    elif key == ord("r"):
        zones.clear()
        current_points.clear()
        print("All zones cleared.")

    # Save
    elif key == ord("s"):

        if len(current_points) >= 3:
            print("Finish the current zone with N before saving.")
            continue

        config = {
            "zones": zones
        }

        with open(CONFIG_PATH, "w") as file:
            json.dump(config, file, indent=4)

        print()
        print("Zones saved successfully.")
        print(f"Saved to: {CONFIG_PATH}")
        print()

    # Quit
    elif key == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()