"""
Main module for the pattern generation component of the clothing pattern generator.

This module integrates the flattening, annotation, sizing, and export
components into a complete pattern generation pipeline.
"""

import os
from typing import Dict, List, Tuple, Any, Optional

from .flattening import PatternSegmenter, PatternFlattener
from .annotation import PatternAnnotator, DartPlacer
from .sizing import PatternSizer, StandardSizer
from .export import PatternExporter

class PatternGenerator:
    """Main class for generating 2D patterns from 3D garment models."""
    
    def __init__(self, output_dir: str, seam_allowance: float = 1.0):
        """
        Initialize the pattern generator with all required components.
        
        Args:
            output_dir: Directory to save output files
            seam_allowance: Default seam allowance in cm
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.segmenter = PatternSegmenter()
        self.flattener = PatternFlattener()
        self.annotator = PatternAnnotator(seam_allowance)
        self.dart_placer = DartPlacer()
        self.sizer = PatternSizer()
        self.standard_sizer = StandardSizer()
        self.exporter = PatternExporter(output_dir)
        
        # Store output directory
        self.output_dir = output_dir
    
    def generate_pattern(self, model_3d: Dict[str, Any], 
                        target_measurements: Optional[Dict[str, float]] = None,
                        target_size: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete sewing pattern from a 3D garment model.
        
        Args:
            model_3d: 3D model dictionary from the reconstruction module
            target_measurements: Optional target measurements for scaling
            target_size: Optional target standard size (XS, S, M, L, XL)
            
        Returns:
            Dictionary with pattern generation results
        """
        # Extract garment type and measurements
        garment_type = model_3d["type"]
        original_measurements = model_3d["measurements"]
        
        # Step 1: Segment 3D model into pattern pieces
        pattern_pieces_3d = self.segmenter.segment_model(model_3d)
        
        # Step 2: Flatten 3D pattern pieces to 2D
        pattern_pieces_2d = []
        for piece_3d in pattern_pieces_3d:
            piece_2d = self.flattener.flatten_piece(piece_3d)
            pattern_pieces_2d.append(piece_2d)
        
        # Step 3: Add darts to pattern pieces
        pattern_pieces_with_darts = []
        for piece_2d in pattern_pieces_2d:
            dart_specs = self.dart_placer.generate_dart_specs(piece_2d, garment_type, original_measurements)
            piece_with_darts = self.dart_placer.add_darts(piece_2d, dart_specs)
            pattern_pieces_with_darts.append(piece_with_darts)
        
        # Step 4: Add construction details to pattern pieces
        pattern_pieces_annotated = []
        for piece_with_darts in pattern_pieces_with_darts:
            # Add seam allowance
            piece_with_seam = self.annotator.add_seam_allowance(piece_with_darts)
            
            # Add grain line
            piece_with_grain = self.annotator.add_grain_line(piece_with_seam)
            
            # Add labels
            piece_info = {
                "name": piece_with_grain["name"],
                "cut_qty": 1,
                "fabric_type": "Main Fabric"
            }
            piece_with_label = self.annotator.add_labels(piece_with_grain, piece_info)
            
            pattern_pieces_annotated.append(piece_with_label)
        
        # Step 5: Scale pattern pieces if needed
        final_pattern_pieces = []
        if target_measurements is not None:
            # Scale to custom measurements
            for piece in pattern_pieces_annotated:
                scaled_piece = self.sizer.scale_pattern(piece, original_measurements, target_measurements)
                final_pattern_pieces.append(scaled_piece)
        elif target_size is not None:
            # Scale to standard size
            for piece in pattern_pieces_annotated:
                scaled_piece = self.standard_sizer.scale_to_standard_size(piece, original_measurements, target_size)
                final_pattern_pieces.append(scaled_piece)
        else:
            # Use original size
            final_pattern_pieces = pattern_pieces_annotated
        
        # Step 6: Export pattern in various formats
        base_filename = f"{garment_type}_pattern"
        
        # Export SVG
        svg_path = self.exporter.export_svg(final_pattern_pieces, f"{base_filename}.svg")
        
        # Export PDF
        pdf_path = self.exporter.export_pdf(final_pattern_pieces, f"{base_filename}.pdf")
        
        # Export DXF
        dxf_path = self.exporter.export_dxf(final_pattern_pieces, f"{base_filename}.dxf")
        
        # Generate layout
        layout_path = self.exporter.generate_layout(final_pattern_pieces, 150, f"{base_filename}_layout.svg")
        
        # Generate instructions
        instructions_path = self.exporter.generate_instructions(final_pattern_pieces, garment_type, f"{base_filename}_instructions.md")
        
        # Return results
        return {
            "garment_type": garment_type,
            "pattern_pieces": final_pattern_pieces,
            "files": {
                "svg": svg_path,
                "pdf": pdf_path,
                "dxf": dxf_path,
                "layout": layout_path,
                "instructions": instructions_path
            }
        }
