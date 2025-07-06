/**
 * Image Cropper for Teacher Photos
 * Allows zooming and repositioning of images before upload
 */
class ImageCropper {
    constructor(options) {
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

        this.image = null;
        this.originalFile = null;
        this.zoom = 1;
        this.posX = 0;
        this.posY = 0;
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.aspectRatio = options.aspectRatio || null;

        this.init();
    }

    init() {
        // File input change event
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Zoom slider event
        this.zoomSlider.addEventListener('input', () => this.handleZoom());

        // Reset button event
        this.resetButton.addEventListener('click', () => this.resetCropper());

        // Apply button event
        this.applyButton.addEventListener('click', () => this.applyCrop());

        // Mouse events for dragging
        this.preview.addEventListener('mousedown', (e) => this.startDrag(e));
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.endDrag());

        // Touch events for mobile
        this.preview.addEventListener('touchstart', (e) => this.startDrag(e));
        document.addEventListener('touchmove', (e) => this.drag(e));
        document.addEventListener('touchend', () => this.endDrag());

        // Position type change event
        if (this.positionTypeSelect) {
            this.positionTypeSelect.addEventListener('change', () => this.updateAspectRatio());
            // Initial update
            this.updateAspectRatio();
        }
    }

    updateAspectRatio() {
        if (!this.positionTypeSelect) return;

        const positionType = this.positionTypeSelect.value;

        // Remove existing classes
        this.preview.classList.remove('leadership', 'teaching');

        // Add appropriate class based on position type
        if (positionType === 'leadership') {
            this.preview.classList.add('leadership');
            this.aspectRatio = 1; // 1:1 for leadership

            // Show/hide appropriate preview boxes
            if (this.leadershipPreview) this.leadershipPreview.parentElement.style.display = 'block';
            if (this.circlePreview) this.circlePreview.parentElement.style.display = 'block';
            if (this.teacherPreview) this.teacherPreview.parentElement.style.display = 'none';
        } else {
            this.preview.classList.add('teaching');
            this.aspectRatio = 4/3; // 4:3 for teaching staff

            // Show/hide appropriate preview boxes
            if (this.leadershipPreview) this.leadershipPreview.parentElement.style.display = 'none';
            if (this.circlePreview) this.circlePreview.parentElement.style.display = 'none';
            if (this.teacherPreview) this.teacherPreview.parentElement.style.display = 'block';
        }

        // If an image is already loaded, recenter it
        if (this.image) {
            this.centerImage();
            this.updateImagePosition();
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        this.originalFile = file;

        const reader = new FileReader();
        reader.onload = (event) => {
            // Create new image element
            if (this.image) {
                this.preview.removeChild(this.image);
            }

            this.image = document.createElement('img');
            this.image.src = event.target.result;

            this.image.onload = () => {
                // Reset cropper state
                this.zoom = 1;
                this.posX = 0;
                this.posY = 0;
                this.zoomSlider.value = 1;
                this.zoomValue.textContent = '100%';

                // Calculate initial position to center the image
                this.centerImage();

                // Add image to preview
                this.preview.appendChild(this.image);

                // Show cropper container
                this.container.style.display = 'block';

                // Update image position (this will also update preview boxes)
                this.updateImagePosition();
            };
        };

        reader.readAsDataURL(file);
    }

    centerImage() {
        const previewRect = this.preview.getBoundingClientRect();
        const imageWidth = this.image.naturalWidth;
        const imageHeight = this.image.naturalHeight;

        // Calculate scaling to fit the preview
        const scaleX = previewRect.width / imageWidth;
        const scaleY = previewRect.height / imageHeight;

        // Use the appropriate scale based on aspect ratio
        let scale;
        if (this.aspectRatio) {
            // For fixed aspect ratio, we want to fill the preview area completely
            scale = Math.max(scaleX, scaleY);

            // Adjust zoom to ensure the image fills the container
            const imageAspect = imageWidth / imageHeight;
            if (imageAspect > this.aspectRatio) {
                // Image is wider than container aspect ratio
                this.zoom = previewRect.height / (imageHeight * scale);
            } else {
                // Image is taller than container aspect ratio
                this.zoom = previewRect.width / (imageWidth * scale);
            }

            // Update zoom slider
            this.zoomSlider.value = this.zoom;
            this.zoomValue.textContent = `${Math.round(this.zoom * 100)}%`;
        } else {
            // For free-form cropping, just fit the image
            scale = Math.min(scaleX, scaleY);
        }

        // Center the image
        this.posX = (previewRect.width - imageWidth * scale * this.zoom) / 2;
        this.posY = (previewRect.height - imageHeight * scale * this.zoom) / 2;
    }

    handleZoom() {
        this.zoom = parseFloat(this.zoomSlider.value);
        this.zoomValue.textContent = `${Math.round(this.zoom * 100)}%`;
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

        // Update main preview
        this.image.style.transform = `translate(${this.posX}px, ${this.posY}px) scale(${this.zoom})`;

        // Update preview boxes if they exist
        this.updatePreviewBoxes();
    }

    updatePreviewBoxes() {
        if (!this.image) return;

        // Create clones of the image for each preview box
        this.updatePreviewBox(this.leadershipPreview, 1);  // Square aspect ratio
        this.updatePreviewBox(this.circlePreview, 1);      // Circle (also 1:1)
        this.updatePreviewBox(this.teacherPreview, 4/3);   // 4:3 aspect ratio
    }

    updatePreviewBox(previewBox, aspectRatio) {
        if (!previewBox || !this.image) return;

        // Clear previous preview
        previewBox.innerHTML = '';

        // Create a clone of the image
        const imgClone = document.createElement('img');
        imgClone.src = this.image.src;
        imgClone.style.width = '100%';
        imgClone.style.height = '100%';
        imgClone.style.objectFit = 'cover';
        imgClone.style.objectPosition = 'center top';

        // Calculate position based on current zoom and position
        const previewRect = previewBox.getBoundingClientRect();
        const mainPreviewRect = this.preview.getBoundingClientRect();

        // Calculate the scale factor between main preview and this preview box
        const scaleFactorX = previewRect.width / mainPreviewRect.width;
        const scaleFactorY = previewRect.height / mainPreviewRect.height;

        // Apply the same transform but adjusted for the preview box size
        const scaledPosX = this.posX * scaleFactorX;
        const scaledPosY = this.posY * scaleFactorY;

        imgClone.style.transform = `translate(${scaledPosX}px, ${scaledPosY}px) scale(${this.zoom})`;

        // Add to preview box
        previewBox.appendChild(imgClone);
    }

    resetCropper() {
        if (!this.image) return;

        this.zoom = 1;
        this.zoomSlider.value = 1;
        this.zoomValue.textContent = '100%';

        this.centerImage();
        this.updateImagePosition();
    }

    applyCrop() {
        if (!this.image || !this.originalFile) return;

        // Get the preview dimensions
        const previewRect = this.preview.getBoundingClientRect();

        // Store crop data in hidden input
        const cropData = {
            zoom: this.zoom,
            posX: this.posX,
            posY: this.posY,
            aspectRatio: this.aspectRatio,
            previewWidth: previewRect.width,
            previewHeight: previewRect.height,
            positionType: this.positionTypeSelect ? this.positionTypeSelect.value : 'teaching'
        };

        this.dataInput.value = JSON.stringify(cropData);

        // Hide the cropper container
        this.container.style.display = 'none';
    }
}
