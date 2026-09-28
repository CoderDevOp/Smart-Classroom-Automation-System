import cv2
from pathlib import Path

from detector import PersonDetector
from zones import ZoneManager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ZONE_CONFIG = PROJECT_ROOT / "config" / "zones.json"

print("Starting Smart Classroom Zone Detection...")
print(f"Zone config: {ZONE_CONFIG}")

detector = PersonDetector()
zone_manager = ZoneManager(str(ZONE_CONFIG))

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("Camera opened successfully.")
print("Press Q to stop.")


while True:

    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read camera frame.")
        break

    persons = detector.detect(frame)

    frame = zone_manager.draw_zones(frame)

    zone_counts = {
        zone["name"]: 0
        for zone in zone_manager.zones
    }

    outside_count = 0

    for person in persons:

        x1, y1, x2, y2 = person["box"]
        confidence = person["confidence"]

        # Top-center point
        center_x = int((x1 + x2) / 2)
        top_y = y1

        zone = zone_manager.get_zone(
            center_x,
            top_y
        )

        if zone in zone_counts:
            zone_counts[zone] += 1
        else:
            outside_count += 1

        # Bounding box
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # Red top-center point
        cv2.circle(
            frame,
            (center_x, top_y),
            6,
            (0, 0, 255),
            -1
        )

        # Small zone label
        cv2.putText(
            frame,
            f"{zone} {confidence:.2f}",
            (x1, max(y1 - 8, 18)),
            cv2.FONT_HERSHEY_COMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )

    # Small dashboard text
    y_position = 30

    for zone_name, count in zone_counts.items():

        cv2.putText(
            frame,
            f"{zone_name}: {count}",
            (15, y_position),
            cv2.FONT_HERSHEY_COMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y_position += 25

    cv2.putText(
        frame,
        f"Outside: {outside_count}",
        (15, y_position),
        cv2.FONT_HERSHEY_COMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        f"Total: {len(persons)}",
        (15, y_position + 25),
        cv2.FONT_HERSHEY_COMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        "Q: Stop",
        (15, y_position + 50),
        cv2.FONT_HERSHEY_COMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    cv2.imshow(
        "Smart Classroom - Zone Occupancy",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()

print("Zone detection stopped.")