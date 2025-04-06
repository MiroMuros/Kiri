"""
Unit tests for the Clothing Pattern Generator application.

This module contains tests for individual components of the application,
ensuring each module functions correctly in isolation.
"""

import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from src.image_processing.preprocessing import ImageValidator, ImagePreprocessor
from src.image_processing.garment_detection import GarmentClassifier, FeatureDetector
from src.pattern_generation.flattening import PatternSegmenter, PatternFlattener
from src.pattern_generation.annotation import PatternAnnotator
from src.pattern_generation.sizing import PatternSizer

class ImageProcessingTests(unittest.TestCase):
    """Unit tests for the image processing module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test image as numpy array
        self.test_image = np.zeros((300, 200, 3), dtype=np.uint8)
        # Add a simple shape to the image
        self.test_image[50:250, 50:150] = 255
        
        # Initialize components
        self.validator = ImageValidator()
        self.preprocessor = ImagePreprocessor()
        self.classifier = GarmentClassifier(None)
        self.feature_detector = FeatureDetector(None)
    
    def test_image_validator(self):
        """Test image validation functionality."""
        # Test valid image
        result = self.validator.validate(self.test_image)
        self.assertTrue(result["valid"])
        
        # Test invalid image (too small)
        small_image = np.zeros((50, 50, 3), dtype=np.uint8)
        result = self.validator.validate(small_image)
        self.assertFalse(result["valid"])
    
    def test_image_preprocessor(self):
        """Test image preprocessing functionality."""
        # Test preprocessing
        preprocessed = self.preprocessor.preprocess(self.test_image)
        self.assertEqual(preprocessed.shape, self.test_image.shape)
        
        # Test background removal
        rgba, mask = self.preprocessor.remove_background(self.test_image)
        self.assertEqual(rgba.shape[:2], self.test_image.shape[:2])
        self.assertEqual(mask.shape, self.test_image.shape[:2])
    
    @patch('src.image_processing.garment_detection.GarmentClassifier._load_model')
    def test_garment_classifier(self, mock_load):
        """Test garment classification functionality."""
        # Mock the model prediction
        self.classifier.model = MagicMock()
        self.classifier.model.predict.return_value = np.array([[0.8, 0.1, 0.1]])
        self.classifier.classes = ['shirt', 'dress', 'pants']
        
        # Test classification
        garment_type, confidence = self.classifier.get_top_prediction(self.test_image)
        self.assertEqual(garment_type, 'shirt')
        self.assertEqual(confidence, 0.8)
    
    @patch('src.image_processing.garment_detection.FeatureDetector._load_model')
    def test_feature_detector(self, mock_load):
        """Test feature detection functionality."""
        # Mock the model prediction
        self.feature_detector.model = MagicMock()
        self.feature_detector.model.predict.return_value = np.array([
            [100, 100],  # shoulder left
            [150, 100],  # shoulder right
            [125, 150],  # bust
            [125, 200]   # waist
        ])
        
        # Test feature detection
        features = self.feature_detector.detect_features(self.test_image, 'shirt')
        self.assertIn('shoulder_left', features)
        self.assertIn('shoulder_right', features)
        self.assertIn('bust', features)
        self.assertIn('waist', features)
        
        # Test visualization
        visualization = self.feature_detector.visualize_features(self.test_image, features)
        self.assertEqual(visualization.shape, self.test_image.shape)

class PatternGenerationTests(unittest.TestCase):
    """Unit tests for the pattern generation module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test 3D model
        self.test_model = {
            "type": "shirt",
            "measurements": {
                "bust": 100,
                "waist": 80,
                "hip": 105,
                "shoulder_width": 42,
                "length": 70
            },
            "vertices": [
                [0, 0, 0], [10, 0, 0], [10, 20, 0], [0, 20, 0],
                [0, 0, -5], [10, 0, -5], [10, 20, -5], [0, 20, -5]
            ],
            "faces": [
                [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
                [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
                [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]
            ]
        }
        
        # Initialize components
        self.segmenter = PatternSegmenter()
        self.flattener = PatternFlattener()
        self.annotator = PatternAnnotator(1.0)
        self.sizer = PatternSizer()
    
    def test_pattern_segmenter(self):
        """Test pattern segmentation functionality."""
        # Test segmentation
        pattern_pieces = self.segmenter.segment_model(self.test_model)
        self.assertGreater(len(pattern_pieces), 0)
        self.assertIn('name', pattern_pieces[0])
        self.assertIn('vertices', pattern_pieces[0])
        self.assertIn('faces', pattern_pieces[0])
    
    def test_pattern_flattener(self):
        """Test pattern flattening functionality."""
        # Get a pattern piece
        pattern_pieces = self.segmenter.segment_model(self.test_model)
        piece_3d = pattern_pieces[0]
        
        # Test flattening
        piece_2d = self.flattener.flatten_piece(piece_3d)
        self.assertIn('vertices', piece_2d)
        self.assertIn('faces', piece_2d)
        self.assertIn('distortion', piece_2d)
        
        # Test optimization
        optimized = self.flattener.optimize_pattern(piece_2d)
        self.assertIn('vertices', optimized)
        self.assertIn('faces', optimized)
    
    def test_pattern_annotator(self):
        """Test pattern annotation functionality."""
        # Get a flattened pattern piece
        pattern_pieces = self.segmenter.segment_model(self.test_model)
        piece_3d = pattern_pieces[0]
        piece_2d = self.flattener.flatten_piece(piece_3d)
        
        # Test seam allowance
        piece_with_seam = self.annotator.add_seam_allowance(piece_2d)
        self.assertIn('vertices_with_seam', piece_with_seam)
        self.assertIn('seam_allowance', piece_with_seam)
        
        # Test grain line
        piece_with_grain = self.annotator.add_grain_line(piece_2d)
        self.assertIn('grain_line', piece_with_grain)
        
        # Test labels
        piece_info = {
            "name": "Front",
            "cut_qty": 1,
            "fabric_type": "Main Fabric"
        }
        piece_with_label = self.annotator.add_labels(piece_2d, piece_info)
        self.assertIn('label', piece_with_label)
    
    def test_pattern_sizer(self):
        """Test pattern sizing functionality."""
        # Get a flattened pattern piece
        pattern_pieces = self.segmenter.segment_model(self.test_model)
        piece_3d = pattern_pieces[0]
        piece_2d = self.flattener.flatten_piece(piece_3d)
        
        # Original measurements
        original_measurements = {
            "bust": 100,
            "waist": 80,
            "hip": 105
        }
        
        # Target measurements
        target_measurements = {
            "bust": 110,
            "waist": 90,
            "hip": 115
        }
        
        # Test scaling
        scaled_piece = self.sizer.scale_pattern(piece_2d, original_measurements, target_measurements)
        self.assertIn('vertices', scaled_piece)
        
        # Verify scaling
        original_vertices = np.array(piece_2d['vertices'])
        scaled_vertices = np.array(scaled_piece['vertices'])
        
        # The scaled vertices should be larger
        original_width = np.max(original_vertices[:, 0]) - np.min(original_vertices[:, 0])
        scaled_width = np.max(scaled_vertices[:, 0]) - np.min(scaled_vertices[:, 0])
        self.assertGreater(scaled_width, original_width)

if __name__ == '__main__':
    unittest.main()
