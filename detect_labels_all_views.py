import json
from pathlib import Path
from inference_sdk import InferenceHTTPClient, InferenceConfiguration


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

registered_root = Path("registered")
detections_root = Path("detections")


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
# FIND DRAWERS
# --------------------------------------------------

drawer_folders = sorted([
    path for path in registered_root.iterdir()
    if path.is_dir()
])

print(f"Found {len(drawer_folders)} drawers.")


# --------------------------------------------------
# PROCESS EACH DRAWER
# --------------------------------------------------

for registered_dir in drawer_folders:

    drawer_name = registered_dir.name

    print("\n" + "=" * 50)
    print(f"Processing {drawer_name}")
    print("=" * 50)

    image_paths = sorted(
        registered_dir.glob("image_*_registered.JPG")
    )

    all_labels = {}

    for path in image_paths:

        print(f"Processing {path.name}...")

        result = client.infer(
            str(path),
            model_id="entomology-unit-trays/3"
        )

        predictions = result["predictions"]

        label_predictions = [
            p for p in predictions
            if p["class"] == "Unit-Tray-Label"
            and p["confidence"] >= 0.7
        ]

        all_labels[path.name] = label_predictions

        print(
            f"  Detected labels: "
            f"{len(label_predictions)}"
        )

    output_folder = detections_root / drawer_name
    output_folder.mkdir(exist_ok=True)

    output_json = (
        output_folder /
        "labels_all_views.json"
    )

    with open(output_json, "w") as f:
        json.dump(
            all_labels,
            f,
            indent=4
        )

    print(
        f"Saved labels_all_views.json "
        f"for {drawer_name}"
    )


print("\nAll drawers finished.")