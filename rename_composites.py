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


############################ READ CSV ############################

with open(
    csv_path,
    newline="",
    encoding="utf-8-sig"
) as csvfile:

    reader = csv.DictReader(csvfile)

    required_columns = {
        "Drawer_ID",
        "Drawer_Order"
    }

    if not required_columns.issubset(
        reader.fieldnames or []
    ):
        raise ValueError(
            "CSV must contain columns named "
            "'Drawer_ID' and 'Drawer_Order'."
        )

    rows = list(reader)


print(
    f"\nFound {len(rows)} drawers in CSV."
)


############################ BUILD RENAME PLAN ############################

rename_plan = []

for row in rows:

    drawer_id = row["Drawer_ID"].strip()
    drawer_order_raw = row["Drawer_Order"].strip()

    if not drawer_id or not drawer_order_raw:
        raise ValueError(
            "CSV contains a blank Drawer_ID or Drawer_Order."
        )

    try:
        drawer_order = int(drawer_order_raw)
    except ValueError:
        raise ValueError(
            f"Invalid Drawer_Order: {drawer_order_raw}"
        )

    old_name = (
        f"drawer_{drawer_order:03d}_composite.JPG"
    )

    old_path = (
        composite_folder /
        old_name
    )

    new_name = (
        f"{drawer_id}.JPG"
    )

    new_path = (
        composite_folder /
        new_name
    )

    if not old_path.exists():
        raise FileNotFoundError(
            f"Expected composite does not exist: "
            f"{old_path}"
        )

    rename_plan.append(
        (
            old_path,
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