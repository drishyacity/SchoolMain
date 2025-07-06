/**
 * Simple Image Preview
 * Shows how an image will appear in different containers
 */
class SimpleImagePreview {
    constructor(options) {
        // Input elements
        this.fileInput = document.getElementById(options.fileInputId);
        this.positionTypeSelect = document.getElementById(options.positionTypeSelectId);
        
        // Preview elements
        this.previewContainer = document.getElementById('image-preview-container');
        this.squarePreview = document.getElementById('square-preview');
        this.circlePreview = document.getElementById('circle-preview');
        this.rectanglePreview = document.getElementById('rectangle-preview');
        
        // Initialize
        this.init();
    }
    
    init() {
        // File input change event
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        // Position type change event
        if (this.positionTypeSelect) {
            this.positionTypeSelect.addEventListener('change', () => this.updatePreviews());
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Only process image files
        if (!file.type.match('image.*')) {
            alert('Please select an image file');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (event) => {
            this.updatePreviews(event.target.result);
        };
        
        reader.readAsDataURL(file);
    }
    
    updatePreviews(imageSrc) {
        if (!imageSrc) return;
        
        // Show the preview container
        if (this.previewContainer) {
            this.previewContainer.style.display = 'block';
        }
        
        // Update each preview box
        this.updatePreviewBox(this.squarePreview, imageSrc);
        this.updatePreviewBox(this.circlePreview, imageSrc);
        this.updatePreviewBox(this.rectanglePreview, imageSrc);
        
        // Show/hide based on position type
        if (this.positionTypeSelect) {
            const positionType = this.positionTypeSelect.value;
            
            if (positionType === 'leadership') {
                // For leadership, show square and circle
                if (this.squarePreview) this.squarePreview.parentElement.style.display = 'block';
                if (this.circlePreview) this.circlePreview.parentElement.style.display = 'block';
                if (this.rectanglePreview) this.rectanglePreview.parentElement.style.display = 'none';
            } else {
                // For teaching, show rectangle
                if (this.squarePreview) this.squarePreview.parentElement.style.display = 'none';
                if (this.circlePreview) this.circlePreview.parentElement.style.display = 'none';
                if (this.rectanglePreview) this.rectanglePreview.parentElement.style.display = 'block';
            }
        }
    }
    
    updatePreviewBox(previewBox, imageSrc) {
        if (!previewBox) return;
        
        // Clear previous content
        previewBox.innerHTML = '';
        
        // Create image element
        const img = document.createElement('img');
        img.src = imageSrc;
        
        // Add to preview box
        previewBox.appendChild(img);
    }
}
