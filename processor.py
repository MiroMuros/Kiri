"""
Main module for the image processing component of the clothing pattern generator.

This module integrates the preprocessing, garment detection, and 3D reconstruction
components into a complete image processing pipeline.
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

from .preprocessing import ImageValidator, ImagePreprocessor
from .garment_detection import GarmentClassifier, FeatureDetector, MeasurementEstimator
from .reconstruction import GarmentReconstructor

class ImageProcessor:
    """Main class for processing clothing images and generating 3D models."""
    
    def __init__(self, 
                 model_dir: Optional[str] = None,
                 reference_object_size: Optional[float] = None):
        """
        Initialize the image processor with all required components.
        
        Args:
            model_dir: Directory containing model files
            reference_object_size: Size of reference object in cm, if available
        """
        # Initialize components
        self.validator = ImageValidator()
        self.preprocessor = ImagePreprocessor()
        
        # Set model paths
        classifier_model = os.path.join(model_dir, "classifier.h5") if model_dir else None
        feature_model = os.path.join(model_dir, "feature_detector.h5") if model_dir else None
        template_dir = os.path.join(model_dir, "templates") if model_dir else None
        
        # Initialize detection and reconstruction components
        self.classifier = GarmentClassifier(classifier_model)
        self.feature_detector = FeatureDetector(feature_model)
        self.measurement_estimator = MeasurementEstimator(reference_object_size)
        self.reconstructor = GarmentReconstructor(template_dir)
    
    def process_image(self, image_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Process a clothing image and generate a 3D model.
        
        Args:
            image_path: Path to the input image
            output_dir: Directory to save output files
            
        Returns:
            Dictionary with processing results
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return {"error": f"Failed to load image: {image_path}"}
        
        # Validate image
        validation_result = self.validator.validate(image)
        if not validation_result["valid"]:
            return {
                "error": "Image validation failed",
                "messages": validation_result["messages"]
            }
        
        # Preprocess image
        preprocessed = self.preprocessor.preprocess(image)
        
        # Remove background
        rgba, mask = self.preprocessor.remove_background(preprocessed)
        
        # Classify garment
        garment_type, confidence = self.classifier.get_top_prediction(preprocessed)
        if garment_type == "unknown":
            return {
                "error": "Unable to classify garment type",
                "confidence": confidence
            }
        
        # Detect features
        features = self.feature_detector.detect_features(preprocessed, garment_type)
        
        # Visualize features
        visualized = self.feature_detector.visualize_features(preprocessed, features)
        
        # Estimate measurements
        measurements = self.measurement_estimator.estimate_measurements(features, garment_type)
        
        # Reconstruct 3D model
        model_3d = self.reconstructor.reconstruct_3d_model(features, garment_type, measurements)
        
        # Save outputs
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # Save preprocessed image
        preprocessed_path = os.path.join(output_dir, f"{base_name}_preprocessed.jpg")
        cv2.imwrite(preprocessed_path, preprocessed)
        
        # Save visualization
        visualization_path = os.path.join(output_dir, f"{base_name}_features.jpg")
        cv2.imwrite(visualization_path, visualized)
        
        # Save 3D model
        model_path = os.path.join(output_dir, f"{base_name}_3d.obj")
        self.reconstructor.export_obj(model_3d, model_path)
        
        # Return results
        return {
            "garment_type": garment_type,
            "confidence": confidence,
            "measurements": measurements,
            "features": features,
            "model_3d": model_3d,
            "files": {
                "preprocessed": preprocessed_path,
                "visualization": visualization_path,
                "model_3d": model_path
            }
        }
    
    def process_multiple_images(self, image_paths: List[str], output_dir: str) -> Dict[str, Any]:
        """
        Process multiple images of the same garment from different angles.
        
        Args:
            image_paths: List of paths to input images
            output_dir: Directory to save output files
            
        Returns:
            Dictionary with processing results
        """
        # Process first image to get garment type and initial features
        primary_result = self.process_image(image_paths[0], output_dir)
        if "error" in primary_result:
            return primary_result
        
        # Process additional images if available
        additional_features = []
        for i, path in enumerate(image_paths[1:], 1):
            result = self.process_image(path, output_dir)
            if "error" not in result and result["garment_type"] == primary_result["garment_type"]:
                additional_features.append(result["features"])
        
        # In a real implementation, we would merge features from multiple views
        # For this placeholder, we'll just use the primary result
        
        return primary_result
