"""
JavaScript functionality for the Clothing Pattern Generator UI.

This module provides the client-side functionality for the web interface,
handling API calls, form validation, and UI interactions.
"""

// Global state to store uploaded images and processing results
const appState = {
    images: {
        front: null,
        back: null,
        side: null,
        details: []
    },
    sessionId: null,
    measurements: {},
    patternFiles: {}
};

// API endpoints
const API = {
    upload: '/api/upload',
    process: '/api/process',
    generatePattern: '/api/generate-pattern',
    files: '/api/files'
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUploads();
    initializeMeasurementForm();
    initializePatternGeneration();
    initializeExportButtons();
});

// Initialize file upload handlers
function initializeFileUploads() {
    // Front view upload
    document.getElementById('front-upload').addEventListener('change', function(e) {
        handleImageUpload(e, 'front-preview', 'front');
    });
    
    // Back view upload
    document.getElementById('back-upload').addEventListener('change', function(e) {
        handleImageUpload(e, 'back-preview', 'back');
    });
    
    // Side view upload
    document.getElementById('side-upload').addEventListener('change', function(e) {
        handleImageUpload(e, 'side-preview', 'side');
    });
    
    // Detail photos upload
    document.getElementById('detail-upload').addEventListener('change', function(e) {
        handleImageUpload(e, 'detail-preview', 'details', true);
    });
}

// Handle image upload and preview
function handleImageUpload(event, previewId, viewType, multiple = false) {
    const files = event.target.files;
    const previewElement = document.getElementById(previewId);
    
    previewElement.innerHTML = '';
    
    if (multiple) {
        // Reset details array
        appState.images.details = [];
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.type.match('image.*')) {
                // Upload file to server
                uploadFile(file, viewType, function(response) {
                    if (response.success) {
                        appState.images.details.push(response.filename);
                        
                        // Create preview
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const img = document.createElement('img');
                            img.src = e.target.result;
                            img.className = 'preview-image me-2 mb-2';
                            img.style.maxHeight = '150px';
                            previewElement.appendChild(img);
                        }
                        reader.readAsDataURL(file);
                    } else {
                        showError('Failed to upload image: ' + (response.error || 'Unknown error'));
                    }
                });
            }
        }
    } else {
        if (files.length > 0 && files[0].type.match('image.*')) {
            const file = files[0];
            
            // Upload file to server
            uploadFile(file, viewType, function(response) {
                if (response.success) {
                    appState.images[viewType] = response.filename;
                    
                    // Create preview
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'preview-image';
                        previewElement.appendChild(img);
                    }
                    reader.readAsDataURL(file);
                } else {
                    showError('Failed to upload image: ' + (response.error || 'Unknown error'));
                }
            });
        }
    }
}

// Upload file to server
function uploadFile(file, viewType, callback) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('view_type', viewType);
    
    fetch(API.upload, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        callback({ success: false, error: error.message });
    });
}

// Initialize measurement form
function initializeMeasurementForm() {
    // Standard size selection
    const sizeButtons = document.querySelectorAll('input[name="size"]');
    sizeButtons.forEach(button => {
        button.addEventListener('change', function() {
            // Disable custom measurements if standard size is selected
            const measurementInputs = document.querySelectorAll('.measurement-form input');
            measurementInputs.forEach(input => {
                input.disabled = this.checked;
            });
        });
    });
    
    // Measurement inputs
    const measurementInputs = document.querySelectorAll('.measurement-form input');
    measurementInputs.forEach(input => {
        input.addEventListener('change', function() {
            appState.measurements[this.id] = parseFloat(this.value);
        });
    });
}

// Initialize pattern generation
function initializePatternGeneration() {
    // Process images when moving to step 3
    document.querySelector('button[onclick="nextStep(2)"]').addEventListener('click', function(e) {
        // Prevent default navigation if not all required images are uploaded
        if (!appState.images.front) {
            e.preventDefault();
            showError('Please upload at least a front view image');
            return;
        }
        
        // Collect all uploaded images
        const images = [];
        if (appState.images.front) images.push(appState.images.front);
        if (appState.images.back) images.push(appState.images.back);
        if (appState.images.side) images.push(appState.images.side);
        images.push(...appState.images.details);
        
        // Process images
        processImages(images);
    });
    
    // Generate pattern when moving to step 4
    document.querySelector('button[onclick="nextStep(3)"]').addEventListener('click', function(e) {
        // Prevent default navigation if no session ID
        if (!appState.sessionId) {
            e.preventDefault();
            showError('Please complete the image processing step first');
            return;
        }
        
        // Collect measurements
        const measurements = {};
        const measurementInputs = document.querySelectorAll('.measurement-form input');
        measurementInputs.forEach(input => {
            if (!input.disabled && input.value) {
                measurements[input.id] = parseFloat(input.value);
            }
        });
        
        // Get selected size if any
        let size = null;
        const sizeButtons = document.querySelectorAll('input[name="size"]');
        sizeButtons.forEach(button => {
            if (button.checked) {
                size = button.id.replace('size-', '').toUpperCase();
            }
        });
        
        // Get seam allowance
        const seamAllowance = parseFloat(document.getElementById('seam-allowance').value) || 1.0;
        
        // Generate pattern
        generatePattern(appState.sessionId, measurements, size, seamAllowance);
    });
}

// Process uploaded images
function processImages(images) {
    // Show loading indicator
    showLoading('Processing images...');
    
    fetch(API.process, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ images: images })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Store session ID and measurements
            appState.sessionId = data.session_id;
            appState.measurements = data.measurements;
            
            // Update measurements form with detected values
            for (const [key, value] of Object.entries(data.measurements)) {
                const input = document.getElementById(key);
                if (input) {
                    input.value = value.toFixed(1);
                }
            }
            
            // Update 3D model preview
            update3DModelPreview(data.model_path);
            
            // Show success message
            showSuccess('Images processed successfully. 3D model generated.');
        } else {
            showError('Failed to process images: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error processing images:', error);
        showError('Error processing images: ' + error.message);
    });
}

