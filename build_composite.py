import json
import cv2
from pathlib import Path


# --------------------------------------------------
# ROOT FOLDERS
# --------------------------------------------------

registered_root = Path("registered")
detections_root = Path("detections")
composites_root = Path("composites")

composites_root.mkdir(exist_ok=True)


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

    detection_dir = detections_root / drawer_name

    # ----------------------------------------------
    # LOAD TRAYS + BEST VIEWS
    # ----------------------------------------------

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

    print(f"Loaded {len(trays)} trays")
    print(f"Loaded {len(best_views)} best-view choices")


    # ----------------------------------------------
    # REFERENCE IMAGE
    # ----------------------------------------------

    reference_path = (
        registered_dir /
        "image_01_registered.JPG"
    )

    reference_image = cv2.imread(
        str(reference_path)
    )

    if reference_image is None:
        raise FileNotFoundError(
            f"Could not load {reference_path}"
        )

    composite = reference_image.copy()


    # ----------------------------------------------
    # REPLACE EACH TRAY
    # ----------------------------------------------

    for tray, choice in zip(
        trays,
        best_views
    ):

        x = tray["x"]
        y = tray["y"]
        w = tray["width"]
        h = tray["height"]

        x1 = int(x - w / 2)
        y1 = int(y - h / 2)
        x2 = int(x + w / 2)
        y2 = int(y + h / 2)

        best_image_path = (
            registered_dir /
            choice["best_image"]
        )

        best_image = cv2.imread(
            str(best_image_path)
        )

        if best_image is None:
            raise FileNotFoundError(
                f"Could not load {best_image_path}"
            )

        composite[y1:y2, x1:x2] = (
            best_image[y1:y2, x1:x2]
        )


    # ----------------------------------------------
    # SAVE COMPOSITE
    # ----------------------------------------------

    output_path = (
        composites_root /
        f"{drawer_name}_composite.JPG"
    )

    cv2.imwrite(
        str(output_path),
        composite
    )

    print(
        f"Saved {output_path}"
    )


print("\nAll drawers finished.")