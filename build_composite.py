import json
import cv2
from pathlib import Path


############################ SETTINGS ############################

drawers_root = Path("drawers")
registered_root = Path("registered")
detections_root = Path("detections")
composites_root = Path("composites")

composites_root.mkdir(exist_ok=True)


############################ PROCESS DRAWERS ############################

drawer_folders = sorted([
    path for path in registered_root.iterdir()
    if path.is_dir()
])

print(f"Found {len(drawer_folders)} drawers.")


for registered_dir in drawer_folders:

    drawer_name = registered_dir.name

    print("\n" + "=" * 50)
    print(f"Processing {drawer_name}")
    print("=" * 50)

    detection_dir = detections_root / drawer_name
    original_dir = drawers_root / drawer_name

    with open(
        detection_dir / "tray_coordinates.json",
        "r"
    ) as f:
        trays = json.load(f)

    with open(
        detection_dir / "best_views.json",
        "r"
    ) as f:
        best_views = json.load(f)

    # Image 1 remains the background/reference
    reference_path = original_dir / "image_01.JPG"
    reference = cv2.imread(str(reference_path))

    if reference is None:
        raise FileNotFoundError(
            f"Could not load {reference_path}"
        )

    composite = reference.copy()

    height, width = reference.shape[:2]


    ############################ EACH TRAY ############################

    for tray, choice in zip(trays, best_views):

        tray_number = choice["tray"]

        x = tray["x"]
        y = tray["y"]
        w = tray["width"]
        h = tray["height"]

        x1 = max(0, int(x - w / 2))
        y1 = max(0, int(y - h / 2))
        x2 = min(width, int(x + w / 2))
        y2 = min(height, int(y + h / 2))

        registered_name = choice["best_image"]

        registered_path = (
            registered_dir /
            registered_name
        )

        registered = cv2.imread(
            str(registered_path)
        )

        if registered is None:
            print(
                f"Tray {tray_number}: "
                f"could not load {registered_path}"
            )
            continue

        # Copy the tray directly from the
        # already-registered image
        composite[y1:y2, x1:x2] = (
            registered[y1:y2, x1:x2]
        )

        print(
            f"Tray {tray_number}: "
            f"{registered_name}"
        )


    ############################ SAVE ############################

    output_path = (
        composites_root /
        f"{drawer_name}_composite.JPG"
    )

    cv2.imwrite(
        str(output_path),
        composite
    )

    print(f"Saved {output_path}")


print("\nAll drawers finished.")