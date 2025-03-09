// Main JavaScript file for Educational Course Generator

// Enable Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alertList = [].slice.call(document.querySelectorAll('.alert:not(.alert-important)'));
    alertList.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Check for course cards that are in processing state
    const processingCards = document.querySelectorAll('[data-status="processing"]');
    processingCards.forEach(function(card) {
        const taskId = card.getAttribute('data-task-id');
        if (taskId) {
            checkCourseStatus(taskId, card);
        }
    });
    
    // Function to check course status via AJAX
    function checkCourseStatus(taskId, cardElement) {
        fetch(`/courses/${taskId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.completed || data.error) {
                    // If course is completed or has error, refresh the card
                    const statusBadge = cardElement.querySelector('.badge');
                    const progressBar = cardElement.querySelector('.progress');
                    
                    if (data.completed) {
                        if (statusBadge) {
                            statusBadge.className = 'badge bg-success';
                            statusBadge.textContent = 'Completed';
                        }
                    } else if (data.error) {
                        if (statusBadge) {
                            statusBadge.className = 'badge bg-danger';
                            statusBadge.textContent = 'Failed';
                        }
                    }
                    
                    // Remove progress bar
                    if (progressBar) {
                        progressBar.remove();
                    }
                    
                    // Update view button to remove spinner
                    const viewButton = cardElement.querySelector('.btn-primary');
                    if (viewButton) {
                        const spinner = viewButton.querySelector('.spinner-border');
                        if (spinner) {
                            spinner.remove();
                        }
                    }
                    
                    // If completed, add download button
                    if (data.completed) {
                        const buttonContainer = cardElement.querySelector('.d-grid');
                        if (buttonContainer && !cardElement.querySelector('.btn-outline-secondary')) {
                            const downloadButton = document.createElement('a');
                            downloadButton.className = 'btn btn-outline-secondary';
                            downloadButton.href = `/courses/${taskId}/download`;
                            downloadButton.textContent = 'Download JSON';
                            buttonContainer.appendChild(downloadButton);
                        }
                    }
                    
                    // Mark card as no longer processing
                    cardElement.setAttribute('data-status', data.completed ? 'completed' : 'error');
                } else {
                    // If still processing, check again in 3 seconds
                    setTimeout(() => checkCourseStatus(taskId, cardElement), 3000);
                }
            })
            .catch(error => {
                console.error('Error checking course status:', error);
                // Try again in 5 seconds
                setTimeout(() => checkCourseStatus(taskId, cardElement), 5000);
            });
    }
});