from ultralytics import YOLO


class PersonDetector:

    def __init__(self, model_path="yolo11n.pt", confidence=0.5):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):

        results = self.model(
            frame,
            conf=self.confidence,
            classes=[0],
            verbose=False
        )

        persons = []

        for result in results:

            for box in result.boxes:

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                confidence = float(box.conf[0])

                persons.append({
                    "box": (x1, y1, x2, y2),
                    "confidence": confidence
                })

        return persons