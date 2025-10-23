# Probe Library Generator

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
- Save all files to `probe_outputs/` directory

### Process Single Probe

```bash
python process_single_probe.py manufacturer probe_name
```

Examples:
```bash
python process_single_probe.py neuronexus A1x32-Poly3-10mm-50-177
python process_single_probe.py cambridgeneurotech ASSY-37-E-1
```

### Discover Available Probes

```bash
python src/probe_library/discover_probes.py
```

This will test which probes are actually available in the probeinterface library.

## Currently Available Probes

Based on testing, these probes are available:

- **neuronexus/A1x32-Poly3-10mm-50-177** - 32 contacts, 1 shank
- **cambridgeneurotech/ASSY-37-E-1** - 32 contacts, 2 shanks
- **cambridgeneurotech/ASSY-77-E-1** - 64 contacts, 4 shanks
- **cambridgeneurotech/ASSY-156-P-1** - 64 contacts, 4 shanks
- **cambridgeneurotech/ASSY-116-P-1** - 32 contacts, 2 shanks

## Output Files

All generated files are saved to the `probe_outputs/` directory:

```
probe_outputs/
├── neuronexus_A1x32-Poly3-10mm-50-177.csv
├── neuronexus_A1x32-Poly3-10mm-50-177.obj
├── neuronexus_A1x32-Poly3-10mm-50-177_metadata.json
├── cambridgeneurotech_ASSY-37-E-1.csv
├── cambridgeneurotech_ASSY-37-E-1.obj
├── cambridgeneurotech_ASSY-37-E-1_metadata.json
└── ...
```

## Example Output

### CSV File
```csv
electrode_number,x,y,z,width,height,depth
1,0,450,0.0,20,20,20
2,0,500,0.0,20,20,20
3,0,400,0.0,20,20,20
...
```

### Metadata JSON
```json
{
  "name": "Neuronexus A1X32-Poly3-10Mm-50-177",
  "type": 1,
  "producer": "neuronexus",
  "sites": 32,
  "shanks": 1,
  "references": "Generated using probeinterface library",
  "spec": "https://probeinterface.readthedocs.io/"
}
```

## Notes

- Coordinates are in micrometers
- The probe tip is at the origin (0,0,0)
- OBJ files include both the probe shank and electrode contact geometry
- The tool automatically handles 2D to 3D conversion for probes
- SSL certificate verification is disabled to handle library download issues

## Troubleshooting

If you get SSL certificate errors, the scripts automatically handle this by disabling certificate verification for the probeinterface library downloads.

If a specific probe isn't available, check the available probe list using the discovery script.