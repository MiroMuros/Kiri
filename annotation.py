"""
Pattern annotation module for adding construction details to 2D patterns.

This module handles:
- Adding seam allowances to pattern pieces
- Placing darts and pleats
- Adding grain lines, notches, and other construction markings
- Generating pattern labels and instructions
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import math

class PatternAnnotator:
    """Class for adding construction details to 2D patterns."""
    
    def __init__(self, seam_allowance: float = 1.0):
        """
        Initialize the pattern annotator.
        
        Args:
            seam_allowance: Default seam allowance in cm
        """
        self.seam_allowance = seam_allowance
    
    def add_seam_allowance(self, pattern_2d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add seam allowance to a 2D pattern piece.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            
        Returns:
            Pattern piece with seam allowance
        """
        # Extract vertices and faces
        vertices = np.array(pattern_2d["vertices"])
        faces = pattern_2d["faces"]
        
        # Find boundary edges
        boundary_edges = self._find_boundary_edges(vertices, faces)
        
        # Create expanded vertices
        expanded_vertices = self._expand_boundary(vertices, boundary_edges, self.seam_allowance)
        
        # Create annotated pattern
        annotated_pattern = pattern_2d.copy()
        annotated_pattern["vertices_with_seam"] = expanded_vertices.tolist()
        annotated_pattern["seam_allowance"] = self.seam_allowance
        
        return annotated_pattern
    
    def _find_boundary_edges(self, vertices: np.ndarray, faces: List[List[int]]) -> List[Tuple[int, int]]:
        """
        Find boundary edges of a pattern piece.
        
        Args:
            vertices: 2D vertices
            faces: Face indices
            
        Returns:
            List of boundary edge vertex pairs
        """
        # Count occurrences of each edge
        edge_count = {}
        
        for face in faces:
            for i in range(len(face)):
                v1 = face[i]
                v2 = face[(i + 1) % len(face)]
                
                # Ensure consistent ordering
                edge = (min(v1, v2), max(v1, v2))
                
                if edge in edge_count:
                    edge_count[edge] += 1
                else:
                    edge_count[edge] = 1
        
        # Boundary edges appear only once
        boundary_edges = [edge for edge, count in edge_count.items() if count == 1]
        
        return boundary_edges
    
    def _expand_boundary(self, vertices: np.ndarray, boundary_edges: List[Tuple[int, int]], 
                        seam_allowance: float) -> np.ndarray:
        """
        Expand boundary by seam allowance.
        
        Args:
            vertices: 2D vertices
            boundary_edges: Boundary edge vertex pairs
            seam_allowance: Seam allowance amount
            
        Returns:
            Expanded vertices
        """
        # In a production system, this would use sophisticated algorithms
        # For this placeholder, we'll use a simplified approach
        
        # Create a copy of vertices
        expanded_vertices = vertices.copy()
        
        # Create a map of vertex to connected boundary edges
        vertex_to_edges = {}
        for v1, v2 in boundary_edges:
            if v1 not in vertex_to_edges:
                vertex_to_edges[v1] = []
            if v2 not in vertex_to_edges:
                vertex_to_edges[v2] = []
            
            vertex_to_edges[v1].append((v1, v2))
            vertex_to_edges[v2].append((v1, v2))
        
        # For each boundary vertex
        for vertex_idx in vertex_to_edges:
            # Get connected edges
            connected_edges = vertex_to_edges[vertex_idx]
            
            if len(connected_edges) == 2:
                # Regular boundary vertex with two connected edges
                edge1, edge2 = connected_edges
                
                # Get other vertices
                other_v1 = edge1[0] if edge1[1] == vertex_idx else edge1[1]
                other_v2 = edge2[0] if edge2[1] == vertex_idx else edge2[1]
                
                # Calculate edge vectors
                vec1 = vertices[other_v1] - vertices[vertex_idx]
                vec2 = vertices[other_v2] - vertices[vertex_idx]
                
                # Normalize
                vec1_norm = vec1 / np.linalg.norm(vec1)
                vec2_norm = vec2 / np.linalg.norm(vec2)
                
                # Calculate perpendicular vectors (rotate 90 degrees)
                perp1 = np.array([-vec1_norm[1], vec1_norm[0]])
                perp2 = np.array([-vec2_norm[1], vec2_norm[0]])
                
                # Calculate bisector
                bisector = perp1 + perp2
                
                # Normalize bisector
                if np.linalg.norm(bisector) > 0:
                    bisector = bisector / np.linalg.norm(bisector)
                else:
                    # If vectors are opposite, use perpendicular
                    bisector = perp1
                
                # Scale by seam allowance
                offset = bisector * seam_allowance
                
                # Apply offset
                expanded_vertices[vertex_idx] = vertices[vertex_idx] + offset
            
            elif len(connected_edges) == 1:
                # End vertex with one connected edge
                edge = connected_edges[0]
                
                # Get other vertex
                other_v = edge[0] if edge[1] == vertex_idx else edge[1]
                
                # Calculate edge vector
                vec = vertices[other_v] - vertices[vertex_idx]
                
                # Normalize
                vec_norm = vec / np.linalg.norm(vec)
                
                # Calculate perpendicular vector (rotate 90 degrees)
                perp = np.array([-vec_norm[1], vec_norm[0]])
                
                # Scale by seam allowance
                offset = perp * seam_allowance
                
                # Apply offset
                expanded_vertices[vertex_idx] = vertices[vertex_idx] + offset
        
        return expanded_vertices
    
    def add_grain_line(self, pattern_2d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add grain line to a 2D pattern piece.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            
        Returns:
            Pattern piece with grain line
        """
        # Extract vertices
        vertices = np.array(pattern_2d["vertices"])
        
        # Calculate bounding box
        min_x = np.min(vertices[:, 0])
        max_x = np.max(vertices[:, 0])
        min_y = np.min(vertices[:, 1])
        max_y = np.max(vertices[:, 1])
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Calculate grain line (vertical by default)
        grain_length = (max_y - min_y) * 0.7
        grain_start = [center_x, center_y - grain_length / 2]
        grain_end = [center_x, center_y + grain_length / 2]
        
        # Add grain line to pattern
        annotated_pattern = pattern_2d.copy()
        annotated_pattern["grain_line"] = {
            "start": grain_start,
            "end": grain_end
        }
        
        return annotated_pattern
    
    def add_notches(self, pattern_2d: Dict[str, Any], seam_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add notches to a 2D pattern piece.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            seam_points: List of seam points that need notches
            
        Returns:
            Pattern piece with notches
        """
        # In a production system, this would use sophisticated algorithms
        # For this placeholder, we'll use a simplified approach
        
        # Add notches to pattern
        annotated_pattern = pattern_2d.copy()
        annotated_pattern["notches"] = seam_points
        
        return annotated_pattern
    
    def add_labels(self, pattern_2d: Dict[str, Any], piece_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add labels to a 2D pattern piece.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            piece_info: Information about the pattern piece
            
        Returns:
            Pattern piece with labels
        """
        # Extract vertices
        vertices = np.array(pattern_2d["vertices"])
        
        # Calculate bounding box
        min_x = np.min(vertices[:, 0])
        max_x = np.max(vertices[:, 0])
        min_y = np.min(vertices[:, 1])
        max_y = np.max(vertices[:, 1])
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Create label
        label = {
            "position": [center_x, center_y],
            "text": piece_info.get("name", "Unknown"),
            "cut_qty": piece_info.get("cut_qty", 1),
            "fabric_type": piece_info.get("fabric_type", "Main Fabric"),
            "notes": piece_info.get("notes", "")
        }
        
        # Add label to pattern
        annotated_pattern = pattern_2d.copy()
        annotated_pattern["label"] = label
        
        return annotated_pattern


class DartPlacer:
    """Class for placing darts on 2D patterns."""
    
    def __init__(self):
        """Initialize the dart placer."""
        pass
    
    def add_darts(self, pattern_2d: Dict[str, Any], dart_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add darts to a 2D pattern piece.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            dart_specs: List of dart specifications
            
        Returns:
            Pattern piece with darts
        """
        # In a production system, this would use sophisticated algorithms
        # For this placeholder, we'll use a simplified approach
        
        # Add darts to pattern
        pattern_with_darts = pattern_2d.copy()
        pattern_with_darts["darts"] = dart_specs
        
        return pattern_with_darts
    
    def generate_dart_specs(self, pattern_2d: Dict[str, Any], 
                           garment_type: str, 
                           measurements: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Generate dart specifications based on garment type and measurements.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            garment_type: Type of garment
            measurements: Garment measurements
            
        Returns:
            List of dart specifications
        """
        # In a production system, this would use sophisticated algorithms
        # For this placeholder, we'll return simplified dart specs
        
        dart_specs = []
        
        # Extract vertices
        vertices = np.array(pattern_2d["vertices"])
        
        # Calculate bounding box
        min_x = np.min(vertices[:, 0])
        max_x = np.max(vertices[:, 0])
        min_y = np.min(vertices[:, 1])
        max_y = np.max(vertices[:, 1])
        
        # Generate darts based on garment type
        if pattern_2d["name"] == "Front" and garment_type in ["shirt", "blouse", "dress"]:
            # Add bust darts
            dart_point = [min_x + (max_x - min_x) * 0.3, min_y + (max_y - min_y) * 0.3]
            dart_end = [min_x + (max_x - min_x) * 0.5, min_y + (max_y - min_y) * 0.4]
            dart_width = 2.0  # cm
            
            dart_specs.append({
                "type": "bust_dart",
                "point": dart_point,
                "end": dart_end,
                "width": dart_width
            })
        
        elif pattern_2d["name"] == "Back" and garment_type in ["shirt", "blouse", "dress"]:
            # Add back darts
            dart_point = [min_x + (max_x - min_x) * 0.5, min_y + (max_y - min_y) * 0.3]
            dart_end = [min_x + (max_x - min_x) * 0.5, min_y + (max_y - min_y) * 0.5]
            dart_width = 1.5  # cm
            
            dart_specs.append({
                "type": "back_dart",
                "point": dart_point,
                "end": dart_end,
                "width": dart_width
            })
        
        elif pattern_2d["name"] in ["Front", "Back"] and garment_type in ["skirt", "pants", "jeans"]:
            # Add waist darts
            dart_point = [min_x + (max_x - min_x) * 0.5, min_y + (max_y - min_y) * 0.1]
            dart_end = [min_x + (max_x - min_x) * 0.5, min_y + (max_y - min_y) * 0.3]
            dart_width = 2.0  # cm
            
            dart_specs.append({
                "type": "waist_dart",
                "point": dart_point,
                "end": dart_end,
                "width": dart_width
            })
        
        return dart_specs
