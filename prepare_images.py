from pathlib import Path
import shutil
import cv2


############################ SETTINGS ############################

input_folder = Path(
    input("Folder containing raw images: ").strip().strip('"')
)

output_folder = Path("drawers")


############################ ARUCO SETTINGS ############################

aruco_dictionary = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_ARUCO_ORIGINAL
)

aruco_parameters = cv2.aruco.DetectorParameters()

aruco_detector = cv2.aruco.ArucoDetector(
    aruco_dictionary,
    aruco_parameters
)


############################ FIND IMAGES ############################

if not input_folder.exists():
    raise FileNotFoundError(
        f"Folder does not exist: {input_folder}"
    )

image_paths = sorted([
    path for path in input_folder.iterdir()
    if path.suffix.lower() in [".jpg", ".jpeg"]
])

print(f"\nFound {len(image_paths)} images.")

if len(image_paths) == 0:
    raise ValueError("No JPG/JPEG images found.")


############################ DETECT DRAWERS ############################

drawer_groups = []
current_drawer = []

print("\nLooking for reference images...")

for image_path in image_paths:

    image = cv2.imread(str(image_path))

    if image is None:
        print(
            f"WARNING: Could not read {image_path.name}"
        )
        continue

    corners, ids, rejected = (
        aruco_detector.detectMarkers(image)
    )

    if ids is None:
        marker_count = 0
    else:
        marker_count = len(ids)

    print(f"{image_path.name}: detected {marker_count} ArUco markers")

    # A reference image contains all 8 ArUco markers
    is_reference = marker_count >= 8

    if is_reference:

        # Save the previous drawer before
        # starting a new one
        if current_drawer:
            drawer_groups.append(
                current_drawer
            )

        # Start a new drawer
        current_drawer = [
            image_path
        ]

        print(
            f"Reference found: "
            f"{image_path.name} "
            f"({marker_count} markers detected)"
        )

    else:

        # Every image after a reference belongs
        # to that drawer until the next reference
        if not current_drawer:
            raise ValueError(
                f"{image_path.name} appears before "
                f"the first reference image. "
                f"The first image must contain "
                f"all 8 ArUco markers."
            )

        current_drawer.append(
            image_path
        )


# Save the final drawer
if current_drawer:
    drawer_groups.append(
        current_drawer
    )


############################ CHECK DRAWERS ############################

if len(drawer_groups) == 0:
    raise ValueError(
        "No reference images containing "
        "8 ArUco markers were found."
    )

print(
    f"\nDetected {len(drawer_groups)} drawers.\n"
)

for drawer_number, drawer_images in enumerate(
    drawer_groups,
    start=1
):

    image_count = len(drawer_images)

    if image_count in [7, 9]:
        status = "OK"
    else:
        status = "WARNING"

    print(
        f"{status}: "
        f"drawer_{drawer_number:03d}: "
        f"{image_count} images"
    )


############################ CREATE DRAWER FOLDERS ############################

output_folder.mkdir(
    exist_ok=True
)

for drawer_number, drawer_images in enumerate(
    drawer_groups,
    start=1
):

    drawer_folder = (
        output_folder /
        f"drawer_{drawer_number:03d}"
    )

    drawer_folder.mkdir(
        exist_ok=True
    )

    for image_index, source_path in enumerate(
        drawer_images,
        start=1
    ):

        destination = (
            drawer_folder /
            f"image_{image_index:02d}.JPG"
        )

        shutil.copy2(
            source_path,
            destination
        )

    print(
        f"Prepared "
        f"drawer_{drawer_number:03d} "
        f"({len(drawer_images)} images)"
    )


############################ FINISHED ############################

print("\nDone.")

########################################################