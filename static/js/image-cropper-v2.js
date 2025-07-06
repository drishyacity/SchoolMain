/**
 * Image Cropper V2 for Teacher Photos
 * Allows zooming and repositioning of images before upload
 */
class ImageCropperV2 {
    constructor(options) {
        // Get DOM elements
        this.fileInput = document.getElementById(options.fileInputId);
        this.container = document.getElementById(options.containerId);
        this.preview = document.getElementById(options.previewId);
        this.zoomSlider = document.getElementById(options.zoomSliderId);
        this.zoomValue = document.getElementById(options.zoomValueId);
        this.resetButton = document.getElementById(options.resetButtonId);
        this.applyButton = document.getElementById(options.applyButtonId);
        this.dataInput = document.getElementById(options.dataInputId);
        this.positionTypeSelect = document.getElementById(options.positionTypeSelectId);

        // Preview containers
        this.leadershipPreview = document.getElementById('leadership-preview');
        this.circlePreview = document.getElementById('circle-preview');
        this.teacherPreview = document.getElementById('teacher-preview');

        // State variables
        this.image = null;
        this.originalFile = null;
        this.zoom = 1;
        this.posX = 0;
        this.posY = 0;
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;

        // Initialize
        this.init();
    }

    init() {
        console.log('Initializing ImageCropperV2');

        // Check if all required elements exist
        if (!this.fileInput) {
            console.error('File input element not found');
            return;
        }

        if (!this.container) {
            console.error('Container element not found');
            return;
        }

        if (!this.preview) {
            console.error('Preview element not found');
            return;
        }

        // File input change event
        this.fileInput.addEventListener('change', (e) => {
            console.log('File input change event triggered');
            this.handleFileSelect(e);
        });

        // Zoom slider event
        if (this.zoomSlider) {
            this.zoomSlider.addEventListener('input', () => this.handleZoom());
        }

        // Reset button event
        if (this.resetButton) {
            this.resetButton.addEventListener('click', () => this.resetCropper());
        }

        // Apply button event
        if (this.applyButton) {
            this.applyButton.addEventListener('click', () => this.applyCrop());
        }

        // Mouse events for dragging
        if (this.preview) {
            this.preview.addEventListener('mousedown', (e) => this.startDrag(e));
            document.addEventListener('mousemove', (e) => this.drag(e));
            document.addEventListener('mouseup', () => this.endDrag());

            // Touch events for mobile
            this.preview.addEventListener('touchstart', (e) => this.startDrag(e));
            document.addEventListener('touchmove', (e) => this.drag(e));
            document.addEventListener('touchend', () => this.endDrag());
        }

        // Position type change event
        if (this.positionTypeSelect) {
            this.positionTypeSelect.addEventListener('change', () => this.updatePreviewVisibility());
            // Initial update
            this.updatePreviewVisibility();
        }

        console.log('ImageCropperV2 initialized successfully');
    }

    updatePreviewVisibility() {
        if (!this.positionTypeSelect) return;

        const positionType = this.positionTypeSelect.value;
        console.log('Position type changed to:', positionType);

        // Get all preview containers
        const leadershipContainer = document.querySelector('.leadership-preview-container');
        const circleContainer = document.querySelector('.circle-preview-container');
        const teacherContainer = document.querySelector('.teacher-preview-container');

        // Show/hide appropriate preview boxes
        if (positionType === 'leadership') {
            // For leadership, show square and circle
            if (leadershipContainer) leadershipContainer.style.display = 'block';
            if (circleContainer) circleContainer.style.display = 'block';
            if (teacherContainer) teacherContainer.style.display = 'none';
        } else {
            // For teaching, show rectangle
            if (leadershipContainer) leadershipContainer.style.display = 'none';
            if (circleContainer) circleContainer.style.display = 'none';
            if (teacherContainer) teacherContainer.style.display = 'block';
        }

        console.log('Preview visibility updated for position type:', positionType);
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) {
            console.log('No file selected');
            return;
        }

        console.log('File selected:', file.name);
        this.originalFile = file;

        const reader = new FileReader();
        reader.onload = (event) => {
            console.log('File loaded');

            // Create new image element
            if (this.image) {
                this.preview.removeChild(this.image);
            }

            this.image = document.createElement('img');
            this.image.src = event.target.result;

            this.image.onload = () => {
                console.log('Image loaded, dimensions:', this.image.naturalWidth, 'x', this.image.naturalHeight);

                // Reset cropper state
                this.zoom = 1;
                this.posX = 0;
                this.posY = 0;

                if (this.zoomSlider) {
                    this.zoomSlider.value = 1;
                }

                if (this.zoomValue) {
                    this.zoomValue.textContent = '100%';
                }

                // Set image styles
                this.image.style.position = 'absolute';
                this.image.style.left = '0';
                this.image.style.top = '0';
                this.image.style.width = '100%';
                this.image.style.height = 'auto';
                this.image.style.transformOrigin = 'top left';

                // Center the image
                this.centerImage();

                // Add image to preview
                this.preview.appendChild(this.image);

                // Show cropper container
                this.container.style.display = 'block';

                // Update image position
                this.updateImagePosition();

                // Update preview boxes
                this.updatePreviewBoxes();

                // Update preview visibility based on position type
                this.updatePreviewVisibility();

                // Alert the user that they can adjust the image
                alert('You can now adjust the image by zooming and repositioning. Click "Apply Changes" when done.');
            };
        };

