// Admin panel JavaScript functionality

// Global variable to store CKEditor instances
window.CKEDITOR_INSTANCES = {};

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
                .then(editor => {
                    console.log('CKEditor initialized for', element.id);

                    // Store the editor instance globally
                    window.CKEDITOR_INSTANCES[element.id] = editor;

                    // Also store it on the element for backward compatibility
                    element.ckeditorInstance = editor;
                })
                .catch(error => {
                    console.error('CKEditor initialization error:', error);
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

    // Handle form submissions - ensure CKEditor content is saved
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Add a submit event listener to each form
        form.addEventListener('submit', function(e) {
            console.log('Form submission handler triggered');

            // Find all CKEditor instances in this form
            const editors = form.querySelectorAll('.ckeditor');

            // Update each textarea with its CKEditor content
            editors.forEach(element => {
                const editor = window.CKEDITOR_INSTANCES[element.id];
                if (editor) {
                    // Get the data from CKEditor
                    const data = editor.getData();

                    // Update the textarea value
                    element.value = data;

                    console.log(`Updated ${element.id} with data:`, data);
                }
            });
        });
    });

    // Add click handlers to all submit buttons as a backup
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form) {
                const editors = form.querySelectorAll('.ckeditor');
                editors.forEach(element => {
                    const editor = window.CKEDITOR_INSTANCES[element.id];
                    if (editor) {
                        element.value = editor.getData();
                        console.log(`Button click: Updated ${element.id}`);
                    }
                });
            }
        });
    });
});
