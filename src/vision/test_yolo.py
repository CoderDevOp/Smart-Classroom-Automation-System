import cv2

from detector import PersonDetector


detector = PersonDetector()

camera = cv2.VideoCapture(0)

while True:
    success, frame = camera.read()

    if not success:
        break

    persons = detector.detect(frame)

    for person in persons:
        x1, y1, x2, y2 = person["box"]
        confidence = person["confidence"]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Person {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"People: {len(persons)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    cv2.imshow("Smart Classroom Detection", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q") or key == ord("Q"):
        print("Stopping system...")
        break

camera.release()
cv2.destroyAllWindows()