import json
import cv2
import numpy as np
from pathlib import Path


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

LABEL_AREA_OVERRIDE = 0.20


# --------------------------------------------------
# ROOT FOLDERS
# --------------------------------------------------

registered_root = Path("registered")
homography_root = Path("homographies")
detections_root = Path("detections")


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
    homography_dir = homography_root / drawer_name

    with open(
        detection_dir / "tray_coordinates.json",
        "r"
    ) as f:
        trays = json.load(f)

    with open(
        detection_dir / "labels_all_views.json",
        "r"
    ) as f:
        labels_all_views = json.load(f)

    image_paths = sorted(
        registered_dir.glob("image_*_registered.JPG")
    )

    print(f"Loaded {len(trays)} trays")
    print(f"Found {len(image_paths)} registered images")


    # --------------------------------------------------
    # CAMERA CENTRE
    # --------------------------------------------------

    reference_image = cv2.imread(
        str(image_paths[0])
    )

    height, width = reference_image.shape[:2]

    camera_centre = np.array([
        width / 2,
        height / 2
    ])


    # --------------------------------------------------
    # CHOOSE BEST VIEW
    # --------------------------------------------------

    print("\nBest view for each tray:")

    best_views = []

    for tray_number, tray in enumerate(
        trays,
        start=1
    ):

        tx = tray["x"]
        ty = tray["y"]
        tw = tray["width"]
        th = tray["height"]

        tx1 = tx - tw / 2
        ty1 = ty - th / 2
        tx2 = tx + tw / 2
        ty2 = ty + th / 2

        tray_centre_registered = np.array(
            [[[tx, ty]]],
            dtype=np.float32
        )

        candidates = []

        # ----------------------------------------------
        # SCORE EACH IMAGE
        # ----------------------------------------------

        for path in image_paths:

            image_name = path.name

            base_name = image_name.replace(
                "_registered.JPG",
                ""
            )

            H = np.load(
                homography_dir /
                f"{base_name}_H.npy"
            )

            H_inverse = np.linalg.inv(H)

            tray_original = cv2.perspectiveTransform(
                tray_centre_registered,
                H_inverse
            )[0][0]

            distance = np.linalg.norm(
                tray_original - camera_centre
            )

            labels = labels_all_views.get(
                image_name,
                []
            )

            labels_in_tray = []

            for label in labels:

                lx = label["x"]
                ly = label["y"]

                if (
                    tx1 <= lx <= tx2
                    and ty1 <= ly <= ty2
                ):
                    labels_in_tray.append(label)

            if labels_in_tray:

                largest_label = max(
                    labels_in_tray,
                    key=lambda p:
                        p["width"] * p["height"]
                )

                label_area = (
                    largest_label["width"]
                    * largest_label["height"]
                )

            else:
                label_area = 0

            candidates.append({
                "image": image_name,
                "distance": float(distance),
                "label_area": float(label_area)
            })


        # --------------------------------------------------
        # FIRST CHOICE = CLOSEST TO CAMERA
        # --------------------------------------------------

        distance_winner = min(
            candidates,
            key=lambda c: c["distance"]
        )

        chosen = distance_winner


        # --------------------------------------------------
        # LABEL-AREA OVERRIDE
        # --------------------------------------------------

        largest_label_candidate = max(
            candidates,
            key=lambda c: c["label_area"]
        )

        current_area = (
            distance_winner["label_area"]
        )

        largest_area = (
            largest_label_candidate["label_area"]
        )

        if current_area > 0:

            required_area = (
                current_area
                * (1 + LABEL_AREA_OVERRIDE)
            )

            if largest_area >= required_area:
                chosen = largest_label_candidate

        elif largest_area > 0:
            chosen = largest_label_candidate


        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        best_views.append({
            "tray": tray_number,
            "best_image": chosen["image"],
            "distance": chosen["distance"],
            "label_area": chosen["label_area"]
        })

        reason = (
            "distance"
            if chosen["image"]
            == distance_winner["image"]
            else "label override"
        )

        print(
            f"Tray {tray_number}: "
            f"{chosen['image']} "
            f"[{reason}] "
            f"distance={chosen['distance']:.0f}px, "
            f"label={chosen['label_area']:.0f}px²"
        )


    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    output_path = (
        detection_dir /
        "best_views.json"
    )

    with open(output_path, "w") as f:
        json.dump(
            best_views,
            f,
            indent=4
        )

    print(
        f"\nSaved best_views.json "
        f"for {drawer_name}"
    )


print("\nAll drawers finished.")