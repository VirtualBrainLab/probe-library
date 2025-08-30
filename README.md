# Probe Library

This readme describes specifications for describing **probes**. These are 3D objects that do not change physical shape during an experiment and have locations along the probe whose position inside the brain are of interest, these might be electrode contacts or 

The individual folders in this repository are used to generate the probes in [Pinpoint](https://github.com/virtualBrainLab/pinpoint).

## Probe

A probe is a 3D object with one or more shanks each of which have sites on them.

File | Description
---|---
metadata.json | probe metadata, in JSON format
model.obj | 3D model of the probe shanks and any attached silicon, the tip of the reference shank is at the origin
hardware/your_hardware.obj | (optional) 3D model of additional hardware attached to the probe, the origin of the hardware model should be at the tip of the reference shank
site_map.csv | coordinates of electrode surface relative to the tip and selection layers
scripts/ | (optional) If you used any scripts to generate your probe 3D model or site_map, please include them here for reproducibility

### metadata.json

Field | Type | Example | Description
---|---|---|---
name | string | Neuropixels 1.0 | Full name of the probe
type | int | 1 | Unique ID that can identify this probe, this must be different from all other probes in the library
producer | string | "imec" | Company or insitutition producing the probe
sites | int | 960 | Number of channels on the probe
shanks | int | 1 | Number of physical shanks
references | string | "https://www.nature.com/articles/nature24636" | Reference papers about the probe
spec | string | "https://www.neuropixels.org/_files/ugd/328966_c5e4d31e8a974962b5eb8ec975408c9f.pdf" | Specifications for the probe

Example for Neuropixels 1.0:

```
{
  "name":"Neuropixels 1.0",
  "type":"1"
  "producer":"imec",
  "sites":"960",
  "shanks":"1",
  "references":"https://www.nature.com/articles/nature24636",
  "spec":"https://www.neuropixels.org/_files/ugd/328966_c5e4d31e8a974962b5eb8ec975408c9f.pdf"
}
```

### model.obj

3D model of the probe with the surface of the tip at the origin. The probe model should be at "rest" according to the Pinpoint convention. In Unity this means that the .obj file is rotated such that the shanks are pointing along the +Z axis, while the site surface points along the +Y axis. On multi-shank probes the reference shank should be at the origin (i.e. additional shanks should be offset in the -X direction).

In Blender this convention corresponds to the shanks pointing along the -Y axis, the site surface pointing along the +Z axis, and additional shanks should be offset in the +X direction.

#### hardware.obj

Additional 3D model files can be included. For example, you may want a 3D model for the circuit boards that are often attached to the actual probe shanks, or for the parts that connect the probe to a micro-manipulator. These additional hardware models will be *fixed* to the probe when displayed in Pinpoint, they cannot be animated or moved inside the program (as of v1.1).

Each .obj file included in the hardware folder will be available as a separate optional 3D model to display and check collisions against. Please group 3D models that are always attached together into a single file.

### site_map.csv

The site map defines the locations of electrode contacts or other points of interest on the probe shanks. In Pinpoint these are the anatomical locations visible on the site maps and can be rendered on the 3D model as well. The first seven columns define the site positions and size relative to the origin (tip) of the probe. The remaining columns define layer options for controlling which sites are actually displayed.

Fields: index, x, y, z, w, h, d, default, layer1, layer2, ...

Example for Neuropixels 1.0:

| index     | x   | y   | z | w  | h  | d  | default | all | bank0 | double_length |
|-----------|-----|-----|---|----|----|----|---------|-----|-------|---------------|
| 0         | -14 | 200 | 0 | 12 | 12 | 24 | 1       | 1   | 1     | 0             |
| 1         | 18  | 200 | 0 | 12 | 12 | 24 | 1       | 1   | 1     | 1             |
| 2         | -30 | 220 | 0 | 12 | 12 | 24 | 1       | 1   | 1     | 0             |
| 3         | 2   | 220 | 0 | 12 | 12 | 24 | 1       | 1   | 1     | 1             |

# Contributing

You can contribute your own probe models to the library and have them included in Pinpoint. Pinpoint is built every 1-2 weeks, if you need to put a 3D model temporarily into the Pinpoint scene you should use the Pinpoint API. To make a new contribution:

 1. Fork the respository
 2. Copy an existing probe folder
 3. Modify the folder to match your new probe
 4. Submit a pull request, your probe metadata and site_map files will run against our automated tests to validate their format. Note that no tests are run on 3D model files.
 5. Once your pull requested is merged, your probe files will automatically be included in future builds of Pinpoint
