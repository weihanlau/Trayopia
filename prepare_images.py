from pathlib import Path
import shutil

############################ SETTINGS ############################


IMAGES_PER_DRAWER = 7

input_folder = Path(
    input("Folder containing raw images: ").strip().strip('"')
)

output_folder = Path("drawers")


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


############################# CHECK IMAGE COUNT ############################

if len(image_paths) == 0:
    raise ValueError("No JPG/JPEG images found.")

if len(image_paths) % IMAGES_PER_DRAWER != 0:
    raise ValueError(
        f"Found {len(image_paths)} images. "
        f"This is not divisible by {IMAGES_PER_DRAWER}."
    )

number_of_drawers = len(image_paths) // IMAGES_PER_DRAWER

print(f"This corresponds to {number_of_drawers} drawers.")


############################# CREATE DRAWER FOLDERS ############################

output_folder.mkdir(exist_ok=True)

for drawer_index in range(number_of_drawers):

    drawer_number = drawer_index + 1

    drawer_folder = (
        output_folder /
        f"drawer_{drawer_number:03d}"
    )

    drawer_folder.mkdir(exist_ok=True)

    start = drawer_index * IMAGES_PER_DRAWER
    end = start + IMAGES_PER_DRAWER

    drawer_images = image_paths[start:end]

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
        f"Prepared drawer_{drawer_number:03d}"
    )


print("\nDone.")

########################################################