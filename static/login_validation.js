'use strict';

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('login-form') || document.getElementById('change-password-form');
    if (!form) return;

    const isChangePassword = form.id === 'change-password-form';
    const submitBtn = form.querySelector('button[type="submit"]');

    function showFieldError(field, message) {
        clearFieldError(field);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        field.parentElement.appendChild(errorDiv);
        field.classList.add('error');
    }

    function clearFieldError(field) {
        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        field.classList.remove('error');
    }

    if (isChangePassword) {
        // Change Password Validierung
        const oldPassword = document.getElementById('old_password');
        const newPassword = document.getElementById('new_password');
        const newPassword2 = document.getElementById('new_password2');

        function validatePasswordPolicy(pwd) {
            const errors = [];
            if (pwd.length < 12) errors.push('mindestens 12 Zeichen');
            if (!/[a-z]/.test(pwd)) errors.push('mindestens ein Kleinbuchstabe');
            if (!/[A-Z]/.test(pwd)) errors.push('mindestens ein Großbuchstabe');
            if (!/\d/.test(pwd)) errors.push('mindestens eine Ziffer');
            if (!/[^A-Za-z0-9]/.test(pwd)) errors.push('mindestens ein Sonderzeichen');
            return errors;
        }

        form.addEventListener('submit', function(e) {
            let isValid = true;

            if (!oldPassword.value) {
                showFieldError(oldPassword, 'Aktuelles Passwort ist erforderlich');
                isValid = false;
            } else {
                clearFieldError(oldPassword);
            }

            const policyErrors = validatePasswordPolicy(newPassword.value);
            if (policyErrors.length > 0) {
                showFieldError(newPassword, 'Passwortanforderungen nicht erfüllt: ' + policyErrors.join(', '));
                isValid = false;
            } else {
                clearFieldError(newPassword);
            }

            if (newPassword.value !== newPassword2.value) {
                showFieldError(newPassword2, 'Die neuen Passwörter stimmen nicht überein');
                isValid = false;
            } else {
                clearFieldError(newPassword2);
            }

            if (oldPassword.value && newPassword.value === oldPassword.value) {
                showFieldError(newPassword, 'Das neue Passwort muss sich vom alten unterscheiden');
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
                return false;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird geändert...';
        });

        newPassword.addEventListener('input', function() {
            const errors = validatePasswordPolicy(this.value);
            if (errors.length > 0 && this.value.length > 0) {
                showFieldError(this, 'Noch fehlend: ' + errors.join(', '));
            } else {
                clearFieldError(this);
            }
        });

        newPassword2.addEventListener('input', function() {
            if (newPassword.value && this.value && newPassword.value !== this.value) {
                showFieldError(this, 'Passwörter stimmen nicht überein');
            } else {
                clearFieldError(this);
            }
        });

    } else {
        // Login Validierung
        const usernameInput = document.getElementById('benutzername');
        const passwordInput = document.getElementById('password');

        function validateForm() {
            const username = usernameInput.value.trim();
            const password = passwordInput.value;
            let isValid = true;

            if (!username) {
                showFieldError(usernameInput, 'Benutzername ist erforderlich');
                isValid = false;
            } else if (username.length > 150) {
                showFieldError(usernameInput, 'Benutzername ist zu lang (max. 150 Zeichen)');
                isValid = false;
            } else {
                clearFieldError(usernameInput);
            }

            if (!password) {
                showFieldError(passwordInput, 'Passwort ist erforderlich');
                isValid = false;
            } else {
                clearFieldError(passwordInput);
            }

            return isValid;
        }

        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Anmeldung läuft...';

            setTimeout(function() {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Anmelden';
            }, 10000);
        });

        usernameInput.addEventListener('blur', function() {
            if (this.value.trim()) {
                validateForm();
            }
        });

        passwordInput.addEventListener('blur', function() {
            if (this.value) {
                validateForm();
            }
        });

        if (!usernameInput.value.trim()) {
            usernameInput.focus();
        } else if (!passwordInput.value) {
            passwordInput.focus();
        }
    }
});