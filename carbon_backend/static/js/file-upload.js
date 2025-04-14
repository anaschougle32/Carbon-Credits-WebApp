/**
 * Enhanced File Upload Component
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
});

function initializeFileUpload() {
    const fileUploadModal = document.getElementById('file-upload-modal');
    const fileDropArea = document.getElementById('file-drop-area');
    const browseFilesBtn = document.getElementById('browse-files-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const fileInput = document.getElementById('file-input');
    const uploadsList = document.getElementById('uploads-list');
    
    // Show modal when trigger is clicked
    document.querySelectorAll('.file-upload-trigger').forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            fileUploadModal.classList.remove('hidden');
            document.body.classList.add('modal-open');
        });
    });
    
    // Close modal functionality
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            fileUploadModal.classList.add('hidden');
            document.body.classList.remove('modal-open');
        });
    }
    
    // Close modal if clicked outside content area
    fileUploadModal?.addEventListener('click', function(e) {
        if (e.target === fileUploadModal) {
            fileUploadModal.classList.add('hidden');
            document.body.classList.remove('modal-open');
        }
    });
    
    // Trigger file input when browse button is clicked
    if (browseFilesBtn && fileInput) {
        browseFilesBtn.addEventListener('click', function() {
            fileInput.click();
        });
    }
    
    // Handle file selection via input
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
    }
    
    // Setup drag and drop area
    if (fileDropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, unhighlight, false);
        });
        
        fileDropArea.addEventListener('drop', handleDrop, false);
    }
    
    // Prevent default behaviors for drag events
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area when file is dragged over
    function highlight() {
        fileDropArea.classList.add('border-blue-500');
        fileDropArea.classList.remove('border-gray-300');
    }
    
    // Remove highlight when file is no longer over drop area
    function unhighlight() {
        fileDropArea.classList.remove('border-blue-500');
        fileDropArea.classList.add('border-gray-300');
    }
    
    // Handle file drop
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    // Process the dropped or selected files
    function handleFiles(files) {
        if (!files.length) return;
        
        Array.from(files).forEach(file => {
            // Validate file type
            const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'image/svg+xml'];
            if (!validTypes.includes(file.type)) {
                showFileError(file.name, 'File type not supported');
                return;
            }
            
            // Validate file size (max 20MB)
            if (file.size > 20 * 1024 * 1024) {
                showFileError(file.name, 'File size exceeds the limit');
                return;
            }
            
            // Add file to the list
            addFileToList(file);
            
            // Upload the file (simulated)
            uploadFile(file);
        });
    }
    
    // Show error for invalid files
    function showFileError(fileName, errorMessage) {
        if (!uploadsList) return;
        
        const fileItem = document.createElement('div');
        fileItem.className = 'flex items-center justify-between p-2 mb-2';
        fileItem.innerHTML = `
            <div class="flex items-center">
                <div class="mr-3 text-red-500">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-700">${fileName}</p>
                    <p class="text-xs text-red-500">${errorMessage}</p>
                </div>
            </div>
        `;
        
        uploadsList.appendChild(fileItem);
        
        // Remove error message after 5 seconds
        setTimeout(() => {
            if (fileItem.parentNode) {
                fileItem.remove();
            }
        }, 5000);
    }
    
    // Add file to the uploads list with progress bar
    function addFileToList(file) {
        if (!uploadsList) return;
        
        const fileId = `file-${Date.now()}`;
        const fileItem = document.createElement('div');
        fileItem.id = fileId;
        fileItem.className = 'flex items-center justify-between p-2 mb-2';
        
        // Determine file icon and class by type
        let statusIndicator, progressBarColor;
        
        // Default to uploading state
        statusIndicator = `
            <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        `;
        progressBarColor = 'bg-blue-500';
        
        fileItem.innerHTML = `
            <div class="flex items-center flex-grow">
                <div class="mr-3">
                    ${statusIndicator}
                </div>
                <div class="w-full">
                    <div class="flex justify-between">
                        <p class="text-sm font-medium text-gray-700">${file.name}</p>
                        <p class="text-xs text-gray-500">${formatFileSize(file.size)}</p>
                    </div>
                    <div class="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div class="progress-bar ${progressBarColor} h-2 rounded-full" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        
        uploadsList.appendChild(fileItem);
        return fileId;
    }
    
    // Format file size in a human-readable format
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    // Simulate file upload with progress
    function uploadFile(file) {
        const fileId = `file-${Date.now()}`;
        const fileItem = document.getElementById(fileId);
        if (!fileItem) return;
        
        const progressBar = fileItem.querySelector('.progress-bar');
        const statusIcon = fileItem.querySelector('.flex.items-center .mr-3');
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            
            if (progress >= 100) {
                clearInterval(interval);
                
                // Update status to completed
                if (statusIcon) {
                    statusIcon.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                    `;
                }
                
                if (progressBar) {
                    progressBar.classList.remove('bg-blue-500');
                    progressBar.classList.add('bg-green-500');
                }
                
                // Update the hidden input field
                const proofUploadInput = document.getElementById('proof-upload');
                if (proofUploadInput) {
                    // Create a reader to convert the file to base64
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        // Set the base64 data as the hidden input value
                        proofUploadInput.value = e.target.result;
                        
                        // Also add the file to the preview list
                        updateFilePreviewList(file, e.target.result);
                    };
                    reader.readAsDataURL(file);
                }
                
                // Close the modal
                fileUploadModal.classList.add('hidden');
                document.body.classList.remove('modal-open');
                
                console.log(`File "${file.name}" uploaded successfully`);
            }
        }, 100);
        
        // Simulate random upload failure (for demonstration)
        if (Math.random() < 0.1) { // 10% chance of failure
            setTimeout(() => {
                clearInterval(interval);
                
                // Update status to error
                if (statusIcon) {
                    statusIcon.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                        </svg>
                    `;
                }
                
                if (progressBar) {
                    progressBar.classList.remove('bg-blue-500');
                    progressBar.classList.add('bg-red-500');
                }
                
                console.log(`Upload failed for "${file.name}"`);
            }, 1500);
        }
    }
    
    // Update the file preview list in the trip log form
    function updateFilePreviewList(file, dataUrl) {
        const previewList = document.getElementById('file-preview-list');
        if (!previewList) return;
        
        // Clear existing previews
        previewList.innerHTML = '';
        
        // Create preview item
        const previewItem = document.createElement('div');
        previewItem.className = 'flex items-center justify-between p-3 border border-gray-200 rounded-lg';
        
        // Determine icon based on file type
        let icon = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
            </svg>
        `;
        
        // For images, show a thumbnail
        if (file.type.startsWith('image/')) {
            icon = `<img src="${dataUrl}" class="h-10 w-10 object-cover rounded" alt="Preview">`;
        }
        
        previewItem.innerHTML = `
            <div class="flex items-center">
                <div class="mr-3">
                    ${icon}
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-700">${file.name}</p>
                    <p class="text-xs text-gray-500">${formatFileSize(file.size)}</p>
                </div>
            </div>
            <button type="button" class="text-gray-400 hover:text-red-500" id="remove-preview-file">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            </button>
        `;
        
        previewList.appendChild(previewItem);
        
        // Add remove functionality
        const removeBtn = document.getElementById('remove-preview-file');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                // Clear the input field
                const proofUploadInput = document.getElementById('proof-upload');
                if (proofUploadInput) {
                    proofUploadInput.value = '';
                }
                
                // Remove the preview
                previewList.innerHTML = '';
                
                // Show notification if addNotification is defined
                if (typeof addNotification === 'function') {
                    addNotification('File removed', 'info');
                }
            });
        }
    }
} 