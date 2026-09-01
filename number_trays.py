import json
import cv2

with open("tray_coordinates.json", "r") as f:
    trays = json.load(f)

image = cv2.imread("registered/image_01_registered.JPG")

for i, tray in enumerate(trays, start=1):
    x = int(tray["x"])
    y = int(tray["y"])

    cv2.putText(
        image,
        str(i),
        (x - 20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 255),
        3
    )

cv2.imwrite("numbered_trays.JPG", image)

print("Saved numbered_trays.JPG")