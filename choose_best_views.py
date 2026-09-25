import os
import json
import cv2
import numpy as np
from pathlib import Path


############################ SETTINGS ############################

DISTANCE_MODE = os.getenv(
    "TRAYOPIA_DISTANCE_MODE",
    "normalized"
)

LABEL_AREA_OVERRIDE = 0.2
MAX_DISTANCE_OVERRIDE = 1.25


############################ ROOT FOLDERS ############################

registered_root = Path("registered")
homography_root = Path("homographies")
detections_root = Path("detections")


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
    
    if DISTANCE_MODE == "normalized":
        with open(
            homography_dir / "image_scales.json",
            "r"
        ) as f:
            image_scales = json.load(f)
    else:
        image_scales = {}

    image_paths = sorted(
        registered_dir.glob("image_*_registered.JPG")
    )

    # In normalized mode, image 1 is the overview/reference image.
    # Use only the zoomed-in images for best-view selection.
    if DISTANCE_MODE == "normalized":
        image_paths = [
            path for path in image_paths
            if path.name != "image_01_registered.JPG"
        ]

    print(f"Loaded {len(trays)} trays")
    print(f"Found {len(image_paths)} registered images")


    ###### CAMERA CENTRE ######

    reference_image = cv2.imread(
    str(registered_dir / "image_01_registered.JPG")
    )

    height, width = reference_image.shape[:2]

    camera_centre = np.array([
        width / 2,
        height / 2
    ])


    ###### CHOOSE BEST VIEW ######

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


        ###### SCORE EACH IMAGE ######

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

            if DISTANCE_MODE == "normalized":
                image_scale = image_scales[base_name]
                normalized_distance = distance / image_scale
            else:
                image_scale = 1.0
                normalized_distance = distance

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

                lx = largest_label["x"]
                ly = largest_label["y"]
                lw = largest_label["width"]
                lh = largest_label["height"]

                label_corners_registered = np.array([[
                    [lx - lw / 2, ly - lh / 2],
                    [lx + lw / 2, ly - lh / 2],
                    [lx + lw / 2, ly + lh / 2],
                    [lx - lw / 2, ly + lh / 2]
                ]], dtype=np.float32)

                # Transform label back into the ORIGINAL image
                label_corners_original = cv2.perspectiveTransform(
                    label_corners_registered,
                    H_inverse
                )[0]

                # Calculate its actual area in the original photograph
                label_area = cv2.contourArea(
                    label_corners_original
                )

            else:
                label_area = 0

            candidates.append({
                "image": image_name,
                "distance": float(distance),
                "normalized_distance": float(normalized_distance),
                "scale": float(image_scale),
                "label_area": float(label_area)
            })


        ###### DEBUG: SHOW ALL DISTANCES ######

        print(f"\nTray {tray_number} candidate distances:")

        for candidate in candidates:
            print(
                f"  {candidate['image']}: "
                f"raw={candidate['distance']:.0f}px, "
                f"scale={candidate['scale']:.3f}x, "
                f"normalized={candidate['normalized_distance']:.0f}px"
            )


        ###### FIRST PASS: CLOSEST TO CAMERA ######

        if DISTANCE_MODE == "normalized":
            distance_winner = min(
                candidates,
                key=lambda c: c["normalized_distance"]
            )
        else:
            distance_winner = min(
                candidates,
                key=lambda c: c["distance"]
            )

        chosen = distance_winner


        ###### SECOND PASS: LABEL AREA OVERRIDE ######

        # Only consider images reasonably close to the distance winner
        distance_key = (
            "normalized_distance"
            if DISTANCE_MODE == "normalized"
            else "distance"
        )

        eligible_candidates = [
            c for c in candidates
            if c[distance_key]
            <= distance_winner[distance_key] * MAX_DISTANCE_OVERRIDE
        ]

        largest_label_candidate = max(
            eligible_candidates,
            key=lambda c: c["label_area"]
        )

        current_area = distance_winner["label_area"]
        largest_area = largest_label_candidate["label_area"]

        if current_area > 0:

            required_area = (
                current_area
                * (1 + LABEL_AREA_OVERRIDE)
            )

            if largest_area >= required_area:
                chosen = largest_label_candidate

        elif largest_area > 0:
            chosen = largest_label_candidate


        ###### SAVE BEST VIEW ######

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

        if DISTANCE_MODE == "normalized":
            chosen_distance = chosen["normalized_distance"]
            distance_label = "normalized distance"
        else:
            chosen_distance = chosen["distance"]
            distance_label = "distance"

        print(
            f"Tray {tray_number}: "
            f"{chosen['image']} "
            f"[{reason}] "
            f"{distance_label}={chosen_distance:.0f}px, "
            f"label={chosen['label_area']:.0f}px²"
        )


    ###### SAVE RESULTS ######

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

########################################################