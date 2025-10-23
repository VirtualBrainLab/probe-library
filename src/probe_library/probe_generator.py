"""
Probe Library Generator

This module uses probeinterface to load probes from the library and generate
the output files needed by Pinpoint:
1. CSV file with electrode positions, dimensions
2. OBJ file with 3D probe geometry
"""

import ssl
import csv
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from probeinterface import get_probe, Probe
from probeinterface import (
    generate_dummy_probe,
    generate_linear_probe,
    generate_multi_columns_probe,
)
from probe_library.obj_generator import generate_probe_obj


class ProbeLibraryGenerator:
    """Generate probe files for Pinpoint from probeinterface library."""

    def __init__(self, output_dir: str = "output"):
        """Initialize generator with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create SSL context that doesn't verify certificates (for library downloads)
        self._setup_ssl_context()

    def _setup_ssl_context(self):
        """Setup SSL context to handle certificate issues."""
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
        except AttributeError:
            pass

    def get_available_probe_specs(self) -> List[Dict[str, Any]]:
        """List all available probes from the probeinterface_library git submodule."""
        from pathlib import Path

        base = Path(__file__).parent.parent.parent / "probeinterface_library"
        probe_specs = []
        for manufacturer in base.iterdir():
            if (
                manufacturer.is_dir()
                and not manufacturer.name.startswith(".")
                and manufacturer.name != ".github"
            ):
                for probe in manufacturer.iterdir():
                    if probe.is_dir():
                        probe_specs.append(
                            {
                                "manufacturer": manufacturer.name,
                                "probe_name": probe.name,
                            }
                        )
        return probe_specs

    def load_probe_from_library(
        self, manufacturer: str, probe_name: str
    ) -> Optional[Probe]:
        """Load a probe from the probeinterface library."""
        try:
            probe = get_probe(manufacturer, probe_name)
            print(
                f"✓ Loaded {manufacturer}/{probe_name}: "
                f"{probe.get_contact_count()} contacts"
            )
            return probe
        except Exception as e:
            print(f"✗ Failed to load {manufacturer}/{probe_name}: {str(e)}")
            return None

    def generate_demo_probes(self) -> List[Tuple[str, Probe]]:
        """Generate demo probes using probeinterface generators."""
        demo_probes = []

        # Linear probe
        try:
            linear_probe = generate_linear_probe(num_elec=32, ypitch=25.0)
            linear_probe.create_auto_shape(probe_type="tip")
            demo_probes.append(("linear_32ch", linear_probe))
            print("✓ Generated linear 32-channel probe")
        except Exception as e:
            print(f"✗ Failed to generate linear probe: {e}")

        # Multi-column probe
        try:
            multi_probe = generate_multi_columns_probe(
                num_columns=4,
                num_contact_per_column=8,
                xpitch=20.0,
                ypitch=25.0,
                contact_shapes="circle",
                contact_shape_params={"radius": 6},
            )
            multi_probe.create_auto_shape(probe_type="rect")
            demo_probes.append(("multi_column_4x8", multi_probe))
            print("✓ Generated multi-column 4x8 probe")
        except Exception as e:
            print(f"✗ Failed to generate multi-column probe: {e}")

        # Dummy probe for testing
        try:
            dummy_probe = generate_dummy_probe(elec_shapes="circle")
            dummy_probe.create_auto_shape(probe_type="tip")
            demo_probes.append(("dummy_probe", dummy_probe))
            print("✓ Generated dummy probe")
        except Exception as e:
            print(f"✗ Failed to generate dummy probe: {e}")

        return demo_probes

    def probe_to_csv(
        self, probe: Probe, filename: str, manufacturer: str = "unknown"
    ) -> bool:
        """
        Generate CSV file with electrode information for Pinpoint.

        CSV format: electrode_number, x, y, z, width, height, depth
        Coordinates are relative to the probe tip.
        """
        try:
            # Get contact positions (relative to tip)
            positions = probe.contact_positions
            n_contacts = probe.get_contact_count()

            # Get contact shapes and parameters
            contact_shapes = getattr(
                probe, "contact_shapes", ["circle"] * n_contacts
            )
            shape_params = getattr(
                probe, "contact_shape_params", [{"radius": 10}] * n_contacts
            )

            # Ensure we have the right number of shape parameters
            if len(shape_params) != n_contacts:
                default_params = {"radius": 10}
                first_param = (
                    shape_params[0] if shape_params else default_params
                )
                shape_params = [first_param] * n_contacts

            out_dir = self.output_dir / manufacturer / filename
            out_dir.mkdir(parents=True, exist_ok=True)
            csv_path = out_dir / f"{filename}.csv"

            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow(
                    [
                        "electrode_number",
                        "x",
                        "y",
                        "z",
                        "width",
                        "height",
                        "depth",
                    ]
                )

                for i in range(n_contacts):
                    # Electrode number (1-based)
                    electrode_num = i + 1

                    # Position relative to tip (convert to micrometers if needed)
                    if probe.ndim == 2:
                        x, y = positions[i]
                        z = 0.0
                    else:
                        x, y, z = positions[i]

                    # Determine dimensions based on contact shape
                    shape = (
                        contact_shapes[i]
                        if i < len(contact_shapes)
                        else "circle"
                    )
                    params = (
                        shape_params[i]
                        if i < len(shape_params)
                        else {"radius": 10}
                    )

                    if shape == "circle":
                        radius = params.get("radius", 10)
                        width = height = depth = 2 * radius
                    elif shape == "square":
                        side = params.get("width", 20)
                        width = height = depth = side
                    elif shape == "rect":
                        width = params.get("width", 20)
                        height = params.get("height", 10)
                        depth = min(width, height)
                    else:
                        # Default dimensions
                        width = height = depth = 20

                    writer.writerow(
                        [electrode_num, x, y, z, width, height, depth]
                    )

            print(f"✓ Generated CSV: {csv_path}")
            return True

        except Exception as e:
            print(f"✗ Failed to generate CSV for {filename}: {e}")
            return False

    def probe_to_obj(
        self, probe: Probe, filename: str, manufacturer: str = "unknown"
    ) -> bool:
        """
        Generate OBJ file with 3D probe geometry using proper contour.

        Uses the advanced OBJ generator that respects probe planar contours
        including triangular tips and multi-shank geometry.
        """
        try:
            out_dir = self.output_dir / manufacturer / filename
            out_dir.mkdir(parents=True, exist_ok=True)
            obj_path = out_dir / f"{filename}.obj"
            success = generate_probe_obj(probe, obj_path)

            if success:
                print(f"✓ Generated OBJ: {obj_path}")
            else:
                print(f"✗ Failed to generate OBJ for {filename}")

            return success

        except Exception as e:
            print(f"✗ Failed to generate OBJ for {filename}: {e}")
            return False

    def generate_metadata_json(
        self,
        probe: Probe,
        filename: str,
        probe_type: int,
        manufacturer: str = "unknown",
    ) -> bool:
        try:
            import json
            import numpy as np

            contour = np.array(getattr(probe, "probe_planar_contour", []))
            tip_coords = []
            if contour.shape[0] > 0:
                # Find all points with the minimum y value (the tips)
                min_y = np.min(contour[:, 1])
                tip_points = contour[np.isclose(contour[:, 1], min_y)]
                # If multiple tips at same y, group by unique x
                unique_x = np.unique(np.round(tip_points[:, 0], decimals=2))
                for x in unique_x:
                    tip = tip_points[
                        np.isclose(np.round(tip_points[:, 0], decimals=2), x)
                    ][0]
                    tip_coords.append([float(tip[0]), float(tip[1]), 0.0])
            else:
                # fallback: use lowest y contact for each shank
                positions = np.array(probe.contact_positions)
                shank_ids = np.array(probe.shank_ids)
                unique_shanks = np.unique(shank_ids)
                ndim = probe.ndim
                for shank in unique_shanks:
                    shank_positions = positions[shank_ids == shank]
                    if shank_positions.shape[0] == 0:
                        tip_coords.append(None)
                        continue
                    tip_elec = shank_positions[
                        np.argmin(shank_positions[:, 1])
                    ]
                    if ndim == 2:
                        x, y = tip_elec
                        z = 0.0
                    else:
                        x, y, z = tip_elec
                    tip_coords.append([float(x), float(y), float(z)])
            metadata = {
                "name": filename.replace("_", " ").title(),
                "type": probe_type,
                "producer": manufacturer,
                "sites": probe.get_contact_count(),
                "shanks": probe.get_shank_count(),
                "tip_coordinates": tip_coords,
                "references": "Generated using probeinterface library",
                "spec": "https://probeinterface.readthedocs.io/",
            }
            out_dir = self.output_dir / manufacturer / filename
            out_dir.mkdir(parents=True, exist_ok=True)
            json_path = out_dir / f"{filename}_metadata.json"
            with open(json_path, "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"✓ Generated metadata: {json_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to generate metadata for {filename}: {e}")
            return False

    def process_probe(
        self,
        probe: Probe,
        name: str,
        probe_type: int,
        manufacturer: str = "unknown",
    ) -> bool:
        """Process a single probe and generate all required files."""
        print(f"\nProcessing probe: {name}")
        print(f"  Contacts: {probe.get_contact_count()}")
        print(f"  Dimensions: {probe.ndim}D")
        print(f"  Shanks: {probe.get_shank_count()}")

        success = True
        success &= self.probe_to_csv(probe, name, manufacturer)
        success &= self.probe_to_obj(probe, name, manufacturer)
        success &= self.generate_metadata_json(
            probe, name, probe_type, manufacturer
        )
        return success

    def process_all_probes(self):
        """Process all available probes from library and generate demo probes."""
        print("Probe Library Generator")
        print("=" * 50)

        probe_type_counter = 1
        successful_probes = 0

        # Try to load probes from the library
        print("\nTrying to load probes from probeinterface library...")
        probe_specs = self.get_available_probe_specs()

        for spec in probe_specs:
            probe = self.load_probe_from_library(
                spec["manufacturer"], spec["probe_name"]
            )
            if probe is not None:
                name = f"{spec['manufacturer']}_{spec['probe_name']}"
                if self.process_probe(
                    probe, name, probe_type_counter, spec["manufacturer"]
                ):
                    successful_probes += 1
                probe_type_counter += 1

        # Generate demo probes
        print("\nGenerating demo probes...")
        demo_probes = self.generate_demo_probes()

        for name, probe in demo_probes:
            if self.process_probe(probe, name, probe_type_counter, "demo"):
                successful_probes += 1
            probe_type_counter += 1

        print(f"\nSummary:")
        print(f"Total processed: {successful_probes} probes")
        print(f"Output directory: {self.output_dir.absolute()}")


def main():
    """Main function to run the probe generator."""
    generator = ProbeLibraryGenerator("probe_outputs")
    generator.process_all_probes()


if __name__ == "__main__":
    main()
