// Admin panel JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar on mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // Initialize CKEditor for rich text areas if present
    if (typeof ClassicEditor !== 'undefined') {
        document.querySelectorAll('.ckeditor').forEach(element => {
            ClassicEditor
                .create(element)
                .catch(error => {
                    console.error(error);
                });
        });
    }
    
    // Preview image uploads
    const imageInputs = document.querySelectorAll('.image-upload');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const preview = document.getElementById(`${this.id}-preview`);
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Confirmation for multiple delete in gallery
    const deleteSelectedBtn = document.getElementById('delete-selected');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', function(e) {
            const checkboxes = document.querySelectorAll('input[name="selected_images"]:checked');
            if (checkboxes.length === 0) {
                e.preventDefault();
                alert('Please select at least one image to delete.');
            } else if (!confirm(`Are you sure you want to delete ${checkboxes.length} selected image(s)? This action cannot be undone.`)) {
                e.preventDefault();
            }
        });
    }
    
    // Select all functionality for checkboxes
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input[name="selected_images"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
    
    // Multi-file upload preview
    const multiImageInput = document.getElementById('images');
    if (multiImageInput) {
        multiImageInput.addEventListener('change', function() {
            const previewContainer = document.getElementById('image-previews');
            previewContainer.innerHTML = '';
            
            if (this.files) {
                for (let i = 0; i < this.files.length; i++) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewWrapper = document.createElement('div');
                        previewWrapper.className = 'preview-item';
                        
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'img-thumbnail';
                        img.style.maxHeight = '150px';
                        img.style.marginRight = '10px';
                        img.style.marginBottom = '10px';
                        
                        previewWrapper.appendChild(img);
                        previewContainer.appendChild(previewWrapper);
                    }
                    reader.readAsDataURL(this.files[i]);
                }
            }
        });
    }
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.classList.add('fade');
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
    });
});
