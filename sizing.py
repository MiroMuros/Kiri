"""
Size adjustment module for scaling patterns to different measurements.

This module handles:
- Scaling pattern pieces based on user measurements
- Applying grading rules for different sizes
- Maintaining proportions during scaling
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class PatternSizer:
    """Class for scaling pattern pieces to different sizes."""
    
    def __init__(self):
        """Initialize the pattern sizer."""
        pass
    
    def scale_pattern(self, pattern_2d: Dict[str, Any], 
                     original_measurements: Dict[str, float],
                     target_measurements: Dict[str, float]) -> Dict[str, Any]:
        """
        Scale a pattern piece to match target measurements.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            original_measurements: Original garment measurements
            target_measurements: Target measurements for scaling
            
        Returns:
            Scaled pattern piece
        """
        # Calculate scaling factors
        scaling_factors = self._calculate_scaling_factors(original_measurements, target_measurements)
        
        # Apply scaling to pattern
        scaled_pattern = self._apply_scaling(pattern_2d, scaling_factors)
        
        return scaled_pattern
    
    def _calculate_scaling_factors(self, original_measurements: Dict[str, float],
                                 target_measurements: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate scaling factors for different dimensions.
        
        Args:
            original_measurements: Original garment measurements
            target_measurements: Target measurements for scaling
            
        Returns:
            Dictionary of scaling factors for different dimensions
        """
        scaling_factors = {}
        
        # Calculate scaling factor for each measurement
        for key in original_measurements:
            if key in target_measurements and original_measurements[key] > 0:
                scaling_factors[key] = target_measurements[key] / original_measurements[key]
        
        # If no specific measurements match, use general scaling
        if not scaling_factors:
            # Default to no scaling
            scaling_factors["default"] = 1.0
        
        return scaling_factors
    
    def _apply_scaling(self, pattern_2d: Dict[str, Any], 
                      scaling_factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Apply scaling factors to a pattern piece.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            scaling_factors: Dictionary of scaling factors
            
        Returns:
            Scaled pattern piece
        """
        # Extract vertices
        vertices = np.array(pattern_2d["vertices"])
        
        # Calculate center for scaling
        center = np.mean(vertices, axis=0)
        
        # Determine appropriate scaling factors for X and Y dimensions
        scale_x = scaling_factors.get("width", 
                  scaling_factors.get("shoulder_width", 
                  scaling_factors.get("waist_width", 
                  scaling_factors.get("default", 1.0))))
        
        scale_y = scaling_factors.get("length", 
                  scaling_factors.get("inseam", 
                  scaling_factors.get("default", 1.0)))
        
        # Scale vertices
        scaled_vertices = []
        for vertex in vertices:
            # Vector from center to vertex
            v = vertex - center
            
            # Scale
            v_scaled = [v[0] * scale_x, v[1] * scale_y]
            
            # New vertex position
            new_vertex = center + v_scaled
            scaled_vertices.append(new_vertex.tolist())
        
        # Create scaled pattern
        scaled_pattern = pattern_2d.copy()
        scaled_pattern["vertices"] = scaled_vertices
        
        # Scale other elements if present
        if "vertices_with_seam" in pattern_2d:
            vertices_with_seam = np.array(pattern_2d["vertices_with_seam"])
            scaled_vertices_with_seam = []
            
            for vertex in vertices_with_seam:
                # Vector from center to vertex
                v = vertex - center
                
                # Scale
                v_scaled = [v[0] * scale_x, v[1] * scale_y]
                
                # New vertex position
                new_vertex = center + v_scaled
                scaled_vertices_with_seam.append(new_vertex.tolist())
            
            scaled_pattern["vertices_with_seam"] = scaled_vertices_with_seam
        
        # Scale grain line if present
        if "grain_line" in pattern_2d:
            grain_line = pattern_2d["grain_line"]
            start = np.array(grain_line["start"])
            end = np.array(grain_line["end"])
            
            # Vector from center to points
            v_start = start - center
            v_end = end - center
            
            # Scale
            v_start_scaled = [v_start[0] * scale_x, v_start[1] * scale_y]
            v_end_scaled = [v_end[0] * scale_x, v_end[1] * scale_y]
            
            # New positions
            new_start = center + v_start_scaled
            new_end = center + v_end_scaled
            
            scaled_pattern["grain_line"] = {
                "start": new_start.tolist(),
                "end": new_end.tolist()
            }
        
        # Scale darts if present
        if "darts" in pattern_2d:
            scaled_darts = []
            
            for dart in pattern_2d["darts"]:
                point = np.array(dart["point"])
                end = np.array(dart["end"])
                
                # Vector from center to points
                v_point = point - center
                v_end = end - center
                
                # Scale
                v_point_scaled = [v_point[0] * scale_x, v_point[1] * scale_y]
                v_end_scaled = [v_end[0] * scale_x, v_end[1] * scale_y]
                
                # New positions
                new_point = center + v_point_scaled
                new_end = center + v_end_scaled
                
                # Scale width
                new_width = dart["width"] * ((scale_x + scale_y) / 2)
                
                scaled_darts.append({
                    "type": dart["type"],
                    "point": new_point.tolist(),
                    "end": new_end.tolist(),
                    "width": new_width
                })
            
            scaled_pattern["darts"] = scaled_darts
        
        # Scale notches if present
        if "notches" in pattern_2d:
            scaled_notches = []
            
            for notch in pattern_2d["notches"]:
                position = np.array(notch["position"])
                
                # Vector from center to position
                v_position = position - center
                
                # Scale
                v_position_scaled = [v_position[0] * scale_x, v_position[1] * scale_y]
                
                # New position
                new_position = center + v_position_scaled
                
                scaled_notches.append({
                    "type": notch["type"],
                    "position": new_position.tolist()
                })
            
            scaled_pattern["notches"] = scaled_notches
        
        # Scale label if present
        if "label" in pattern_2d:
            label = pattern_2d["label"]
            position = np.array(label["position"])
            
            # Vector from center to position
            v_position = position - center
            
            # Scale
            v_position_scaled = [v_position[0] * scale_x, v_position[1] * scale_y]
            
            # New position
            new_position = center + v_position_scaled
            
            scaled_pattern["label"] = {
                "position": new_position.tolist(),
                "text": label["text"],
                "cut_qty": label["cut_qty"],
                "fabric_type": label["fabric_type"],
                "notes": label["notes"]
            }
        
        return scaled_pattern


class StandardSizer:
    """Class for applying standard sizing to patterns."""
    
    # Standard size measurements (simplified)
    STANDARD_SIZES = {
        "XS": {
            "bust": 82,
            "waist": 62,
            "hip": 87,
            "shoulder_width": 36,
            "back_length": 38
        },
        "S": {
            "bust": 88,
            "waist": 68,
            "hip": 93,
            "shoulder_width": 38,
            "back_length": 39
        },
        "M": {
            "bust": 94,
            "waist": 74,
            "hip": 99,
            "shoulder_width": 40,
            "back_length": 40
        },
        "L": {
            "bust": 100,
            "waist": 80,
            "hip": 105,
            "shoulder_width": 42,
            "back_length": 41
        },
        "XL": {
            "bust": 106,
            "waist": 86,
            "hip": 111,
            "shoulder_width": 44,
            "back_length": 42
        }
    }
    
    def __init__(self):
        """Initialize the standard sizer."""
        pass
    
    def get_standard_measurements(self, size: str) -> Dict[str, float]:
        """
        Get standard measurements for a given size.
        
        Args:
            size: Size code (XS, S, M, L, XL)
            
        Returns:
            Dictionary of standard measurements
        """
        if size in self.STANDARD_SIZES:
            return self.STANDARD_SIZES[size]
        else:
            # Return medium size as default
            return self.STANDARD_SIZES["M"]
    
    def scale_to_standard_size(self, pattern_2d: Dict[str, Any], 
                              original_measurements: Dict[str, float],
                              target_size: str) -> Dict[str, Any]:
        """
        Scale a pattern piece to a standard size.
        
        Args:
            pattern_2d: 2D pattern piece dictionary
            original_measurements: Original garment measurements
            target_size: Target standard size
            
        Returns:
            Scaled pattern piece
        """
        # Get standard measurements for target size
        target_measurements = self.get_standard_measurements(target_size)
        
        # Create pattern sizer
        sizer = PatternSizer()
        
        # Scale pattern
        scaled_pattern = sizer.scale_pattern(pattern_2d, original_measurements, target_measurements)
        
        return scaled_pattern
