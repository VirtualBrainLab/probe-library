# Probe Library

This tool uses probeinterface to generate CSV and OBJ files for neural probes that are compatible with Pinpoint.

## Files Generated

For each probe, the tool generates:

1. **CSV file** - Electrode positions and dimensions (`probe_name.csv`)
2. **OBJ file** - 3D geometry of the probe (`probe_name.obj`)  
3. **Metadata JSON** - Probe specifications (`probe_name_metadata.json`)

## CSV Format

The CSV file contains electrode information with these columns:
- `electrode_number`: 1-based electrode number
- `x`, `y`, `z`: Electrode position relative to probe tip (micrometers)
- `width`, `height`, `depth`: Electrode dimensions (micrometers)

## Installation

Make sure you have the virtual environment set up:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install required packages (already done)
pip install probeinterface numpy
```

## Usage

### Process All Available Probes

```bash
python src/probe_library/probe_generator.py
```

This will:
- Try to load all known probes from the probeinterface library
- Generate demo probes (linear, multi-column, dummy)
- Save all files to `probe_outputs/<manufacturer>/<probe_name>` directory

## Notes

- Coordinates are in micrometers
- The origin (0,0,0) is the bottom/left corner of the bottom/left-most electrode
