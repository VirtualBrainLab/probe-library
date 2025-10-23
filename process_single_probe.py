"""
Simple probe processor - generate CSV, OBJ, and metadata for specific probes.

Usage:
    python process_single_probe.py manufacturer probe_name
    
Example:
    python process_single_probe.py neuronexus A1x32-Poly3-10mm-50-177
"""

import sys
import ssl
import csv
import json
import numpy as np
from pathlib import Path

from probeinterface import get_probe
from src.probe_library.obj_generator import generate_probe_obj

# Setup SSL to avoid certificate issues
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

def generate_csv(probe, output_path):
    """Generate CSV file with electrode information."""
    positions = probe.contact_positions
    n_contacts = probe.get_contact_count()
    
    # Get contact shapes and parameters
    contact_shapes = getattr(probe, 'contact_shapes', ['circle'] * n_contacts)
    shape_params = getattr(probe, 'contact_shape_params', [{'radius': 10}] * n_contacts)
    
    if len(shape_params) != n_contacts:
        shape_params = [{'radius': 10}] * n_contacts
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['electrode_number', 'x', 'y', 'z', 'width', 'height', 'depth'])
        
        for i in range(n_contacts):
            electrode_num = i + 1
            
            if probe.ndim == 2:
                x, y = positions[i]
                z = 0.0
            else:
                x, y, z = positions[i]
            
            shape = contact_shapes[i] if i < len(contact_shapes) else 'circle'
            params = shape_params[i] if i < len(shape_params) else {'radius': 10}
            
            if shape == 'circle':
                radius = params.get('radius', 10)
                width = height = depth = 2 * radius
            elif shape == 'square':
                side = params.get('width', 20)
                width = height = depth = side
            elif shape == 'rect':
                width = params.get('width', 20)
                height = params.get('height', 10)
                depth = min(width, height)
            else:
                width = height = depth = 20
            
            writer.writerow([electrode_num, x, y, z, width, height, depth])

def generate_obj(probe, output_path):
    """Generate OBJ file using advanced probe geometry."""
    return generate_probe_obj(probe, Path(output_path))

def generate_metadata(probe, output_path, probe_type, manufacturer):
    """Generate metadata JSON file."""
    metadata = {
        "name": probe.annotations.get('model_name', 'Unknown Probe'),
        "type": probe_type,
        "producer": manufacturer,
        "sites": probe.get_contact_count(),
        "shanks": probe.get_shank_count(),
        "references": "Generated using probeinterface library",
        "spec": "https://probeinterface.readthedocs.io/"
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    if len(sys.argv) != 3:
        print("Usage: python process_single_probe.py manufacturer probe_name")
        print("\nAvailable probes:")
        print("  neuronexus A1x32-Poly3-10mm-50-177")
        print("  cambridgeneurotech ASSY-37-E-1")
        print("  cambridgeneurotech ASSY-77-E-1") 
        print("  cambridgeneurotech ASSY-156-P-1")
        print("  cambridgeneurotech ASSY-116-P-1")
        sys.exit(1)
    
    manufacturer = sys.argv[1]
    probe_name = sys.argv[2]
    
    print(f"Loading probe: {manufacturer}/{probe_name}")
    
    try:
        probe = get_probe(manufacturer, probe_name)
        print(f"✓ Loaded: {probe.get_contact_count()} contacts, {probe.get_shank_count()} shanks")
    except Exception as e:
        print(f"✗ Failed to load probe: {e}")
        return
    
    # Create output directory
    output_dir = Path("probe_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Generate files
    base_name = f"{manufacturer}_{probe_name}"
    
    try:
        generate_csv(probe, output_dir / f"{base_name}.csv")
        print(f"✓ Generated: {base_name}.csv")
        
        generate_obj(probe, output_dir / f"{base_name}.obj")
        print(f"✓ Generated: {base_name}.obj")
        
        generate_metadata(probe, output_dir / f"{base_name}_metadata.json", 1, manufacturer)
        print(f"✓ Generated: {base_name}_metadata.json")
        
        print(f"\nAll files saved to: {output_dir.absolute()}")
        
    except Exception as e:
        print(f"✗ Error generating files: {e}")

if __name__ == "__main__":
    main()