"""
Pattern export module for generating output files in various formats.

This module handles:
- Exporting patterns as PDF files
- Generating vector formats (SVG, DXF)
- Creating pattern layout for efficient fabric cutting
- Generating construction instructions
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import os
import math

class PatternExporter:
    """Class for exporting patterns in various formats."""
    
    def __init__(self, output_dir: str):
        """
        Initialize the pattern exporter.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def export_svg(self, pattern_pieces: List[Dict[str, Any]], 
                  filename: str, 
                  include_seam_allowance: bool = True) -> str:
        """
        Export pattern pieces as SVG file.
        
        Args:
            pattern_pieces: List of 2D pattern piece dictionaries
            filename: Output filename
            include_seam_allowance: Whether to include seam allowance
            
        Returns:
            Path to the generated SVG file
        """
        # Create SVG file path
        svg_path = os.path.join(self.output_dir, filename)
        
        # Calculate overall dimensions
        min_x, min_y, max_x, max_y = self._calculate_bounding_box(pattern_pieces)
        
        # Add padding
        padding = 20
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding
        
        # Create SVG content
        svg_content = f'<svg width="{width}mm" height="{height}mm" viewBox="{min_x-padding} {min_y-padding} {width} {height}" xmlns="http://www.w3.org/2000/svg">\n'
        
        # Add each pattern piece
        for i, piece in enumerate(pattern_pieces):
            svg_content += self._pattern_piece_to_svg(piece, i, include_seam_allowance)
        
        # Close SVG
        svg_content += '</svg>'
        
        # Write to file
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        return svg_path
    
    def _calculate_bounding_box(self, pattern_pieces: List[Dict[str, Any]]) -> Tuple[float, float, float, float]:
        """
        Calculate the bounding box for all pattern pieces.
        
        Args:
            pattern_pieces: List of 2D pattern piece dictionaries
            
        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for piece in pattern_pieces:
            # Check vertices with seam allowance if available
            if "vertices_with_seam" in piece:
                vertices = piece["vertices_with_seam"]
            else:
                vertices = piece["vertices"]
            
            for vertex in vertices:
                min_x = min(min_x, vertex[0])
                min_y = min(min_y, vertex[1])
                max_x = max(max_x, vertex[0])
                max_y = max(max_y, vertex[1])
        
        return min_x, min_y, max_x, max_y
    
    def _pattern_piece_to_svg(self, piece: Dict[str, Any], index: int, 
                             include_seam_allowance: bool) -> str:
        """
        Convert a pattern piece to SVG elements.
        
        Args:
            piece: 2D pattern piece dictionary
            index: Index of the pattern piece
            include_seam_allowance: Whether to include seam allowance
            
        Returns:
            SVG content for the pattern piece
        """
        # Choose vertices based on seam allowance preference
        if include_seam_allowance and "vertices_with_seam" in piece:
            vertices = piece["vertices_with_seam"]
            stroke_color = "#000000"
        else:
            vertices = piece["vertices"]
            stroke_color = "#000000"
        
        # Create group for this pattern piece
        svg = f'  <g id="piece_{index}" transform="translate(0,0)">\n'
        
        # Create path for the outline
        path = '    <path d="M'
        
        # Add vertices to path
        for i, vertex in enumerate(vertices):
            if i == 0:
                path += f"{vertex[0]},{vertex[1]}"
            else:
                path += f" L{vertex[0]},{vertex[1]}"
        
        # Close path
        path += ' Z" '
        path += f'fill="none" stroke="{stroke_color}" stroke-width="0.5" />\n'
        
        svg += path
        
        # Add cut line (original vertices without seam allowance)
        if include_seam_allowance and "vertices" in piece:
            cut_vertices = piece["vertices"]
            cut_path = '    <path d="M'
            
            # Add vertices to path
            for i, vertex in enumerate(cut_vertices):
                if i == 0:
                    cut_path += f"{vertex[0]},{vertex[1]}"
                else:
                    cut_path += f" L{vertex[0]},{vertex[1]}"
            
            # Close path
            cut_path += ' Z" '
            cut_path += 'fill="none" stroke="#999999" stroke-width="0.25" stroke-dasharray="2,2" />\n'
            
            svg += cut_path
        
        # Add grain line if present
        if "grain_line" in piece:
            grain_line = piece["grain_line"]
            start = grain_line["start"]
            end = grain_line["end"]
            
            svg += f'    <line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" stroke="#000000" stroke-width="0.5" />\n'
            
            # Add arrowheads
            arrow_size = 5
            svg += f'    <polygon points="{start[0]},{start[1]} {start[0]-arrow_size/2},{start[1]+arrow_size} {start[0]+arrow_size/2},{start[1]+arrow_size}" fill="#000000" />\n'
            svg += f'    <polygon points="{end[0]},{end[1]} {end[0]-arrow_size/2},{end[1]-arrow_size} {end[0]+arrow_size/2},{end[1]-arrow_size}" fill="#000000" />\n'
        
        # Add darts if present
        if "darts" in piece:
            for dart in piece["darts"]:
                point = dart["point"]
                end = dart["end"]
                width = dart["width"]
                
                # Calculate dart legs
                dx = end[0] - point[0]
                dy = end[1] - point[1]
                length = math.sqrt(dx*dx + dy*dy)
                
                # Normalize direction vector
                if length > 0:
                    dx /= length
                    dy /= length
                
                # Calculate perpendicular vector
                perp_x = -dy
                perp_y = dx
                
                # Calculate dart points
                left_x = end[0] + perp_x * width / 2
                left_y = end[1] + perp_y * width / 2
                right_x = end[0] - perp_x * width / 2
                right_y = end[1] - perp_y * width / 2
                
                # Draw dart
                svg += f'    <path d="M{left_x},{left_y} L{point[0]},{point[1]} L{right_x},{right_y}" fill="none" stroke="#000000" stroke-width="0.5" />\n'
        
        # Add notches if present
        if "notches" in piece:
            for notch in piece["notches"]:
                position = notch["position"]
                
                # Draw notch as small triangle
                svg += f'    <circle cx="{position[0]}" cy="{position[1]}" r="2" fill="none" stroke="#000000" stroke-width="0.5" />\n'
        
        # Add label if present
        if "label" in piece:
            label = piece["label"]
            position = label["position"]
            text = label["text"]
            cut_qty = label["cut_qty"]
            
            svg += f'    <text x="{position[0]}" y="{position[1]}" font-family="Arial" font-size="10" text-anchor="middle">{text}</text>\n'
            svg += f'    <text x="{position[0]}" y="{position[1]+12}" font-family="Arial" font-size="8" text-anchor="middle">Cut: {cut_qty}</text>\n'
        
        # Close group
        svg += '  </g>\n'
        
        return svg
    
    def export_pdf(self, pattern_pieces: List[Dict[str, Any]], 
                  filename: str, 
                  include_seam_allowance: bool = True,
                  page_size: str = "A4") -> str:
        """
        Export pattern pieces as PDF file.
        
        Args:
            pattern_pieces: List of 2D pattern piece dictionaries
            filename: Output filename
            include_seam_allowance: Whether to include seam allowance
            page_size: Page size (A4, A3, etc.)
            
        Returns:
            Path to the generated PDF file
        """
        # For a production system, this would use a PDF generation library
        # For this placeholder, we'll generate an SVG and note that it would be converted to PDF
        
        # Generate SVG first
        svg_filename = os.path.splitext(filename)[0] + ".svg"
        svg_path = self.export_svg(pattern_pieces, svg_filename, include_seam_allowance)
        
        # Create PDF file path
        pdf_path = os.path.join(self.output_dir, filename)
        
        # In a real implementation, we would convert SVG to PDF here
        # For this placeholder, we'll create a text file noting the conversion
        with open(pdf_path, 'w') as f:
            f.write(f"This would be a PDF file generated from {svg_filename}\n")
            f.write(f"Page size: {page_size}\n")
            f.write(f"Include seam allowance: {include_seam_allowance}\n")
            f.write(f"Number of pattern pieces: {len(pattern_pieces)}\n")
        
        return pdf_path
    
    def export_dxf(self, pattern_pieces: List[Dict[str, Any]], 
                  filename: str, 
                  include_seam_allowance: bool = True) -> str:
        """
        Export pattern pieces as DXF file.
        
        Args:
            pattern_pieces: List of 2D pattern piece dictionaries
            filename: Output filename
            include_seam_allowance: Whether to include seam allowance
            
        Returns:
            Path to the generated DXF file
        """
        # For a production system, this would use a DXF generation library
        # For this placeholder, we'll create a text file noting the conversion
        
        # Create DXF file path
        dxf_path = os.path.join(self.output_dir, filename)
        
        # In a real implementation, we would generate a DXF file here
        # For this placeholder, we'll create a text file
        with open(dxf_path, 'w') as f:
            f.write(f"This would be a DXF file for pattern pieces\n")
            f.write(f"Include seam allowance: {include_seam_allowance}\n")
            f.write(f"Number of pattern pieces: {len(pattern_pieces)}\n")
            
            for i, piece in enumerate(pattern_pieces):
                f.write(f"\nPiece {i+1}: {piece.get('name', 'Unnamed')}\n")
                f.write(f"  Number of vertices: {len(piece['vertices'])}\n")
        
        return dxf_path
    
    def generate_layout(self, pattern_pieces: List[Dict[str, Any]], 
                       fabric_width: float, 
                       filename: str) -> str:
        """
        Generate an efficient fabric cutting layout.
        
        Args:
            pattern_pieces: List of 2D pattern piece dictionaries
            fabric_width: Width of fabric in cm
            filename: Output filename
            
        Returns:
            Path to the generated layout file
        """
        # For a production system, this would use a layout optimization algorithm
        # For this placeholder, we'll create a simple layout
        
        # Create layout file path
        layout_path = os.path.join(self.output_dir, filename)
        
        # Calculate layout dimensions
        min_x, min_y, max_x, max_y = self._calculate_bounding_box(pattern_pieces)
        
        # Create SVG content for layout
        svg_content = f'<svg width="{fabric_width}mm" height="{max_y-min_y+100}mm" viewBox="0 0 {fabric_width} {max_y-min_y+100}" xmlns="http://www.w3.org/2000/svg">\n'
        
        # Add fabric background
        svg_content += f'  <rect x="0" y="0" width="{fabric_width}" height="{max_y-min_y+100}" fill="#f0f0f0" />\n'
        
        # Add grid lines
        for i in range(0, int(fabric_width), 10):
            svg_content += f'  <line x1="{i}" y1="0" x2="{i}" y2="{max_y-min_y+100}" stroke="#cccccc" stroke-width="0.5" />\n'
        
        for i in range(0, int(max_y-min_y+100), 10):
            svg_content += f'  <line x1="0" y1="{i}" x2="{fabric_width}" y2="{i}" stroke="#cccccc" stroke-width="0.5" />\n'
        
        # Simple layout algorithm - just place pieces in a row
        x_offset = 10
        y_offset = 10
        
        for i, piece in enumerate(pattern_pieces):
            # Choose vertices with seam allowance if available
            if "vertices_with_seam" in piece:
                vertices = piece["vertices_with_seam"]
            else:
                vertices = piece["vertices"]
            
            # Calculate piece dimensions
            piece_min_x = min(v[0] for v in vertices)
            piece_min_y = min(v[1] for v in vertices)
            piece_max_x = max(v[0] for v in vertices)
            piece_max_y = max(v[1] for v in vertices)
            piece_width = piece_max_x - piece_min_x
            piece_height = piece_max_y - piece_min_y
            
            # Check if piece fits in current row
            if x_offset + piece_width > fabric_width:
                x_offset = 10
                y_offset += piece_height + 10
            
            # Add piece to layout
            svg_content += f'  <g transform="translate({x_offset-piece_min_x}, {y_offset-piece_min_y})">\n'
            
            # Add outline
            path = '    <path d="M'
            for j, vertex in enumerate(vertices):
                if j == 0:
                    path += f"{vertex[0]},{vertex[1]}"
                else:
                    path += f" L{vertex[0]},{vertex[1]}"
            path += ' Z" '
            path += 'fill="#ffffff" stroke="#000000" stroke-width="0.5" />\n'
            svg_content += path
            
            # Add label
            if "label" in piece:
                label = piece["label"]
                position = label["position"]
                text = label["text"]
                
                # Adjust position relative to piece
                pos_x = position[0]
                pos_y = position[1]
                
                svg_content += f'    <text x="{pos_x}" y="{pos_y}" font-family="Arial" font-size="10" text-anchor="middle">{text}</text>\n'
            
            svg_content += '  </g>\n'
            
            # Update x_offset for next piece
            x_offset += piece_width + 10
        
        # Close SVG
        svg_content += '</svg>'
        
        # Write to file
        with open(layout_path, 'w') as f:
            f.write(svg_content)
        
        return layout_path
    
    def generate_instructions(self, pattern_pieces: List[Dict[str, Any]], 
                             garment_type: str, 
                             filename: str) -> str:
        """
        Generate construction instructions.
        
        Args:
            pattern_pieces: List of 2D pattern piece dictionaries
            garment_type: Type of garment
            filename: Output filename
            
        Returns:
            Path to the generated instructions file
        """
        # Create instructions file path
        instructions_path = os.path.join(self.output_dir, filename)
        
        # Generate basic instructions based on garment type
        instructions = f"# Construction Instructions for {garment_type.capitalize()}
(Content truncated due to size limit. Use line ranges to read in chunks)