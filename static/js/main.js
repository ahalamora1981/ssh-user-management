// Form validation and interactions
document.addEventListener('DOMContentLoaded', function() {
    // Password confirmation validation
    const passwordForm = document.querySelector('form[data-validate-passwords]');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');

            if (password.value !== confirmPassword.value) {
                e.preventDefault();
                confirmPassword.classList.add('error');
                showErrorMessage(confirmPassword, 'Passwords do not match');
            }
        });
    }

    // Real-time password match check
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    if (password && confirmPassword) {
        confirmPassword.addEventListener('input', function() {
            if (this.value && this.value !== password.value) {
                this.classList.add('error');
            } else {
                this.classList.remove('error');
                hideErrorMessage(this);
            }
        });
    }

    // Clear error on input
    document.querySelectorAll('input.error').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('error');
            hideErrorMessage(this);
        });
    });
});

function showErrorMessage(element, message) {
    hideErrorMessage(element);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    element.parentNode.appendChild(errorDiv);
}

function hideErrorMessage(element) {
    const existing = element.parentNode.querySelector('.error-message');
    if (existing) {
        existing.remove();
    }
}