        reader.readAsDataURL(file);
    }

    centerImage() {
        if (!this.image) return;

        const previewRect = this.preview.getBoundingClientRect();
        const imageWidth = this.image.naturalWidth;
        const imageHeight = this.image.naturalHeight;

        // Center the image
        this.posX = (previewRect.width - imageWidth) / 2;
        this.posY = (previewRect.height - imageHeight) / 2;

        console.log('Image centered at:', this.posX, this.posY);
    }

    handleZoom() {
        if (!this.zoomSlider || !this.zoomValue) return;

        this.zoom = parseFloat(this.zoomSlider.value);
        this.zoomValue.textContent = `${Math.round(this.zoom * 100)}%`;

        console.log('Zoom changed to:', this.zoom);
        this.updateImagePosition();
    }

    startDrag(e) {
        if (!this.image) return;

        this.isDragging = true;

        // Get start position
        if (e.type === 'mousedown') {
            this.startX = e.clientX;
            this.startY = e.clientY;
        } else if (e.type === 'touchstart') {
            this.startX = e.touches[0].clientX;
            this.startY = e.touches[0].clientY;
        }

        e.preventDefault();
    }

    drag(e) {
        if (!this.isDragging || !this.image) return;

        let currentX, currentY;

        if (e.type === 'mousemove') {
            currentX = e.clientX;
            currentY = e.clientY;
        } else if (e.type === 'touchmove') {
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        }

        // Calculate the distance moved
        const deltaX = currentX - this.startX;
        const deltaY = currentY - this.startY;

        // Update position
        this.posX += deltaX;
        this.posY += deltaY;

        // Update start position for next move
        this.startX = currentX;
        this.startY = currentY;

        // Update image position
        this.updateImagePosition();

        e.preventDefault();
    }

    endDrag() {
        this.isDragging = false;
    }

    updateImagePosition() {
        if (!this.image) return;

        console.log('Updating image position:', this.posX, this.posY, this.zoom);

        // Update main preview
        this.image.style.position = 'absolute';
        this.image.style.left = '0';
        this.image.style.top = '0';
        this.image.style.width = '100%';
        this.image.style.height = 'auto';
        this.image.style.transform = `translate(${this.posX}px, ${this.posY}px) scale(${this.zoom})`;
        this.image.style.transformOrigin = 'top left';

        // Update preview boxes
        this.updatePreviewBoxes();

        // Update position type visibility
        this.updatePreviewVisibility();
    }

    updatePreviewBoxes() {
        if (!this.image) return;

        this.updatePreviewBox(this.leadershipPreview);
        this.updatePreviewBox(this.circlePreview);
        this.updatePreviewBox(this.teacherPreview);
    }

    updatePreviewBox(previewBox) {
        if (!previewBox || !this.image) return;

        console.log('Updating preview box:', previewBox.id);

        // Clear previous content
        previewBox.innerHTML = '';

        // Create a clone of the image
        const imgClone = document.createElement('img');
        imgClone.src = this.image.src;

        // Set basic styles for the preview image
        imgClone.style.width = '100%';
        imgClone.style.height = '100%';
        imgClone.style.objectFit = 'cover';
        imgClone.style.objectPosition = 'center top';

        // Add to preview box
        previewBox.appendChild(imgClone);

        console.log('Preview box updated:', previewBox.id);
    }

    resetCropper() {
        if (!this.image) return;

        this.zoom = 1;

        if (this.zoomSlider) {
            this.zoomSlider.value = 1;
        }

        if (this.zoomValue) {
            this.zoomValue.textContent = '100%';
        }

        this.centerImage();
        this.updateImagePosition();

        console.log('Cropper reset');
    }

    applyCrop() {
        if (!this.image || !this.originalFile || !this.dataInput) return;

        // Get the preview dimensions
        const previewRect = this.preview.getBoundingClientRect();

        // Store crop data in hidden input
        const cropData = {
            zoom: this.zoom,
            posX: this.posX,
            posY: this.posY,
            previewWidth: previewRect.width,
            previewHeight: previewRect.height,
            positionType: this.positionTypeSelect ? this.positionTypeSelect.value : 'teaching'
        };

        this.dataInput.value = JSON.stringify(cropData);

        console.log('Crop data applied:', cropData);

        // Hide the cropper container
        this.container.style.display = 'none';
    }
}
