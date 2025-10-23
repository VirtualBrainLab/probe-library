"""
Advanced OBJ file generator for neural probes.

This module generates 3D OBJ files using the actual probe contour information
from probeinterface, including proper tip geometry and multi-shank support.
"""

import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

from probeinterface import Probe


class ProbeOBJGenerator:
    """Generate OBJ files with proper probe geometry."""

    def __init__(self):
        self.vertices = []
        self.faces = []
        self.vertex_count = 0

    def reset(self):
        """Reset generator for a new probe."""
        self.vertices = []
        self.faces = []
        self.vertex_count = 0

    def add_vertex(self, x: float, y: float, z: float) -> int:
        """Add a vertex and return its 1-based index (OBJ format)."""
        self.vertices.append([x, y, z])
        self.vertex_count += 1
        return self.vertex_count

    def add_face(self, vertex_indices: List[int]):
        """Add a face using 1-based vertex indices."""
        self.faces.append(vertex_indices)

    def extrude_contour(
        self, contour_points: np.ndarray, z_bottom: float, z_top: float
    ) -> Tuple[List[int], List[int]]:
        """
        Extrude a 2D contour to create 3D geometry.
        Returns bottom and top vertex indices.
        """
        bottom_indices = []
        top_indices = []

        for point in contour_points:
            x, y = point
            bottom_idx = self.add_vertex(x, y, z_bottom)
            top_idx = self.add_vertex(x, y, z_top)
            bottom_indices.append(bottom_idx)
            top_indices.append(top_idx)

        return bottom_indices, top_indices

    def create_faces_from_contour(
        self, bottom_indices: List[int], top_indices: List[int]
    ):
        """Create faces for an extruded contour."""
        n_points = len(bottom_indices)

        # Bottom face (reverse order for correct normal)
        if n_points >= 3:
            self.add_face(list(reversed(bottom_indices)))

        # Top face
        if n_points >= 3:
            self.add_face(top_indices)

        # Side faces
        for i in range(n_points):
            next_i = (i + 1) % n_points

            # Create quad face for each side
            face = [
                bottom_indices[i],
                bottom_indices[next_i],
                top_indices[next_i],
                top_indices[i],
            ]
            self.add_face(face)

    def add_contact_geometry(self, probe: Probe, contact_height: float = 2.0):
        """Add individual contact geometry to the mesh."""
        positions = probe.contact_positions
        contact_shapes = getattr(
            probe, "contact_shapes", ["circle"] * len(positions)
        )
        shape_params = getattr(
            probe, "contact_shape_params", [{"radius": 10}] * len(positions)
        )

        # Convert 2D positions to 3D if needed
        if probe.ndim == 2:
            positions_3d = np.column_stack(
                [positions, np.zeros(len(positions))]
            )
        else:
            positions_3d = positions

        for i, pos in enumerate(positions_3d):
            shape = contact_shapes[i] if i < len(contact_shapes) else "circle"
            params = (
                shape_params[i] if i < len(shape_params) else {"radius": 10}
            )

            if shape == "circle":
                radius = params.get("radius", 10)
                self._add_circular_contact(pos, radius, contact_height)
            elif shape in ["square", "rect"]:
                width = params.get("width", 20)
                height = params.get("height", width)
                self._add_rectangular_contact(
                    pos, width, height, contact_height
                )

    def _add_circular_contact(
        self,
        position: np.ndarray,
        radius: float,
        height: float,
        n_segments: int = 8,
    ):
        """Add a circular contact as a cylinder."""
        x, y, z = position

        # Generate circle points
        angles = np.linspace(0, 2 * np.pi, n_segments, endpoint=False)

        bottom_indices = []
        top_indices = []

        for angle in angles:
            cx = x + radius * np.cos(angle)
            cy = y + radius * np.sin(angle)

            bottom_idx = self.add_vertex(cx, cy, z - height / 2)
            top_idx = self.add_vertex(cx, cy, z + height / 2)

            bottom_indices.append(bottom_idx)
            top_indices.append(top_idx)

        # Create faces
        self.create_faces_from_contour(bottom_indices, top_indices)

    def _add_rectangular_contact(
        self,
        position: np.ndarray,
        width: float,
        height: float,
        thickness: float,
    ):
        """Add a rectangular contact."""
        x, y, z = position

        # Rectangle corners
        corners = [
            [x - width / 2, y - height / 2],
            [x + width / 2, y - height / 2],
            [x + width / 2, y + height / 2],
            [x - width / 2, y + height / 2],
        ]

        bottom_indices = []
        top_indices = []

        for corner in corners:
            cx, cy = corner
            bottom_idx = self.add_vertex(cx, cy, z - thickness / 2)
            top_idx = self.add_vertex(cx, cy, z + thickness / 2)
            bottom_indices.append(bottom_idx)
            top_indices.append(top_idx)

        self.create_faces_from_contour(bottom_indices, top_indices)

    def generate_probe_mesh(
        self,
        probe: Probe,
        probe_thickness: float = 20.0,
        contact_height: float = 2.0,
        add_contacts: bool = False,
    ) -> bool:
        """
        Generate complete probe mesh including shank and contacts.

        Args:
            probe: Probe object from probeinterface
            probe_thickness: Thickness of the probe shank (in micrometers)
            contact_height: Height of contact geometry (in micrometers)
            add_contacts: Whether to add individual contact geometry (ignored, always False)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.reset()

            # Get probe planar contour
            contour = probe.probe_planar_contour
            if contour is None or len(contour) < 3:
                print(
                    "Warning: No valid planar contour found, generating basic shape"
                )
                return self._generate_basic_probe_shape(
                    probe, probe_thickness, contact_height, False
                )

            print(f"Using probe contour with {len(contour)} points")

            # Extrude the probe contour to create the main shank
            bottom_indices, top_indices = self.extrude_contour(
                contour, -probe_thickness / 2, probe_thickness / 2
            )

            # Create faces for the main probe body
            self.create_faces_from_contour(bottom_indices, top_indices)
            return True

        except Exception as e:
            print(f"Error generating probe mesh: {e}")
            return False

    def _generate_basic_probe_shape(
        self,
        probe: Probe,
        probe_thickness: float,
        contact_height: float,
        add_contacts: bool = False,
    ) -> bool:
        """Fallback method to generate basic rectangular probe shape."""
        try:
            positions = probe.contact_positions
            if probe.ndim == 2:
                positions_3d = np.column_stack(
                    [positions, np.zeros(len(positions))]
                )
            else:
                positions_3d = positions

            # Calculate bounds
            min_coords = np.min(positions_3d, axis=0)
            max_coords = np.max(positions_3d, axis=0)

            # Add margins
            margin = 30.0
            x_min, x_max = min_coords[0] - margin, max_coords[0] + margin
            y_min, y_max = min_coords[1] - margin, max_coords[1] + margin

            # Create basic rectangular contour
            basic_contour = np.array(
                [
                    [x_min, y_max],
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                ]
            )

            bottom_indices, top_indices = self.extrude_contour(
                basic_contour, -probe_thickness / 2, probe_thickness / 2
            )

            self.create_faces_from_contour(bottom_indices, top_indices)
            return True

        except Exception as e:
            print(f"Error generating basic probe shape: {e}")
            return False

    def save_obj(self, filepath: Path, probe_name: str = "probe") -> bool:
        """Save the generated mesh to an OBJ file."""
        try:
            with open(filepath, "w") as f:
                f.write(f"# Probe: {probe_name}\n")
                f.write(f"# Generated by ProbeOBJGenerator\n")
                f.write(f"# Vertices: {len(self.vertices)}\n")
                f.write(f"# Faces: {len(self.faces)}\n\n")

                # Write vertices
                for vertex in self.vertices:
                    f.write(
                        f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n"
                    )

                f.write("\n")

                # Write faces
                for face in self.faces:
                    f.write(f"f {' '.join(map(str, face))}\n")

            print(f"✓ Saved OBJ: {filepath}")
            return True

        except Exception as e:
            print(f"✗ Error saving OBJ: {e}")
            return False


def generate_probe_obj(
    probe: Probe,
    output_path: Path,
    probe_thickness: float = 20.0,
    contact_height: float = 2.0,
    add_contacts: bool = False,
) -> bool:
    """
    Convenience function to generate OBJ file for a probe.

    Args:
        probe: Probe object from probeinterface
        output_path: Path where to save the OBJ file
        probe_thickness: Thickness of probe shank in micrometers
        contact_height: Height of contact geometry in micrometers
        add_contacts: Whether to include individual contact geometry (ignored, always False)

    Returns:
        True if successful, False otherwise
    """
    generator = ProbeOBJGenerator()
    if generator.generate_probe_mesh(
        probe, probe_thickness, contact_height, False
    ):
        probe_name = getattr(probe, "model_name", output_path.stem)
        return generator.save_obj(output_path, probe_name)
    return False


if __name__ == "__main__":
    # Test the generator
    from probeinterface import get_probe, generate_linear_probe

    print("Testing ProbeOBJGenerator...")

    # Test with library probe
    probe = get_probe("neuronexus", "A1x32-Poly3-10mm-50-177")
    output_path = Path("test_neuronexus.obj")

    if generate_probe_obj(probe, output_path):
        print(f"Successfully generated: {output_path}")

    # Test with generated probe
    linear_probe = generate_linear_probe(num_elec=16, ypitch=20)
    linear_probe.create_auto_shape(probe_type="tip")

    output_path2 = Path("test_linear_tip.obj")
    if generate_probe_obj(linear_probe, output_path2):
        print(f"Successfully generated: {output_path2}")
