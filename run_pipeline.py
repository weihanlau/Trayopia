import os
import subprocess
import sys
import time
import urllib.request

start_time = time.time()

############################ SETTINGS ############################

# Choose inference method:
# "roboflow" = Roboflow hosted inference
# "local"    = local Roboflow Inference server
DEPLOYMENT = "roboflow"

# Choose best-view distance method:
# "normalized" = correct for different zoom levels
# "standard"   = use pixel distance when images are at the same zoom
DISTANCE_MODE = "normalized"

############################ PASS SETTINGS TO SCRIPTS ############################

if DEPLOYMENT not in ("roboflow", "local"):
    raise ValueError(
        'DEPLOYMENT must be either "roboflow" or "local"'
    )

if DISTANCE_MODE not in ("standard", "normalized"):
    raise ValueError(
        'DISTANCE_MODE must be either "standard" or "normalized"'
    )

env = os.environ.copy()
env["TRAYOPIA_DEPLOYMENT"] = DEPLOYMENT
env["TRAYOPIA_DISTANCE_MODE"] = DISTANCE_MODE

############################ FOR LOCAL INFERENCE ############################

def inference_server_running():
    try:
        urllib.request.urlopen(
            "http://localhost:9001",
            timeout=2
        )
        return True
    except:
        return False


if DEPLOYMENT == "local":

    if inference_server_running():
        print("Local inference server already running.")

    else:
        print("Starting local Roboflow Inference...")

        subprocess.run(
            [
                "docker", "start",
                "trayopia-inference"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # If the container doesn't exist yet, create it
        if not inference_server_running():

            subprocess.Popen(
                [
                    "docker", "run",
                    "-d",
                    "--name", "trayopia-inference",
                    "--restart", "unless-stopped",
                    "--gpus", "all",
                    "-p", "9001:9001",
                    "roboflow/roboflow-inference-server-gpu:latest"
                ]
            )

        print("Waiting for local inference server...")

        for _ in range(600):

            if inference_server_running():
                print("Local inference server ready.")
                break

            time.sleep(2)

        else:
            raise RuntimeError(
                "Local Roboflow Inference failed to start."
            )

############################ RUN TRAYOPIA ############################

scripts = [
    "prepare_images.py",
    "register_images.py",
    "detect_trays.py",
    "detect_labels_all_views.py",
    "choose_best_views.py",
    "build_composite.py"
]


for script in scripts:

    print("\n" + "=" * 60)
    print(f"RUNNING: {script}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script],
        env=env
    )

    if result.returncode != 0:
        print(f"\nPipeline stopped at: {script}")
        sys.exit(result.returncode)


elapsed_time = time.time() - start_time

minutes = int(elapsed_time // 60)
seconds = int(elapsed_time % 60)

print("\n" + "=" * 60)
print("PIPELINE COMPLETE")
print(f"Total time: {minutes}m {seconds}s")
print("=" * 60)

########################################################