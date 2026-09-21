import subprocess
import sys
import shutil
from pathlib import Path

########################################################


def run_script(script):

    print("\n" + "=" * 60)
    print(f"RUNNING: {script}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:
        print(f"\nPipeline stopped at: {script}")
        sys.exit(result.returncode)


########################################################
# CLEAN OLD COMPARISON RESULTS
########################################################

for folder in [
    "detections_original",
    "composites_original",
    "detections_field",
    "composites_field"
]:
    path = Path(folder)

    if path.exists():
        shutil.rmtree(path)


########################################################
# PREPARE + REGISTER ONCE
########################################################

run_script("prepare_images.py")
run_script("register_images.py")


########################################################
# RUN ORIGINAL MODELS
########################################################

print("\n" + "#" * 60)
print("ORIGINAL MODELS")
print("#" * 60)

run_script("detect_trays_roboflow.py")
run_script("detect_labels_all_views.py")
run_script("choose_best_views.py")
run_script("build_composite.py")


# Save original results

shutil.copytree(
    "detections",
    "detections_original"
)

shutil.copytree(
    "composites",
    "composites_original"
)


########################################################
# RUN FIELD MUSEUM MODELS
########################################################

print("\n" + "#" * 60)
print("FIELD MUSEUM MODELS")
print("#" * 60)

# Clear working outputs so Field results start clean

shutil.rmtree("detections")
shutil.rmtree("composites")

Path("detections").mkdir()
Path("composites").mkdir()


run_script("detect_trays_roboflow_FieldModels.py")
run_script("detect_labels_all_views_FieldModels.py")
run_script("choose_best_views.py")
run_script("build_composite.py")


# Save Field Museum results

shutil.copytree(
    "detections",
    "detections_field"
)

shutil.copytree(
    "composites",
    "composites_field"
)


########################################################

print("\n" + "=" * 60)
print("MODEL COMPARISON COMPLETE")
print("=" * 60)

print("\nOriginal model results:")
print("  detections_original/")
print("  composites_original/")

print("\nField Museum model results:")
print("  detections_field/")
print("  composites_field/")

########################################################