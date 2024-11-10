// Improved File Upload Handling
        document.getElementById('dataFile').addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                document.querySelector('.upload-container p').textContent = `Selected file: ${fileName}`;
            }
        });

        // Checkbox Handling
        document.querySelectorAll('.preprocessing-option').forEach(option => {
            const checkbox = option.querySelector('input[type="checkbox"]');

            option.addEventListener('click', function(e) {
                if (e.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });

            checkbox.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });

        // Form Submission Handler
        document.querySelector('.btn-submit').addEventListener('click', function(e) {
            e.preventDefault();

            const selectedOptions = {
                removeDuplicates: document.getElementById('removeDuplicates').checked,
                cleanText: document.getElementById('cleanText').checked,
                removeStopwords: document.getElementById('removeStopwords').checked,
                inputMethod: document.getElementById('dataFile').files.length > 0 ? 'file' : 'text',
                data: document.getElementById('dataFile').files.length > 0
                    ? document.getElementById('dataFile').files[0].name
                    : document.querySelector('textarea').value
            };

            console.log('Form submission:', selectedOptions);
            // Add your form submission logic here
        });
        // File preview functionality
const uploadContainer = document.querySelector('.upload-container');
const dataFileInput = document.getElementById('dataFile');
const rawDataInput = document.querySelector('textarea');
const originalUploadText = uploadContainer.querySelector('p').textContent;

// Function to reset file upload
function resetFileUpload() {
    dataFileInput.value = '';
    uploadContainer.querySelector('p').textContent = originalUploadText;
    uploadContainer.classList.remove('disabled');
    uploadContainer.style.cursor = 'pointer';
    dataFileInput.disabled = false;

    // Create or update selected file div
    let selectedFileDiv = document.querySelector('.selected-file');
    if (selectedFileDiv) {
        selectedFileDiv.style.display = 'none';
    }
}

// Function to reset text area
function resetTextArea() {
    rawDataInput.value = '';
    rawDataInput.disabled = false;
}

// Function to show selected file
function showSelectedFile(fileName) {
    // Create or get selected file div
    let selectedFileDiv = document.querySelector('.selected-file');
    if (!selectedFileDiv) {
        selectedFileDiv = document.createElement('div');
        selectedFileDiv.className = 'selected-file';
        selectedFileDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-between p-2 mt-3 bg-light rounded">
                <span class="selected-file-name"></span>
                <button type="button" class="btn btn-sm btn-danger remove-file">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        uploadContainer.insertAdjacentElement('afterend', selectedFileDiv);
    }

    // Update file name and show the div
    selectedFileDiv.querySelector('.selected-file-name').textContent = `Selected file: ${fileName}`;
    selectedFileDiv.style.display = 'block';

    // Add click handler to remove button
    selectedFileDiv.querySelector('.remove-file').onclick = function(e) {
        e.stopPropagation();
        resetFileUpload();
        rawDataInput.disabled = false;
    };
}

// Handle file selection
dataFileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        // Disable text area
        rawDataInput.value = '';
        rawDataInput.disabled = true;

        // Update upload container
        uploadContainer.classList.add('disabled');
        uploadContainer.style.cursor = 'not-allowed';
        uploadContainer.querySelector('p').textContent = 'File selected';

        // Show selected file
        showSelectedFile(file.name);
    }
});

// Handle text area input
rawDataInput.addEventListener('input', function(e) {
    if (e.target.value) {
        // Disable file upload
        uploadContainer.classList.add('disabled');
        uploadContainer.style.cursor = 'not-allowed';
        dataFileInput.disabled = true;
        resetFileUpload();
    } else {
        // Re-enable file upload
        uploadContainer.classList.remove('disabled');
        uploadContainer.style.cursor = 'pointer';
        dataFileInput.disabled = false;
    }
});

// Checkbox selection handling
document.querySelectorAll('.preprocessing-option').forEach(option => {
    const checkbox = option.querySelector('input[type="checkbox"]');

    option.addEventListener('click', function(e) {
        if (e.target !== checkbox) {
            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change'));
        }
    });

    checkbox.addEventListener('click', function(e) {
        e.stopPropagation();
    });
});
