"""
Image validation and preprocessing module for clothing pattern generator.

This module handles:
- Image quality validation
- Background removal
- Image normalization
- Image enhancement for feature detection
"""

import cv2
import numpy as np
from typing import Tuple, Dict, List, Optional, Union

class ImageValidator:
    """Class for validating input images of clothing items."""
    
    def __init__(self, min_resolution: Tuple[int, int] = (800, 800),
                 min_brightness: float = 0.3,
                 max_brightness: float = 0.8):
        """
        Initialize the image validator with quality thresholds.
        
        Args:
            min_resolution: Minimum acceptable image resolution (width, height)
            min_brightness: Minimum acceptable average brightness (0-1)
            max_brightness: Maximum acceptable average brightness (0-1)
        """
        self.min_resolution = min_resolution
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
    
    def validate(self, image: np.ndarray) -> Dict[str, Union[bool, str]]:
        """
        Validate an image for use in garment analysis.
        
        Args:
            image: OpenCV image in BGR format
            
        Returns:
            Dictionary with validation results and messages
        """
        result = {
            "valid": True,
            "messages": []
        }
        
        # Check resolution
        height, width = image.shape[:2]
        if width < self.min_resolution[0] or height < self.min_resolution[1]:
            result["valid"] = False
            result["messages"].append(
                f"Image resolution ({width}x{height}) is below minimum required "
                f"({self.min_resolution[0]}x{self.min_resolution[1]})"
            )
        
        # Check brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray) / 255.0
        if brightness < self.min_brightness:
            result["valid"] = False
            result["messages"].append(
                f"Image is too dark (brightness: {brightness:.2f}). "
                f"Minimum required: {self.min_brightness:.2f}"
            )
        elif brightness > self.max_brightness:
            result["valid"] = False
            result["messages"].append(
                f"Image is too bright (brightness: {brightness:.2f}). "
                f"Maximum allowed: {self.max_brightness:.2f}"
            )
        
        # Check contrast
        std_dev = np.std(gray) / 255.0
        if std_dev < 0.1:
            result["valid"] = False
            result["messages"].append(
                f"Image has low contrast (std dev: {std_dev:.2f}). "
                f"This may affect feature detection."
            )
        
        return result


class ImagePreprocessor:
    """Class for preprocessing clothing images for analysis."""
    
    def __init__(self, target_size: Optional[Tuple[int, int]] = None):
        """
        Initialize the image preprocessor.
        
        Args:
            target_size: Optional target size for resizing images (width, height)
        """
        self.target_size = target_size
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess an image for garment analysis.
        
        Args:
            image: OpenCV image in BGR format
            
        Returns:
            Preprocessed image
        """
        # Resize if target size is specified
        if self.target_size is not None:
            image = cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)
        
        # Apply histogram equalization to enhance contrast
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced_lab = cv2.merge((l, a, b))
        enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced_image
    
    def remove_background(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove background from clothing image.
        
        Args:
            image: OpenCV image in BGR format
            
        Returns:
            Tuple of (image with transparent background, binary mask)
        """
        # For a production system, we would use a more sophisticated segmentation model
        # Here we'll implement a simplified version using GrabCut algorithm
        
        # Create initial mask
        mask = np.zeros(image.shape[:2], np.uint8)
        
        # Assume the clothing item is roughly in the center
        height, width = image.shape[:2]
        rect = (width//6, height//6, 2*width//3, 2*height//3)
        
        # Background and foreground models
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # Apply GrabCut
        cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Create binary mask
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        
        # Apply mask to image
        rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = mask2 * 255
        
        return rgba, mask2 * 255
