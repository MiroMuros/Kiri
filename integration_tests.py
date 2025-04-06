"""
Integration tests for the Clothing Pattern Generator application.

This module contains tests to verify the integration between different components
of the application, ensuring they work together correctly.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from src.image_processing.processor import ImageProcessor
from src.pattern_generation.generator import PatternGenerator
from src.ui.app import app as flask_app

class IntegrationTests(unittest.TestCase):
    """Integration tests for the Clothing Pattern Generator application."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.test_upload_dir = tempfile.mkdtemp()
        self.test_output_dir = tempfile.mkdtemp()
        
        # Configure Flask app for testing
        flask_app.config['TESTING'] = True
        flask_app.config['UPLOAD_FOLDER'] = self.test_upload_dir
        flask_app.config['OUTPUT_FOLDER'] = self.test_output_dir
        self.app = flask_app.test_client()
        
        # Create test image
        self.test_image_path = os.path.join(self.test_upload_dir, 'test_image.jpg')
        with open(self.test_image_path, 'w') as f:
            f.write('dummy image content')
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directories
        shutil.rmtree(self.test_upload_dir)
        shutil.rmtree(self.test_output_dir)
    
    @patch('src.image_processing.processor.ImageProcessor.process_multiple_images')
    def test_image_processing_integration(self, mock_process):
        """Test integration between UI and image processing module."""
        # Mock the image processing result
        mock_result = {
            'garment_type': 'shirt',
            'measurements': {
                'bust': 100,
                'waist': 80,
                'hip': 105,
                'shoulder_width': 42,
                'length': 70
            },
            'files': {
                'model_3d': 'test_session/test_3d.obj'
            }
        }
        mock_process.return_value = mock_result
        
        # Test file upload
        with open(self.test_image_path, 'rb') as img:
            response = self.app.post(
                '/api/upload',
                data={
                    'file': (img, 'test_image.jpg'),
                    'view_type': 'front'
                },
                content_type='multipart/form-data'
            )
            
            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('filename', data)
            
            # Test image processing
            response = self.app.post(
                '/api/process',
                json={'images': [data['filename']]},
                content_type='application/json'
            )
            
            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['garment_type'], 'shirt')
            self.assertIn('measurements', data)
            self.assertIn('session_id', data)
    
    @patch('src.pattern_generation.generator.PatternGenerator.generate_pattern')
    def test_pattern_generation_integration(self, mock_generate):
        """Test integration between UI and pattern generation module."""
        # Mock the pattern generation result
        mock_result = {
            'garment_type': 'shirt',
            'pattern_pieces': [],
            'files': {
                'svg': 'test_session/shirt_pattern.svg',
                'pdf': 'test_session/shirt_pattern.pdf',
                'dxf': 'test_session/shirt_pattern.dxf',
                'layout': 'test_session/shirt_pattern_layout.svg',
                'instructions': 'test_session/shirt_pattern_instructions.md'
            }
        }
        mock_generate.return_value = mock_result
        
        # Create test session directory and metadata
        session_id = 'test_session'
        session_dir = os.path.join(self.test_output_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create metadata file
        metadata = {
            'session_id': session_id,
            'garment_type': 'shirt',
            'measurements': {
                'bust': 100,
                'waist': 80,
                'hip': 105
            },
            'files': {
                'model_3d': os.path.join(session_id, 'test_3d.obj')
            }
        }
        with open(os.path.join(session_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
        
        # Test pattern generation
        response = self.app.post(
            '/api/generate-pattern',
            json={
                'session_id': session_id,
                'measurements': {
                    'bust': 100,
                    'waist': 80,
                    'hip': 105
                },
                'seam_allowance': 1.0
            },
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['garment_type'], 'shirt')
        self.assertIn('files', data)
        self.assertIn('svg', data['files'])
        self.assertIn('pdf', data['files'])
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow from image upload to pattern generation."""
        # This would be a more comprehensive test in a real implementation
        # For this placeholder, we'll just verify the API endpoints exist
        
        # Test index page
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Test upload endpoint
        response = self.app.post('/api/upload')
        self.assertIn(response.status_code, [400, 415])  # Should fail without file
        
        # Test process endpoint
        response = self.app.post('/api/process', json={})
        self.assertIn(response.status_code, [400, 415])  # Should fail without images
        
        # Test generate-pattern endpoint
        response = self.app.post('/api/generate-pattern', json={})
        self.assertIn(response.status_code, [400, 415])  # Should fail without session_id

if __name__ == '__main__':
    unittest.main()
