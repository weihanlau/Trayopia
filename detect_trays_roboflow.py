import cv2
import json
from pathlib import Path
from inference_sdk import InferenceHTTPClient, InferenceConfiguration


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

registered_root = Path("registered")

detections_root = Path("detections")
detections_root.mkdir(exist_ok=True)

import os
from dotenv import load_dotenv

load_dotenv()

roboflow_api_key = os.getenv("ROBOFLOW_API_KEY")

if not roboflow_api_key:
    raise ValueError("ROBOFLOW_API_KEY not found in .env")

# --------------------------------------------------
# ROBOFLOW ENDPOINT
# --------------------------------------------------

client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=roboflow_api_key
).configure(
    InferenceConfiguration(
        api_key_transport="header"
    )
)

# --------------------------------------------------
# FIND ALL DRAWERS
# --------------------------------------------------

drawer_folders = sorted([
    path for path in registered_root.iterdir()
    if path.is_dir()
])

print(f"Found {len(drawer_folders)} drawers.")


# --------------------------------------------------
# PROCESS EACH DRAWER
# --------------------------------------------------

for registered_folder in drawer_folders:

    drawer_name = registered_folder.name

    print("\n" + "=" * 50)
    print(f"Processing {drawer_name}")
    print("=" * 50)

    image_path = (
        registered_folder /
        "image_01_registered.JPG"
    )

    output_folder = detections_root / drawer_name
    output_folder.mkdir(exist_ok=True)

    output_image = (
        output_folder /
        "roboflow_tray_detection.JPG"
    )

    tray_json = (
        output_folder /
        "tray_coordinates.json"
    )

    label_json = (
        output_folder /
        "label_coordinates.json"
    )


    # --------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------

    image = cv2.imread(str(image_path))

    if image is None:
        print(f"ERROR: Could not open {image_path}")
        continue


    # --------------------------------------------------
    # ROBOFLOW INFERENCE
    # --------------------------------------------------

    result = client.infer(
        str(image_path),
        model_id="entomology-unit-trays/3"
    )


    # --------------------------------------------------
    # EXTRACT PREDICTIONS
    # --------------------------------------------------

    predictions = result["predictions"]

    tray_predictions = [
        p for p in predictions
        if p["class"] == "Unit-Tray"
        and p["confidence"] >= 0.8
    ]

    label_predictions = [
        p for p in predictions
        if p["class"] == "Unit-Tray-Label"
        and p["confidence"] >= 0.8
    ]

    print(
        f"Detected trays: {len(tray_predictions)}"
    )

    print(
        f"Detected labels: {len(label_predictions)}"
    )


    # --------------------------------------------------
    # DRAW TRAY BOXES
    # --------------------------------------------------

    output = image.copy()

    for p in tray_predictions:

        x = p["x"]
        y = p["y"]
        w = p["width"]
        h = p["height"]

        x1 = int(x - w / 2)
        y1 = int(y - h / 2)
        x2 = int(x + w / 2)
        y2 = int(y + h / 2)

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            4
        )

    cv2.imwrite(
        str(output_image),
        output
    )


    # --------------------------------------------------
    # SAVE JSON FILES
    # --------------------------------------------------

    with open(tray_json, "w") as f:
        json.dump(
            tray_predictions,
            f,
            indent=4
        )

    with open(label_json, "w") as f:
        json.dump(
            label_predictions,
            f,
            indent=4
        )

    print(f"Saved tray detections for {drawer_name}")


print("\nAll drawers finished.")