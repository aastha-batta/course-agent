// Course form handling
document.addEventListener('DOMContentLoaded', function() {
    const courseForm = document.getElementById('courseForm');
    const submitButton = document.getElementById('submitButton');
    
    if (courseForm) {
        courseForm.addEventListener('submit', function(e) {
            // Change button text and disable it
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generating Course...';
            submitButton.disabled = true;
            
            // Form will submit normally
        });
    }
});