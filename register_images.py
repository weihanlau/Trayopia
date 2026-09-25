import cv2
import numpy as np
import json
from pathlib import Path


############################ SETTINGS ############################

drawers_folder = Path("drawers")
registered_root = Path("registered")
homography_root = Path("homographies")

reference_name = "image_01.JPG"

registered_root.mkdir(exist_ok=True)
homography_root.mkdir(exist_ok=True)

MARKER_ERROR_THRESHOLD = 10.0
MIN_GOOD_MARKERS = 4


############################ ARUCO ############################

dictionary = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_ARUCO_ORIGINAL
)

parameters = cv2.aruco.DetectorParameters()

parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

detector = cv2.aruco.ArucoDetector(dictionary, parameters)


############################ FUNCTION: detect_markers and marker_size ############################

def detect_markers(image):

    corners, ids, rejected = detector.detectMarkers(image)

    if ids is None:
        return {}

    marker_dict = {}

    for marker_corners, marker_id in zip(
        corners,
        ids.flatten()
    ):
        marker_dict[int(marker_id)] = marker_corners[0]

    return marker_dict

def marker_size(corners):
    """Average side length of an ArUco marker in pixels."""

    side_lengths = [
        np.linalg.norm(corners[0] - corners[1]),
        np.linalg.norm(corners[1] - corners[2]),
        np.linalg.norm(corners[2] - corners[3]),
        np.linalg.norm(corners[3] - corners[0])
    ]

    return np.mean(side_lengths)

############################ PROCESS DRAWERS ############################

drawer_folders = sorted([
    path for path in drawers_folder.iterdir()
    if path.is_dir()
])

print(f"Found {len(drawer_folders)} drawers.")

