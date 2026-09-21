from pathlib import Path
import csv


############################ SETTINGS ############################

composite_folder = Path("composites")

csv_path = Path(
    input("CSV file containing drawer information: ")
    .strip()
    .strip('"')
)


############################ CHECK FILES ############################

if not csv_path.exists():
    raise FileNotFoundError(
        f"CSV file does not exist: {csv_path}"
    )

if not composite_folder.exists():
    raise FileNotFoundError(
        f"Composite folder does not exist: {composite_folder}"
    )


############################ FIND COMPOSITES ############################

composite_paths = sorted([
    path for path in composite_folder.iterdir()
    if (
        path.suffix.lower() in [".jpg", ".jpeg"]
        and path.stem.startswith("drawer_")
        and path.stem.endswith("_composite")
    )
])

print(
    f"\nFound {len(composite_paths)} composite images."
)


############################ READ CSV ############################

with open(
    csv_path,
    newline="",
    encoding="utf-8-sig"
) as csvfile:

    reader = csv.DictReader(csvfile)

    required_columns = {
        "family",
        "drawer_number"
    }

    if not required_columns.issubset(
        reader.fieldnames or []
    ):
        raise ValueError(
            "CSV must contain columns named "
            "'family' and 'drawer_number'."
        )

    rows = list(reader)


print(
    f"Found {len(rows)} rows in CSV."
)


############################ CHECK COUNTS ############################

if len(composite_paths) != len(rows):

    raise ValueError(
        "\nNumber of composites does not match "
        "number of CSV rows.\n"
        f"Composites: {len(composite_paths)}\n"
        f"CSV rows:   {len(rows)}\n\n"
        "Nothing has been renamed."
    )


############################ BUILD RENAME PLAN ############################

rename_plan = []

for composite_path, row in zip(
    composite_paths,
    rows
):

    family = row["family"].strip()
    drawer_number = row["drawer_number"].strip()

    if not family or not drawer_number:
        raise ValueError(
            "CSV contains a blank family or "
            "drawer_number."
        )

    new_name = (
        f"{family}_{drawer_number}.JPG"
    )

    new_path = (
        composite_folder /
        new_name
    )

    rename_plan.append(
        (
            composite_path,
            new_path
        )
    )


############################ CHECK DUPLICATES ############################

new_names = [
    new_path.name.lower()
    for _, new_path in rename_plan
]

if len(new_names) != len(set(new_names)):

    raise ValueError(
        "CSV would create duplicate filenames. "
        "Nothing has been renamed."
    )


############################ PREVIEW ############################

print("\nProposed renaming:\n")

for old_path, new_path in rename_plan:

    print(
        f"{old_path.name} "
        f"-> "
        f"{new_path.name}"
    )


############################ CONFIRM ############################

confirmation = input(
    "\nRename these files? (y/n): "
).strip().lower()

if confirmation not in ["y", "yes"]:

    print(
        "\nCancelled. Nothing was renamed."
    )

    raise SystemExit


############################ RENAME ############################

for old_path, new_path in rename_plan:

    if new_path.exists():

        print(
            f"WARNING: {new_path.name} "
            f"already exists. Skipping."
        )

        continue

    old_path.rename(
        new_path
    )

    print(
        f"Renamed: "
        f"{old_path.name} "
        f"-> "
        f"{new_path.name}"
    )


############################ FINISHED ############################

print("\nDone.")

########################################################