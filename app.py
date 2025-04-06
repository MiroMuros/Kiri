"""
Flask application for the Clothing Pattern Generator.

This module provides the web server and API endpoints for the application,
connecting the UI with the image processing and pattern generation modules.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import uuid
from werkzeug.utils import secure_filename

# Import our modules
from ..image_processing.processor import ImageProcessor
from ..pattern_generation.generator import PatternGenerator

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/clothing_pattern_app/uploads'
OUTPUT_FOLDER = '/tmp/clothing_pattern_app/output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads for garment photos."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    view_type = request.form.get('view_type', 'front')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        unique_filename = f"{unique_id}_{filename}"
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'view_type': view_type,
            'file_path': file_path
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/process', methods=['POST'])
def process_images():
    """Process uploaded images and generate 3D model."""
    data = request.json
    
    if not data or 'images' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    
    # Get image paths
    image_paths = [os.path.join(app.config['UPLOAD_FOLDER'], img) for img in data['images']]
    
    # Create a session ID for this processing job
    session_id = str(uuid.uuid4())
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize image processor
        processor = ImageProcessor(model_dir=None)
        
        # Process images
        result = processor.process_multiple_images(image_paths, output_dir)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        # Save result metadata
        metadata_path = os.path.join(output_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump({
                'session_id': session_id,
                'garment_type': result['garment_type'],
                'measurements': result['measurements'],
                'files': result['files']
            }, f)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'garment_type': result['garment_type'],
            'measurements': result['measurements'],
            'model_path': result['files']['model_3d']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-pattern', methods=['POST'])
def generate_pattern():
    """Generate pattern based on 3D model and measurements."""
    data = request.json
    
    if not data or 'session_id' not in data:
        return jsonify({'error': 'No session ID provided'}), 400
    
    session_id = data['session_id']
    input_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_pattern")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load metadata
        metadata_path = os.path.join(input_dir, 'metadata.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Load 3D model
        model_path = metadata['files']['model_3d']
        
        # Get measurements from request or use original
        measurements = data.get('measurements', metadata['measurements'])
        
        # Get size from request
        size = data.get('size')
        
        # Initialize pattern generator
        generator = PatternGenerator(output_dir, seam_allowance=data.get('seam_allowance', 1.0))
        
        # Generate pattern
        # In a real implementation, we would load the 3D model from the file
        # For this placeholder, we'll create a simplified model
        model_3d = {
            "type": metadata['garment_type'],
            "measurements": measurements,
            "vertices": [[0, 0, 0], [10, 0, 0], [10, 20, 0], [0, 20, 0], 
                         [0, 0, -5], [10, 0, -5], [10, 20, -5], [0, 20, -5]],
            "faces": [[0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], 
                      [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], 
                      [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
        }
        
        # Generate pattern
        result = generator.generate_pattern(model_3d, measurements if size is None else None, size)
        
        # Save result metadata
        pattern_metadata_path = os.path.join(output_dir, 'pattern_metadata.json')
        with open(pattern_metadata_path, 'w') as f:
            json.dump({
                'session_id': session_id,
                'garment_type': result['garment_type'],
                'files': result['files']
            }, f)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'garment_type': result['garment_type'],
            'files': result['files']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<path:filename>')
def get_file(filename):
    """Serve generated files."""
    # Extract session ID from filename
    parts = filename.split('/')
    if len(parts) >= 2:
        session_id = parts[0]
        file_name = parts[-1]
        directory = os.path.join(app.config['OUTPUT_FOLDER'], '/'.join(parts[:-1]))
        return send_from_directory(directory, file_name)
    
    return jsonify({'error': 'Invalid file path'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
