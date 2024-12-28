// Show content function
function showContent(contentId) {
    document.querySelectorAll('.content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(contentId).classList.add('active');
}

// Initialize the first content section
document.getElementById('text-labelling').classList.add('active');

// Text file upload handling
const textFile = document.getElementById('textFile');
const textInput = document.getElementById('textInput');
const selectedFile = document.getElementById('selectedFile');
const fileName = document.getElementById('fileName');
const fileInputMethod = document.getElementById('fileInputMethod');
const textInputMethod = document.getElementById('textInputMethod');
const uploadContainer = document.querySelector('.upload-container');

// Image upload handling
const imageFile = document.getElementById('imageFile');
const imageUploadContainer = document.querySelector('#picture-labelling .upload-container');
let imageCountDisplay = document.createElement('div');
imageCountDisplay.className = 'selected-images-count mt-3';
imageUploadContainer.insertAdjacentElement('afterend', imageCountDisplay);

function updateImageCount(files) {
    if (files.length > 0) {
        imageCountDisplay.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-images me-2"></i>
                ${files.length} image${files.length > 1 ? 's' : ''} selected
            </div>`;
    } else {
        imageCountDisplay.innerHTML = `
            <div class="alert alert-secondary">
                <i class="fas fa-image me-2"></i>
                No files chosen
            </div>`;
    }
}

// Initialize with "No files chosen" message
updateImageCount([]);

function disableTextInput() {
    textInput.value = '';
    textInput.disabled = true;
    textInputMethod.classList.remove('active');
    fileInputMethod.classList.add('active');
    uploadContainer.classList.add('disabled');
}

function disableFileInput() {
    textFile.value = '';
    selectedFile.classList.remove('active');
    fileName.textContent = '';
    fileInputMethod.classList.remove('active');
    textInputMethod.classList.add('active');
    uploadContainer.classList.add('disabled');
}

function enableAllInputs() {
    textInput.disabled = false;
    fileInputMethod.classList.remove('active');
    textInputMethod.classList.remove('active');
    uploadContainer.classList.remove('disabled');
}

// Text file event listeners
textFile.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileName.textContent = e.target.files[0].name;
        selectedFile.classList.add('active');
        disableTextInput();
    } else {
        enableAllInputs();
    }
});

textInput.addEventListener('input', (e) => {
    if (e.target.value.length > 0) {
        disableFileInput();
    } else {
        enableAllInputs();
    }
});

function removeFile() {
    textFile.value = '';
    selectedFile.classList.remove('active');
    fileName.textContent = '';
    enableAllInputs();
}

// Image file event listener
imageFile.addEventListener('change', (e) => {
    updateImageCount(e.target.files);
});

// Drag and drop handling for text files
uploadContainer.addEventListener('dragover', (e) => {
    if (!uploadContainer.classList.contains('disabled')) {
        e.preventDefault();
        uploadContainer.style.borderColor = 'var(--accent-color)';
        uploadContainer.style.backgroundColor = 'rgba(88, 101, 242, 0.1)';
    }
});

uploadContainer.addEventListener('dragleave', (e) => {
    if (!uploadContainer.classList.contains('disabled')) {
        e.preventDefault();
        uploadContainer.style.borderColor = '';
        uploadContainer.style.backgroundColor = '';
    }
});

uploadContainer.addEventListener('drop', (e) => {
    if (!uploadContainer.classList.contains('disabled')) {
        e.preventDefault();
        uploadContainer.style.borderColor = '';
        uploadContainer.style.backgroundColor = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            textFile.files = files;
            fileName.textContent = files[0].name;
            selectedFile.classList.add('active');
            disableTextInput();
        }
    }
});

// Drag and drop handling for images
imageUploadContainer.addEventListener('dragover', (e) => {
    e.preventDefault();
    imageUploadContainer.style.borderColor = 'var(--accent-color)';
    imageUploadContainer.style.backgroundColor = 'rgba(88, 101, 242, 0.1)';
});

imageUploadContainer.addEventListener('dragleave', (e) => {
    e.preventDefault();
    imageUploadContainer.style.borderColor = '';
    imageUploadContainer.style.backgroundColor = '';
});

imageUploadContainer.addEventListener('drop', (e) => {
    e.preventDefault();
    imageUploadContainer.style.borderColor = '';
    imageUploadContainer.style.backgroundColor = '';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        imageFile.files = files;
        updateImageCount(files);
    }
});

// Single click handler for upload containers
uploadContainer.onclick = function(e) {
    if (!uploadContainer.classList.contains('disabled') && !textInput.value) {
        textFile.click();
    }
};

imageUploadContainer.onclick = function() {
    imageFile.click();
};
 document.querySelector('.btn-submit').addEventListener('click', function(event) {
    event.preventDefault();

    const formData = new FormData(document.querySelector('form'));

    fetch('{% url "text_labelling" %}', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob();
    })
    .then(blob => {
        // Create a blob URL and trigger download
        const url = window.URL.createObjectURL(
            new Blob([blob], { type: 'text/csv;charset=utf-8-sig' })
        );
        const a = document.createElement('a');
        a.href = url;
        a.download = 'labeled_data.csv';
        document.body.appendChild(a);
        a.click();

        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while downloading the file.');
    });
});