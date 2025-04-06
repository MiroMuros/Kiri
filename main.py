"""
Main application module for the Clothing Pattern Generator.

This module integrates all components and provides the entry point for the application.
"""

import os
import sys
from flask import Flask, render_template, send_from_directory

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from src.ui.app import app as flask_app
from src.image_processing.processor import ImageProcessor
from src.pattern_generation.generator import PatternGenerator

def main():
    """Main entry point for the application."""
    # Create necessary directories
    os.makedirs('/tmp/clothing_pattern_app/uploads', exist_ok=True)
    os.makedirs('/tmp/clothing_pattern_app/output', exist_ok=True)
    
    # Configure Flask app
    flask_app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src/ui')
    flask_app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src/ui/static')
    
    # Register additional routes
    @flask_app.route('/')
    def index():
        return render_template('index.html')
    
    @flask_app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory(flask_app.static_folder, path)
    
    # Run the application
    flask_app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
