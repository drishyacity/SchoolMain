/**
 * Basic Image Cropper
 * A simple tool for adjusting images before upload
 */
function initBasicImageCropper() {
    // Get DOM elements
    const fileInput = document.getElementById('image-upload');
    const cropperContainer = document.getElementById('image-cropper-container');
    const mainPreview = document.getElementById('main-preview');
    const zoomSlider = document.getElementById('zoom-slider');
    const zoomValue = document.getElementById('zoom-value');
    const resetButton = document.getElementById('reset-button');
    const applyButton = document.getElementById('apply-button');
    const cropDataInput = document.getElementById('crop-data');
    
    // Preview elements
    const teacherPreview = document.getElementById('teacher-preview');
    const leadershipPreview = document.getElementById('leadership-preview');
    const circlePreview = document.getElementById('circle-preview');
    
    // State variables
    let currentImage = null;
    let zoom = 1;
    let posX = 0;
    let posY = 0;
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    
    // Check if all required elements exist
    if (!fileInput || !cropperContainer || !mainPreview) {
        console.error('Required elements not found');
        return;
    }
    
    // File input change event
    fileInput.addEventListener('change', function(e) {
        const file = this.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            // Clear previous image
            mainPreview.innerHTML = '';
            if (teacherPreview) teacherPreview.innerHTML = '';
            if (leadershipPreview) leadershipPreview.innerHTML = '';
            if (circlePreview) circlePreview.innerHTML = '';
            
            // Create new image
            currentImage = document.createElement('img');
            currentImage.src = e.target.result;
            currentImage.style.position = 'absolute';
            currentImage.style.left = '0';
            currentImage.style.top = '0';
            currentImage.style.width = '100%';
            currentImage.style.height = 'auto';
            currentImage.style.transformOrigin = 'top left';
            
            // Reset position and zoom
            zoom = 1;
            posX = 0;
            posY = 0;
            
            if (zoomSlider) zoomSlider.value = 1;
            if (zoomValue) zoomValue.textContent = '100%';
            
            // Add image to preview
            mainPreview.appendChild(currentImage);
            
            // Show cropper container
            cropperContainer.style.display = 'block';
            
            // Scroll to cropper
            setTimeout(() => {
                cropperContainer.scrollIntoView({ behavior: 'smooth' });
            }, 300);
            
            // Update preview
            updateImagePosition();
            updatePreviewBoxes();
            
            // Alert user
            alert('You can now adjust the image by zooming and repositioning. Click "Apply Changes" when done.');
        };
        
        reader.readAsDataURL(file);
    });
    
    // Zoom slider event
    if (zoomSlider) {
        zoomSlider.addEventListener('input', function() {
            zoom = parseFloat(this.value);
            if (zoomValue) zoomValue.textContent = Math.round(zoom * 100) + '%';
            updateImagePosition();
            updatePreviewBoxes();
        });
    }
    
    // Reset button event
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            zoom = 1;
            posX = 0;
            posY = 0;
            
            if (zoomSlider) zoomSlider.value = 1;
            if (zoomValue) zoomValue.textContent = '100%';
            
            updateImagePosition();
            updatePreviewBoxes();
        });
    }
    
    // Apply button event
    if (applyButton) {
        applyButton.addEventListener('click', function() {
            if (!currentImage) return;
            
            // Store crop data
            const cropData = {
                zoom: zoom,
                posX: posX,
                posY: posY,
                positionType: document.getElementById('position_type')?.value || 'teaching'
            };
            
            if (cropDataInput) {
                cropDataInput.value = JSON.stringify(cropData);
            }
            
            alert('Image adjustments applied! You can now save the form.');
        });
    }
    
    // Mouse events for dragging
    if (mainPreview) {
        mainPreview.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', endDrag);
        
        // Touch events for mobile
        mainPreview.addEventListener('touchstart', startDrag);
        document.addEventListener('touchmove', drag);
        document.addEventListener('touchend', endDrag);
    }
    
    // Start drag
    function startDrag(e) {
        if (!currentImage) return;
        
        isDragging = true;
        
        // Get start position
        if (e.type === 'mousedown') {
            startX = e.clientX;
            startY = e.clientY;
        } else if (e.type === 'touchstart') {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }
        
        e.preventDefault();
    }
    
    // Drag
    function drag(e) {
        if (!isDragging || !currentImage) return;
        
        let currentX, currentY;
        
        if (e.type === 'mousemove') {
            currentX = e.clientX;
            currentY = e.clientY;
        } else if (e.type === 'touchmove') {
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        }
        
        // Calculate the distance moved
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        
        // Update position
        posX += deltaX;
        posY += deltaY;
        
        // Update start position for next move
        startX = currentX;
        startY = currentY;
        
        // Update image position
        updateImagePosition();
        updatePreviewBoxes();
        
        e.preventDefault();
    }
    
    // End drag
    function endDrag() {
        isDragging = false;
    }
    
    // Update image position
    function updateImagePosition() {
        if (!currentImage) return;
        
        currentImage.style.transform = `translate(${posX}px, ${posY}px) scale(${zoom})`;
    }
    
    // Update preview boxes
    function updatePreviewBoxes() {
        if (!currentImage) return;
        
        // Update teacher preview
        if (teacherPreview) {
            updatePreviewBox(teacherPreview);
        }
        
        // Update leadership preview
        if (leadershipPreview) {
            updatePreviewBox(leadershipPreview);
        }
        
        // Update circle preview
        if (circlePreview) {
            updatePreviewBox(circlePreview);
        }
    }
    
    // Update a single preview box
    function updatePreviewBox(previewBox) {
        // Clear previous content
        previewBox.innerHTML = '';
        
        // Create a clone of the image
        const imgClone = document.createElement('img');
        imgClone.src = currentImage.src;
        imgClone.style.width = '100%';
        imgClone.style.height = '100%';
        imgClone.style.objectFit = 'cover';
        imgClone.style.objectPosition = 'center top';
        
        // Add to preview box
        previewBox.appendChild(imgClone);
    }
    
    // Update preview visibility based on position type
    document.getElementById('position_type')?.addEventListener('change', function() {
        const positionType = this.value;
        
        // Get preview containers
        const leadershipContainer = document.querySelector('.leadership-preview-container');
        const circleContainer = document.querySelector('.circle-preview-container');
        const teacherContainer = document.querySelector('.teacher-preview-container');
        
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
    });
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initBasicImageCropper);