for image_folder in drawer_folders:

    drawer_name = image_folder.name

    print("\n" + "=" * 50)
    print(f"Processing {drawer_name}")
    print("=" * 50)

    output_folder = registered_root / drawer_name
    homography_folder = homography_root / drawer_name

    output_folder.mkdir(exist_ok=True)
    homography_folder.mkdir(exist_ok=True)

    ###### REFERENCE IMAGE ######

    reference_path = image_folder / reference_name
    reference = cv2.imread(str(reference_path))

    if reference is None:
        print(
            f"ERROR: Could not open {reference_path}"
        )
        continue

    reference_markers = detect_markers(reference)

    print(f"Reference image: {reference_name}")
    print(
        f"Markers: {sorted(reference_markers.keys())}"
    )

    height, width = reference.shape[:2]

    #homography for reference
    np.save(
        homography_folder / "image_01_H.npy",
        np.eye(3)
    )

    cv2.imwrite(
        str(
            output_folder /
            "image_01_registered.JPG"
        ),
        reference
    )

    ###### FIND IMAGES ######

    image_paths = sorted([
        path for path in image_folder.iterdir()
        if path.suffix.lower() in [".jpg", ".jpeg"]
    ])

    image_scales = {
        "image_01": 1.0
    }

    ###### REGISTER EACH IMAGE ######

    for image_path in image_paths:

        if image_path.name.lower() == reference_name.lower():
            continue

        image = cv2.imread(str(image_path))

        if image is None:
            print(
                f"Could not open {image_path.name}"
            )
            continue

        markers = detect_markers(image)

        shared_ids = sorted(
            set(markers.keys()) &
            set(reference_markers.keys())
        )

        print(f"\n{image_path.name}")
        print(f"  Shared markers: {shared_ids}")

        if len(shared_ids) < 1:
            print("  ERROR: No shared markers")
            continue

        ###### ESTIMATE IMAGE SCALE FROM ARUCO MARKERS ######

        scale_ratios = []

        for marker_id in shared_ids:

            reference_size = marker_size(
                reference_markers[marker_id]
            )

            image_size = marker_size(
                markers[marker_id]
            )

            if reference_size > 0:
                scale_ratios.append(
                    image_size / reference_size
                )

        image_scale = float(np.median(scale_ratios))

        image_scales[image_path.stem] = image_scale

        print(
            f"  ArUco scale relative to reference: "
            f"{image_scale:.3f}x"
        )

        source_points = []
        destination_points = []

        for marker_id in shared_ids:

            source_points.extend(
                markers[marker_id]
            )

            destination_points.extend(
                reference_markers[marker_id]
            )

        source_points = np.array(
            source_points,
            dtype=np.float32
        )

        destination_points = np.array(
            destination_points,
            dtype=np.float32
        )

        print(
            f"  Using {len(source_points)} "
            f"corresponding points"
        )

        ###### CALCULATE HOMOGRAPHY ######

        H, mask = cv2.findHomography(
            source_points,
            destination_points,
            cv2.RANSAC,
            3.0
        )

        if H is None:
            print(
                "  ERROR: Homography could not "
                "be calculated"
            )
            continue

        ###### MEASURE REGISTRATION ERROR ######

        projected_points = cv2.perspectiveTransform(
            source_points.reshape(-1, 1, 2),
            H
        ).reshape(-1, 2)

        errors = np.linalg.norm(
            projected_points - destination_points,
            axis=1
        )
        
        mean_error = np.mean(errors)
        max_error = np.max(errors)

        bad_markers = []

        for i, marker_id in enumerate(shared_ids):

            start = i * 4
            end = start + 4

            marker_error = np.mean(
                errors[start:end]
            )

            if marker_error > MARKER_ERROR_THRESHOLD:
                bad_markers.append(marker_id)

        good_markers = [
            marker_id
            for marker_id in shared_ids
            if marker_id not in bad_markers
        ]

        ###### RECALCULATE WITHOUT BAD MARKERS ######

        if bad_markers and len(good_markers) >= MIN_GOOD_MARKERS:

            print(
                f"  Removing bad markers: {bad_markers}"
            )

            source_points = []
            destination_points = []

            for marker_id in good_markers:

                source_points.extend(
                    markers[marker_id]
                )

                destination_points.extend(
                    reference_markers[marker_id]
                )

            source_points = np.array(
                source_points,
                dtype=np.float32
            )

            destination_points = np.array(
                destination_points,
                dtype=np.float32
            )

            H, mask = cv2.findHomography(
                source_points,
                destination_points,
                cv2.RANSAC,
                3.0
            )

            print(
                f"  Recalculated using: {good_markers}"
            )

        elif bad_markers:

            print(
                f"  WARNING: Bad markers {bad_markers}, "
                f"but only {len(good_markers)} good markers remain. "
                f"Keeping original homography."
            )

        np.save(
            homography_folder /
            f"{image_path.stem}_H.npy",
            H
        )

        ###### ERROR FOR EACH MARKER ######

        for i, marker_id in enumerate(shared_ids):

            start = i * 4
            end = start + 4

            marker_errors = errors[start:end]

            print(
                f"  Marker {marker_id}: "
                f"mean={np.mean(marker_errors):.2f}px, "
                f"max={np.max(marker_errors):.2f}px"
            )

        ###### WARP IMAGE ######

        registered = cv2.warpPerspective(
            image,
            H,
            (width, height)
        )

        output_name = (
            image_path.stem +
            "_registered.JPG"
        )

        cv2.imwrite(
            str(output_folder / output_name),
            registered
        )

        ###### OVERLAY ######

        overlay = cv2.addWeighted(
            reference,
            0.5,
            registered,
            0.5,
            0
        )

        overlay_name = (
            image_path.stem +
            "_overlay.JPG"
        )

        cv2.imwrite(
            str(output_folder / overlay_name),
            overlay
        )

        inliers = (
            int(mask.sum())
            if mask is not None
            else 0
        )

        print("  Homography calculated")
        print(
            f"  RANSAC inliers: "
            f"{inliers}/{len(source_points)}"
        )
        print(f"  Saved: {output_name}")
        
        print(
            f"  Mean marker error: "
            f"{mean_error:.2f}px"
        )
        print(
            f"  Max marker error: "
            f"{max_error:.2f}px"
        )
    
    scale_path = homography_folder / "image_scales.json"

    with open(scale_path, "w") as f:
        json.dump(
            image_scales,
            f,
            indent=4
        )

    print(f"\nSaved image scales: {scale_path}")


print("\nDone.")

########################################################