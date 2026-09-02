import cv2
import numpy as np
from pathlib import Path


############################ SETTINGS ############################

drawers_folder = Path("drawers")
registered_root = Path("registered")
homography_root = Path("homographies")

reference_name = "image_01.JPG"

registered_root.mkdir(exist_ok=True)
homography_root.mkdir(exist_ok=True)


############################ ARUCO ############################

dictionary = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_ARUCO_ORIGINAL
)

parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)


############################ FUNCTION: detect markers ############################

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
            5.0
        )

        if H is None:
            print(
                "  ERROR: Homography could not "
                "be calculated"
            )
            continue

        np.save(
            homography_folder /
            f"{image_path.stem}_H.npy",
            H
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


print("\nDone.")

########################################################