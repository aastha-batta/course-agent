// Course form handling
document.addEventListener('DOMContentLoaded', function() {
    const courseForm = document.getElementById('courseForm');
    const submitButton = document.getElementById('submitButton');
    
    if (courseForm) {
        courseForm.addEventListener('submit', function(e) {
            // Validate the form
            if (!courseForm.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            // Change button text and disable it
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generating Course...';
            submitButton.disabled = true;
            
            // Add loading overlay to the form
            const formWrapper = courseForm.closest('.card');
            if (formWrapper) {
                formWrapper.classList.add('position-relative');
                const loadingOverlay = document.createElement('div');
                loadingOverlay.classList.add('position-absolute', 'top-0', 'start-0', 'w-100', 'h-100', 'bg-white', 'bg-opacity-75', 'd-flex', 'align-items-center', 'justify-content-center');
                loadingOverlay.innerHTML = `
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <h5>Submitting your request...</h5>
                        <p class="text-muted">Please wait while we process your course</p>
                    </div>
                `;
                formWrapper.appendChild(loadingOverlay);
            }
            
            // Form will submit normally
        });
    }
});