// Generate pattern from 3D model
function generatePattern(sessionId, measurements, size, seamAllowance) {
    // Show loading indicator
    showLoading('Generating pattern...');
    
    fetch(API.generatePattern, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: sessionId,
            measurements: measurements,
            size: size,
            seam_allowance: seamAllowance
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Store pattern files
            appState.patternFiles = data.files;
            
            // Update pattern preview
            updatePatternPreview(data.files.svg);
            
            // Update layout preview
            updateLayoutPreview(data.files.layout);
            
            // Update export buttons
            updateExportButtons(data.files);
            
            // Show success message
            showSuccess('Pattern generated successfully.');
        } else {
            showError('Failed to generate pattern: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error generating pattern:', error);
        showError('Error generating pattern: ' + error.message);
    });
}

// Update 3D model preview
function update3DModelPreview(modelPath) {
    const container = document.getElementById('3d-model-container');
    container.innerHTML = '';
    
    // In a real implementation, this would use Three.js to render the 3D model
    // For this placeholder, we'll just show a message
    const message = document.createElement('div');
    message.className = 'd-flex justify-content-center align-items-center h-100';
    message.innerHTML = `
        <div class="text-center">
            <p>3D model generated successfully</p>
            <p class="text-muted">Model path: ${modelPath}</p>
        </div>
    `;
    container.appendChild(message);
}

// Update pattern preview
function updatePatternPreview(svgPath) {
    const container = document.getElementById('pattern-pieces-container');
    container.innerHTML = '';
    
    // Create an iframe to display the SVG
    const iframe = document.createElement('iframe');
    iframe.src = API.files + '/' + svgPath;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    container.appendChild(iframe);
}

// Update layout preview
function updateLayoutPreview(layoutPath) {
    const container = document.getElementById('layout-container');
    container.innerHTML = '';
    
    // Create an iframe to display the layout
    const iframe = document.createElement('iframe');
    iframe.src = API.files + '/' + layoutPath;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    container.appendChild(iframe);
}

// Initialize export buttons
function initializeExportButtons() {
    // PDF download
    document.querySelector('.export-option:nth-child(1) button').addEventListener('click', function() {
        if (appState.patternFiles && appState.patternFiles.pdf) {
            window.open(API.files + '/' + appState.patternFiles.pdf, '_blank');
        } else {
            showError('PDF file not available');
        }
    });
    
    // SVG download
    document.querySelector('.export-option:nth-child(2) button').addEventListener('click', function() {
        if (appState.patternFiles && appState.patternFiles.svg) {
            window.open(API.files + '/' + appState.patternFiles.svg, '_blank');
        } else {
            showError('SVG file not available');
        }
    });
    
    // DXF download
    document.querySelector('.export-option:nth-child(3) button').addEventListener('click', function() {
        if (appState.patternFiles && appState.patternFiles.dxf) {
            window.open(API.files + '/' + appState.patternFiles.dxf, '_blank');
        } else {
            showError('DXF file not available');
        }
    });
    
    // Layout download
    document.querySelector('.export-option:nth-child(4) button').addEventListener('click', function() {
        if (appState.patternFiles && appState.patternFiles.layout) {
            window.open(API.files + '/' + appState.patternFiles.layout, '_blank');
        } else {
            showError('Layout file not available');
        }
    });
    
    // Instructions download
    document.querySelector('.export-option:nth-child(5) button').addEventListener('click', function() {
        if (appState.patternFiles && appState.patternFiles.instructions) {
            window.open(API.files + '/' + appState.patternFiles.instructions, '_blank');
        } else {
            showError('Instructions file not available');
        }
    });
}

// Update export buttons with file paths
function updateExportButtons(files) {
    // Enable all buttons
    const buttons = document.querySelectorAll('.export-option button');
    buttons.forEach(button => {
        button.disabled = false;
    });
}

// Show error message
function showError(message) {
    alert('Error: ' + message);
}

// Show success message
function showSuccess(message) {
    alert('Success: ' + message);
}

// Show loading indicator
function showLoading(message) {
    // In a real implementation, this would show a loading spinner
    console.log('Loading: ' + message);
}

// Hide loading indicator
function hideLoading() {
    // In a real implementation, this would hide the loading spinner
    console.log('Loading complete');
}

// Navigation between steps
function nextStep(currentStep) {
    // Update progress bar
    const progressBar = document.querySelector('.progress-bar');
    progressBar.style.width = ((currentStep + 1) * 25) + '%';
    progressBar.setAttribute('aria-valuenow', ((currentStep + 1) * 25));
    
    // Hide current step and show next step
    const stepContainers = document.querySelectorAll('.step-container');
    stepContainers[currentStep - 1].style.display = 'none';
    stepContainers[currentStep].style.display = 'block';
    
    // Scroll to top
    window.scrollTo(0, 0);
}

function prevStep(currentStep) {
    // Update progress bar
    const progressBar = document.querySelector('.progress-bar');
    progressBar.style.width = ((currentStep - 1) * 25) + '%';
    progressBar.setAttribute('aria-valuenow', ((currentStep - 1) * 25));
    
    // Hide current step and show previous step
    const stepContainers = document.querySelectorAll('.step-container');
    stepContainers[currentStep - 1].style.display = 'none';
    stepContainers[currentStep - 2].style.display = 'block';
    
    // Scroll to top
    window.scrollTo(0, 0);
}

function finishProcess() {
    alert('Pattern generation complete! All files have been d
(Content truncated due to size limit. Use line ranges to read in chunks)