import subprocess
import sys


scripts = [
    "prepare_images.py",
    "register_images.py",
    "detect_trays_roboflow.py",
    "detect_labels_all_views.py",
    "choose_best_views.py",
    "build_composite.py"
]


for script in scripts:

    print("\n" + "=" * 60)
    print(f"RUNNING: {script}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:
        print(f"\nPipeline stopped at: {script}")
        sys.exit(result.returncode)


print("\n" + "=" * 60)
print("PIPELINE COMPLETE")
print("=" * 60)