import json
import cv2
from pathlib import Path
from trayopia_logger import print


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
    
    with open(
        detection_dir / "trays_all_views.json",
        "r"
    ) as f:
        trays_all_views = json.load(f)

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

        view_trays = trays_all_views.get(
            registered_name,
            []
        )

        matching_tray = None
        smallest_distance = float("inf")

        for candidate in view_trays:

            dx = candidate["x"] - x
            dy = candidate["y"] - y

            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < smallest_distance:
                smallest_distance = distance
                matching_tray = candidate

        if matching_tray is not None:
            max_match_distance = max(w, h) * 0.5

            if smallest_distance > max_match_distance:
                matching_tray = None

        if matching_tray is not None:

            mx = matching_tray["x"]
            my = matching_tray["y"]
            mw = matching_tray["width"]
            mh = matching_tray["height"]

            # Small local alignment correction
            shift_x = x - mx
            shift_y = y - my

            max_shift = min(w, h) * 0.10

            if abs(shift_x) > max_shift or abs(shift_y) > max_shift:
                shift_x = 0
                shift_y = 0

            mx1 = max(0, int(mx - mw / 2))
            my1 = max(0, int(my - mh / 2))
            mx2 = min(width, int(mx + mw / 2))
            my2 = min(height, int(my + mh / 2))
        
            tolerance_x = w * 0.05
            tolerance_y = h * 0.05

            needs_resize = (
                mx1 < x1 - tolerance_x or
                my1 < y1 - tolerance_y or
                mx2 > x2 + tolerance_x or
                my2 > y2 + tolerance_y
            )

            shifted_x1 = int(x1 - shift_x)
            shifted_y1 = int(y1 - shift_y)
            shifted_x2 = int(x2 - shift_x)
            shifted_y2 = int(y2 - shift_y)

            if (
                shifted_x1 < 0 or
                shifted_y1 < 0 or
                shifted_x2 > width or
                shifted_y2 > height
            ):
                shifted_x1 = x1
                shifted_y1 = y1
                shifted_x2 = x2
                shifted_y2 = y2

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

        if matching_tray is not None and needs_resize:

            # Crop the full detected tray from the selected image
            tray_crop = registered[my1:my2, mx1:mx2]

            # Resize it to fit the reference tray space
            target_width = x2 - x1
            target_height = y2 - y1

            tray_crop = cv2.resize(
                tray_crop,
                (target_width, target_height),
                interpolation=cv2.INTER_AREA
            )

            composite[y1:y2, x1:x2] = tray_crop

        else:

            # Normal crop with local position correction
            if matching_tray is not None:
                composite[y1:y2, x1:x2] = (
                    registered[
                        shifted_y1:shifted_y2,
                        shifted_x1:shifted_x2
                    ]
                )
            else:
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