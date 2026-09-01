# Trayopia

Trayopia is a simple tool for combining multiple images of entomological drawers into a composite that provides unobscured views of specimens and labels within individual unit trays.

Whole-drawer imaging plays an increasing role as a starting point for digitizing entomological collections, but producing a single image that clearly captures every specimen and label can be challenging without specialized imaging systems (e.g. robotic imaging rigs, telecentric optical systems, etc.). One major problem that is often encounted in whole-drawer imaging is that entomological unit trays can obscure specimens and labels when drawers are photographed directly from above, particularly when objects sit close to the walls of a tray.

Trayopia addresses this problem by combining information from multiple photographs of the same drawer taken from different positions. The position of the drawer relative to the camera is changed between photographs, providing different views into each unit tray and revealing contents that may be obscured in other images.

Trayopia registers these images into a common coordinate system, identifies individual unit trays and their labels, selects the best view for each tray, and assembles the selected views into a single composite image. The resulting composite image can then be used as input for more complex whole-drawer processing pipelines, such as DrawerDissect.

## How it works

Trayopia processes multiple photographs of the same drawer through four main steps:

1. **Image registration:** ArUco markers are used to align each photograph to a common coordinate system.
2. **Tray and label detection:** An object-detection model (Roboflow) identifies individual unit trays and their labels.
3. **View selection:** For each tray, Trayopia selects a view based on its position relative to the camera and the visibility of its label.
4. **Compositing:** The selected tray views are assembled into a single composite image that preserves the original whole-drawer image.

## How Trayopia assigns "best views"

Currently, Trayopia uses a tiered approach to select the best view of each unit tray that will make thier way into the final composite imgae. Trayopia favours views in which the tray is closest to the centre of the camera (based on homography distance), while using the unit tray label area to override this choice when a unit tray's label is substantially more visible in another image. The logic is that trays closer to the camera centre are generally viewed more directly from above, while a larger detected label area provides an additional indication that the contents of the tray are less obscured by the tray walls.

Additional methods for selecting the optimal view of each unit tray will be added in future versions of Trayopia.

## Image capture protocol

Before imaging, place ArUco markers around the drawer as shown in the example below. The markers provide reference points that allow Trayopia to align the drawer across photographs.

Trayopia uses seven photographs per drawer. 

1. **Reference:** Centre the drawer beneath the camera so that all ArUco markers are visible. This image defines the layout of the final composite.
2. **Top left**
3. **Top centre**
4. **Top right**
5. **Bottom left**
6. **Bottom centre**
7. **Bottom right**

For each additional photograph, reposition the drawer relative to the camera so that different parts of the drawer are brought closer to the centre of the image. Keep the drawer flat and ensure that three ArUco markers remain visible in each photograph.

## Installation

Clone the repository and create a Python virtual environment.

### Installing on Windows

```powershell
git clone https://github.com/weihanlau/Trayopia.git
cd Trayopia

py -3.12 -m venv drawerenv
.\drawerenv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

### Installing on macOS / Linux

```bash
git clone https://github.com/weihanlau/Trayopia.git
cd Trayopia

python3.12 -m venv drawerenv
source drawerenv/bin/activate

python -m pip install -r requirements.txt
```

Trayopia has been developed and tested using **Python 3.12**.

### Configure the Roboflow API key

Trayopia uses Roboflow for unit-tray and label detection. A Roboflow API key is required to run the pipeline.

Create a file named `.env` in the main `Trayopia` directory and add your Roboflow API key:

```text
ROBOFLOW_API_KEY=your_roboflow_api_key_here
```

Your directory should then look like:

```text
Trayopia/
├── .env
├── run_pipeline.py
├── requirements.txt
└── ...
```

## Input

Trayopia requires seven images per drawer, captured in the order described in the [Image capture protocol](#image-capture-protocol). Image filenames do not matter, but **the order of the images does**.

Place the images in a single folder. When the pipeline is run, you will be prompted to provide the path to this folder when running the pipeline.

## Output

Trayopia produces one composite whole-drawer image for each set of seven input photographs. The composite combines the selected best view of each unit tray into a single image.

## Citation

If you use Trayopia in your work, please cite this GitHub repository.

## Etymology

**Trayopia** is a play on *myopia*. Suffering from pesky unit tray walls obscuring your specimens and labels? You've got a case of Trayopia... which is also the name of this tool. We should have thought more about the name of this thing.